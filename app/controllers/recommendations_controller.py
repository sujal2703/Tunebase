from __future__ import annotations

from collections import defaultdict

from flask import Request

from app.controllers.common import current_user_id, get_model, parse_pagination
from app.controllers.songs_controller import _serialize_song
from app.utils.http import api_response
from app.utils.pagination import make_pagination_meta
from app.utils.schema_introspection import find_column, find_foreign_key_columns_referencing, primary_key_column


def list_recommendations(req: Request):
    user_id = current_user_id()
    Songs = get_model("songs")
    UserInterest = get_model("user_interest")
    Recommendations = get_model("recommendations")
    PlaylistSongs = get_model("playlist_songs")
    Playlists = get_model("playlists")
    Likes = get_model("likes")
    PlayHistory = get_model("play_history")
    Follows = get_model("follows")

    page, per_page = parse_pagination(req)

    signal_scores: dict[int, float] = defaultdict(float)
    playlist_song_ids: set[int] = set()
    liked_song_ids: set[int] = set()
    listened_song_ids: set[int] = set()
    followed_artist_ids: set[int] = set()
    excluded_song_ids: set[int] = set()

    playlist_user_fk_cols = find_foreign_key_columns_referencing(Playlists, "users")
    playlist_song_playlist_fk_cols = find_foreign_key_columns_referencing(PlaylistSongs, "playlists")
    playlist_song_song_fk_cols = find_foreign_key_columns_referencing(PlaylistSongs, "songs")
    song_genre_fk_col = find_foreign_key_columns_referencing(Songs, "genres")
    song_artist_fk_col = find_foreign_key_columns_referencing(Songs, "artists")

    if playlist_user_fk_cols and playlist_song_playlist_fk_cols and playlist_song_song_fk_cols and song_genre_fk_col:
        user_playlist_rows = Playlists.query.filter(playlist_user_fk_cols[0] == user_id).all()
        user_playlist_ids = [getattr(row, primary_key_column(Playlists).name) for row in user_playlist_rows]
        if user_playlist_ids:
            playlist_song_rows = PlaylistSongs.query.filter(playlist_song_playlist_fk_cols[0].in_(user_playlist_ids)).all()
            playlist_song_ids = {getattr(row, playlist_song_song_fk_cols[0].name) for row in playlist_song_rows}
            if playlist_song_ids:
                playlist_songs = Songs.query.filter(primary_key_column(Songs).in_(playlist_song_ids)).all()
                for song in playlist_songs:
                    genre_id = getattr(song, song_genre_fk_col[0].name)
                    if genre_id is not None:
                        signal_scores[genre_id] += 4.5

    like_song_fk_cols = find_foreign_key_columns_referencing(Likes, "songs")
    like_user_fk_cols = find_foreign_key_columns_referencing(Likes, "users")
    if like_song_fk_cols and like_user_fk_cols:
        liked_song_ids = {
            getattr(row, like_song_fk_cols[0].name)
            for row in Likes.query.filter(like_user_fk_cols[0] == user_id).all()
        }
        if liked_song_ids and song_genre_fk_col:
            liked_songs = Songs.query.filter(primary_key_column(Songs).in_(liked_song_ids)).all()
            for song in liked_songs:
                genre_id = getattr(song, song_genre_fk_col[0].name)
                if genre_id is not None:
                    signal_scores[genre_id] += 3.25

    history_song_fk_cols = find_foreign_key_columns_referencing(PlayHistory, "songs")
    history_user_fk_cols = find_foreign_key_columns_referencing(PlayHistory, "users")
    if history_song_fk_cols and history_user_fk_cols and song_genre_fk_col:
        history_rows = PlayHistory.query.filter(history_user_fk_cols[0] == user_id).all()
        listened_song_ids = {getattr(row, history_song_fk_cols[0].name) for row in history_rows}
        if listened_song_ids:
            history_songs = Songs.query.filter(primary_key_column(Songs).in_(listened_song_ids)).all()
            for song in history_songs:
                genre_id = getattr(song, song_genre_fk_col[0].name)
                if genre_id is not None:
                    signal_scores[genre_id] += 1.75

    follow_user_fk_cols = find_foreign_key_columns_referencing(Follows, "users")
    follow_artist_fk_cols = find_foreign_key_columns_referencing(Follows, "artists")
    if follow_user_fk_cols and follow_artist_fk_cols:
        followed_artist_ids = {
            getattr(row, follow_artist_fk_cols[0].name)
            for row in Follows.query.filter(follow_user_fk_cols[0] == user_id).all()
        }

    interest_user_fk_cols = find_foreign_key_columns_referencing(UserInterest, "users")
    interest_genre_fk_cols = find_foreign_key_columns_referencing(UserInterest, "genres")
    if interest_user_fk_cols and interest_genre_fk_cols:
        interest_score_col = find_column(UserInterest, ["score", "interest_score"], required=True)
        explicit_interests = UserInterest.query.filter(interest_user_fk_cols[0] == user_id).all()
        for row in explicit_interests:
            genre_id = getattr(row, interest_genre_fk_cols[0].name)
            interest_score = float(getattr(row, interest_score_col.name, 0) or 0)
            if genre_id is not None and interest_score > 0:
                signal_scores[genre_id] += interest_score

    dynamic_genre_ids = [genre_id for genre_id, _score in sorted(signal_scores.items(), key=lambda item: item[1], reverse=True)]
    excluded_song_ids = playlist_song_ids | liked_song_ids

    if dynamic_genre_ids and song_genre_fk_col:
        genre_fk = song_genre_fk_col[0]
        candidate_query = Songs.query.filter(genre_fk.in_(dynamic_genre_ids))
        if excluded_song_ids:
            candidate_query = candidate_query.filter(~primary_key_column(Songs).in_(excluded_song_ids))

        candidates = candidate_query.all()
        if candidates:
            ranked_candidates = []
            for song in candidates:
                song_id = getattr(song, primary_key_column(Songs).name)
                genre_id = getattr(song, genre_fk.name)
                artist_id = getattr(song, song_artist_fk_col[0].name) if song_artist_fk_col else None
                score = float(signal_scores.get(genre_id, 0))
                score += min(float(getattr(song, "total_likes", 0) or 0) / 10000, 3.0)
                score += min(float(getattr(song, "total_plays", 0) or 0) / 50000, 2.0)
                if artist_id in followed_artist_ids:
                    score += 2.75
                if song_id in listened_song_ids:
                    score -= 1.5
                ranked_candidates.append((score, song))

            ranked_candidates.sort(
                key=lambda item: (
                    item[0],
                    getattr(item[1], "total_likes", 0) or 0,
                    getattr(item[1], "total_plays", 0) or 0,
                ),
                reverse=True,
            )
            total = len(ranked_candidates)
            page_start = (page - 1) * per_page
            page_items = [song for _score, song in ranked_candidates[page_start:page_start + per_page]]
            if page_items:
                return api_response(
                    ok=True,
                    data={
                        "items": [_serialize_song(i, user_id=user_id) for i in page_items],
                        "pagination": make_pagination_meta(page, per_page, total),
                        "filters": {
                            "genre_ids": dynamic_genre_ids[:5],
                            "source": "personalized_mix",
                            "followed_artist_ids": sorted(followed_artist_ids),
                        },
                    },
                )

    # Preferred: if you already populate `recommendations`, just return it.
    rec_user_fk_cols = find_foreign_key_columns_referencing(Recommendations, "users")
    rec_song_fk_cols = find_foreign_key_columns_referencing(Recommendations, "songs")
    if rec_user_fk_cols and rec_song_fk_cols:
        rec_user_fk = rec_user_fk_cols[0]
        rec_song_fk = rec_song_fk_cols[0]
        rec_score_col = find_column(Recommendations, ["score"], required=False)
        if rec_score_col is None:
            rec_score_col = find_column(Recommendations, ["rec_score", "recommendation_score"], required=False)
        if rec_score_col is None:
            rec_score_col = primary_key_column(Recommendations)

        base_q = Recommendations.query.filter(rec_user_fk == user_id).order_by(rec_score_col.desc())
        total = base_q.count()
        rec_rows = base_q.offset((page - 1) * per_page).limit(per_page).all()

        if rec_rows:
            song_pk = primary_key_column(Songs)
            song_ids = [getattr(r, rec_song_fk.name) for r in rec_rows if getattr(r, rec_song_fk.name) is not None]
            songs = Songs.query.filter(song_pk.in_(song_ids)).all()
            songs_by_id = {getattr(s, song_pk.name): s for s in songs}

            items = []
            for r in rec_rows:
                sid = getattr(r, rec_song_fk.name)
                song_obj = songs_by_id.get(sid)
                if not song_obj:
                    continue
                item = _serialize_song(song_obj, user_id=user_id)
                item["recommendation_score"] = getattr(r, rec_score_col.name, None)
                item["recommendation_id"] = getattr(r, primary_key_column(Recommendations).name, None)
                items.append(item)

            return api_response(
                ok=True,
                data={"items": items, "pagination": make_pagination_meta(page, per_page, total)},
            )

    # Fallback: compute from `user_interest` (genre_id + score).
    if not interest_user_fk_cols or not interest_genre_fk_cols:
        return api_response(ok=True, data={"items": [], "pagination": make_pagination_meta(page, per_page, 0)})

    interest_user_fk = interest_user_fk_cols[0]
    interest_genre_fk = interest_genre_fk_cols[0]
    interest_score_col = find_column(UserInterest, ["score", "interest_score"], required=True)

    top_interests = (
        UserInterest.query.filter(interest_user_fk == user_id)
        .order_by(interest_score_col.desc())
        .limit(5)
        .all()
    )
    genre_ids = [getattr(r, interest_genre_fk.name) for r in top_interests if getattr(r, interest_genre_fk.name) is not None]
    if not genre_ids:
        return api_response(ok=True, data={"items": [], "pagination": make_pagination_meta(page, per_page, 0)})

    # Filter songs by genre and order by popularity.
    songs_genre_fk = find_foreign_key_columns_referencing(Songs, "genres")[0]
    popularity_col = find_column(Songs, ["total_likes", "total_plays", "duration"], required=False)
    if popularity_col is None:
        popularity_col = primary_key_column(Songs)

    q = Songs.query.filter(songs_genre_fk.in_(genre_ids)).order_by(popularity_col.desc())
    total = q.count()
    items = q.offset((page - 1) * per_page).limit(per_page).all()

    return api_response(
        ok=True,
        data={
            "items": [_serialize_song(i, user_id=user_id) for i in items],
            "pagination": make_pagination_meta(page, per_page, total),
            "filters": {"genre_ids": genre_ids},
        },
    )

