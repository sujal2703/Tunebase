from __future__ import annotations

from datetime import date, datetime, timedelta

from flask_bcrypt import generate_password_hash
from sqlalchemy import create_engine, inspect, text

from config import Config


DEFAULT_PASSWORD = "TuneBase@123"


USERS = [
    {"user_id": 1, "name": "Aarav Mehta", "email": "aarav.mehta@tunebase.app", "date_of_birth": date(2000, 5, 12)},
    {"user_id": 2, "name": "Riya Sharma", "email": "riya.sharma@tunebase.app", "date_of_birth": date(1999, 8, 22)},
    {"user_id": 3, "name": "Karan Patel", "email": "karan.patel@tunebase.app", "date_of_birth": date(2001, 2, 15)},
    {"user_id": 4, "name": "Sneha Iyer", "email": "sneha.iyer@tunebase.app", "date_of_birth": date(2002, 7, 18)},
    {"user_id": 5, "name": "Aditya Singh", "email": "aditya.singh@tunebase.app", "date_of_birth": date(1998, 11, 30)},
    {"user_id": 6, "name": "Neha Verma", "email": "neha.verma@tunebase.app", "date_of_birth": date(1997, 3, 8)},
    {"user_id": 7, "name": "Kabir Khan", "email": "kabir.khan@tunebase.app", "date_of_birth": date(2001, 12, 3)},
    {"user_id": 8, "name": "Isha Nair", "email": "isha.nair@tunebase.app", "date_of_birth": date(2000, 9, 27)},
]

ROLES = [
    {"role_id": 1, "role_name": "admin"},
    {"role_id": 2, "role_name": "listener"},
    {"role_id": 3, "role_name": "premium_listener"},
]

USER_ROLES = [
    {"user_id": 1, "role_id": 1},
    {"user_id": 1, "role_id": 3},
    {"user_id": 2, "role_id": 3},
    {"user_id": 3, "role_id": 2},
    {"user_id": 4, "role_id": 3},
    {"user_id": 5, "role_id": 2},
    {"user_id": 6, "role_id": 3},
    {"user_id": 7, "role_id": 2},
    {"user_id": 8, "role_id": 2},
]

GENRES = [
    {"genre_id": 1, "genre_name": "Pop"},
    {"genre_id": 2, "genre_name": "R&B"},
    {"genre_id": 3, "genre_name": "Bollywood"},
    {"genre_id": 4, "genre_name": "Hip-Hop"},
    {"genre_id": 5, "genre_name": "Alternative"},
    {"genre_id": 6, "genre_name": "Electronic"},
    {"genre_id": 7, "genre_name": "Soul"},
]

ARTISTS = [
    {"artist_id": 1, "artist_name": "Taylor Swift", "bio": "American singer-songwriter known for pop and narrative songwriting."},
    {"artist_id": 2, "artist_name": "The Weeknd", "bio": "Canadian artist blending R&B, synth-pop, and dark cinematic production."},
    {"artist_id": 3, "artist_name": "Arijit Singh", "bio": "Indian playback singer with a major footprint across Bollywood soundtracks."},
    {"artist_id": 4, "artist_name": "Dua Lipa", "bio": "British-Albanian pop artist known for dance-pop hits."},
    {"artist_id": 5, "artist_name": "Coldplay", "bio": "British band combining alternative rock with stadium-sized pop melodies."},
    {"artist_id": 6, "artist_name": "A. R. Rahman", "bio": "Oscar-winning Indian composer and producer."},
    {"artist_id": 7, "artist_name": "Drake", "bio": "Canadian rapper and singer with mainstream hip-hop chart success."},
    {"artist_id": 8, "artist_name": "Adele", "bio": "English singer-songwriter recognized for soul-pop ballads."},
    {"artist_id": 9, "artist_name": "Ed Sheeran", "bio": "English pop singer-songwriter with acoustic and crossover chart hits."},
    {"artist_id": 10, "artist_name": "Olivia Rodrigo", "bio": "American singer-songwriter known for pop-rock confessionals."},
    {"artist_id": 11, "artist_name": "Billie Eilish", "bio": "American artist known for minimal, atmospheric pop production."},
    {"artist_id": 12, "artist_name": "Imagine Dragons", "bio": "American pop-rock band with arena-ready hooks."},
    {"artist_id": 13, "artist_name": "Shreya Ghoshal", "bio": "Indian playback singer with a wide-ranging Bollywood catalog."},
    {"artist_id": 14, "artist_name": "Kendrick Lamar", "bio": "American rapper acclaimed for layered lyricism and conceptual albums."},
    {"artist_id": 15, "artist_name": "SZA", "bio": "American singer-songwriter blending R&B, soul, and alternative pop."},
    {"artist_id": 16, "artist_name": "Post Malone", "bio": "American artist known for melodic hip-hop and pop crossover hits."},
    {"artist_id": 17, "artist_name": "BTS", "bio": "South Korean group with global pop and performance-driven releases."},
    {"artist_id": 18, "artist_name": "Lana Del Rey", "bio": "American singer-songwriter known for cinematic alternative pop."},
]

ALBUMS = [
    {"album_id": 1, "album_name": "Midnights", "artist_id": 1, "release_date": date(2022, 10, 21)},
    {"album_id": 2, "album_name": "After Hours", "artist_id": 2, "release_date": date(2020, 3, 20)},
    {"album_id": 3, "album_name": "Brahmastra (Original Motion Picture Soundtrack)", "artist_id": 3, "release_date": date(2022, 9, 8)},
    {"album_id": 4, "album_name": "Future Nostalgia", "artist_id": 4, "release_date": date(2020, 3, 27)},
    {"album_id": 5, "album_name": "Music of the Spheres", "artist_id": 5, "release_date": date(2021, 10, 15)},
    {"album_id": 6, "album_name": "Vande Mataram", "artist_id": 6, "release_date": date(1997, 8, 12)},
    {"album_id": 7, "album_name": "Scorpion", "artist_id": 7, "release_date": date(2018, 6, 29)},
    {"album_id": 8, "album_name": "30", "artist_id": 8, "release_date": date(2021, 11, 19)},
    {"album_id": 9, "album_name": "Divide", "artist_id": 9, "release_date": date(2017, 3, 3)},
    {"album_id": 10, "album_name": "GUTS", "artist_id": 10, "release_date": date(2023, 9, 8)},
    {"album_id": 11, "album_name": "SOUR", "artist_id": 10, "release_date": date(2021, 5, 21)},
    {"album_id": 12, "album_name": "Happier Than Ever", "artist_id": 11, "release_date": date(2021, 7, 30)},
    {"album_id": 13, "album_name": "Evolve", "artist_id": 12, "release_date": date(2017, 6, 23)},
    {"album_id": 14, "album_name": "Mercury - Act 1", "artist_id": 12, "release_date": date(2021, 9, 3)},
    {"album_id": 15, "album_name": "Aashiqui 2", "artist_id": 13, "release_date": date(2013, 4, 6)},
    {"album_id": 16, "album_name": "Animal (Original Motion Picture Soundtrack)", "artist_id": 13, "release_date": date(2023, 11, 24)},
    {"album_id": 17, "album_name": "DAMN.", "artist_id": 14, "release_date": date(2017, 4, 14)},
    {"album_id": 18, "album_name": "Mr. Morale & the Big Steppers", "artist_id": 14, "release_date": date(2022, 5, 13)},
    {"album_id": 19, "album_name": "SOS", "artist_id": 15, "release_date": date(2022, 12, 9)},
    {"album_id": 20, "album_name": "Ctrl", "artist_id": 15, "release_date": date(2017, 6, 9)},
    {"album_id": 21, "album_name": "Hollywood's Bleeding", "artist_id": 16, "release_date": date(2019, 9, 6)},
    {"album_id": 22, "album_name": "BE", "artist_id": 17, "release_date": date(2020, 11, 20)},
    {"album_id": 23, "album_name": "Born to Die", "artist_id": 18, "release_date": date(2012, 1, 27)},
    {"album_id": 24, "album_name": "Did You Know That There's a Tunnel Under Ocean Blvd", "artist_id": 18, "release_date": date(2023, 3, 24)},
]

SONGS = [
    {"song_id": 1, "title": "Anti-Hero", "duration": 200, "artist_id": 1, "album_id": 1, "genre_id": 1, "total_plays": 98234, "total_likes": 18221},
    {"song_id": 2, "title": "Lavender Haze", "duration": 202, "artist_id": 1, "album_id": 1, "genre_id": 1, "total_plays": 74551, "total_likes": 14114},
    {"song_id": 3, "title": "Blinding Lights", "duration": 200, "artist_id": 2, "album_id": 2, "genre_id": 2, "total_plays": 150320, "total_likes": 28400},
    {"song_id": 4, "title": "Save Your Tears", "duration": 215, "artist_id": 2, "album_id": 2, "genre_id": 2, "total_plays": 131450, "total_likes": 25910},
    {"song_id": 5, "title": "Kesariya", "duration": 268, "artist_id": 3, "album_id": 3, "genre_id": 3, "total_plays": 120442, "total_likes": 24030},
    {"song_id": 6, "title": "Deva Deva", "duration": 250, "artist_id": 3, "album_id": 3, "genre_id": 3, "total_plays": 87450, "total_likes": 16880},
    {"song_id": 7, "title": "Levitating", "duration": 203, "artist_id": 4, "album_id": 4, "genre_id": 6, "total_plays": 140230, "total_likes": 27655},
    {"song_id": 8, "title": "Don't Start Now", "duration": 183, "artist_id": 4, "album_id": 4, "genre_id": 1, "total_plays": 119800, "total_likes": 23111},
    {"song_id": 9, "title": "My Universe", "duration": 226, "artist_id": 5, "album_id": 5, "genre_id": 5, "total_plays": 84560, "total_likes": 15220},
    {"song_id": 10, "title": "Higher Power", "duration": 211, "artist_id": 5, "album_id": 5, "genre_id": 5, "total_plays": 76440, "total_likes": 13840},
    {"song_id": 11, "title": "Maa Tujhe Salaam", "duration": 368, "artist_id": 6, "album_id": 6, "genre_id": 3, "total_plays": 65420, "total_likes": 12980},
    {"song_id": 12, "title": "Gurus of Peace", "duration": 336, "artist_id": 6, "album_id": 6, "genre_id": 3, "total_plays": 40210, "total_likes": 8844},
    {"song_id": 13, "title": "God's Plan", "duration": 198, "artist_id": 7, "album_id": 7, "genre_id": 4, "total_plays": 112330, "total_likes": 21400},
    {"song_id": 14, "title": "In My Feelings", "duration": 217, "artist_id": 7, "album_id": 7, "genre_id": 4, "total_plays": 109540, "total_likes": 19850},
    {"song_id": 15, "title": "Easy On Me", "duration": 224, "artist_id": 8, "album_id": 8, "genre_id": 7, "total_plays": 100240, "total_likes": 19330},
    {"song_id": 16, "title": "Oh My God", "duration": 225, "artist_id": 8, "album_id": 8, "genre_id": 7, "total_plays": 72220, "total_likes": 14080},
    {"song_id": 17, "title": "Shape of You", "duration": 234, "artist_id": 9, "album_id": 9, "genre_id": 1, "total_plays": 161200, "total_likes": 30245},
    {"song_id": 18, "title": "Perfect", "duration": 263, "artist_id": 9, "album_id": 9, "genre_id": 1, "total_plays": 118950, "total_likes": 22140},
    {"song_id": 19, "title": "vampire", "duration": 220, "artist_id": 10, "album_id": 10, "genre_id": 1, "total_plays": 105430, "total_likes": 19950},
    {"song_id": 20, "title": "bad idea right?", "duration": 185, "artist_id": 10, "album_id": 10, "genre_id": 1, "total_plays": 84220, "total_likes": 15570},
    {"song_id": 21, "title": "good 4 u", "duration": 178, "artist_id": 10, "album_id": 11, "genre_id": 5, "total_plays": 132880, "total_likes": 24910},
    {"song_id": 22, "title": "drivers license", "duration": 242, "artist_id": 10, "album_id": 11, "genre_id": 1, "total_plays": 140430, "total_likes": 27005},
    {"song_id": 23, "title": "Happier Than Ever", "duration": 298, "artist_id": 11, "album_id": 12, "genre_id": 5, "total_plays": 98410, "total_likes": 18310},
    {"song_id": 24, "title": "Therefore I Am", "duration": 174, "artist_id": 11, "album_id": 12, "genre_id": 1, "total_plays": 90440, "total_likes": 16870},
    {"song_id": 25, "title": "Believer", "duration": 204, "artist_id": 12, "album_id": 13, "genre_id": 5, "total_plays": 171550, "total_likes": 31550},
    {"song_id": 26, "title": "Thunder", "duration": 187, "artist_id": 12, "album_id": 13, "genre_id": 5, "total_plays": 149880, "total_likes": 27920},
    {"song_id": 27, "title": "Wrecked", "duration": 244, "artist_id": 12, "album_id": 14, "genre_id": 5, "total_plays": 72210, "total_likes": 13110},
    {"song_id": 28, "title": "Follow You", "duration": 176, "artist_id": 12, "album_id": 14, "genre_id": 5, "total_plays": 70340, "total_likes": 12890},
    {"song_id": 29, "title": "Sun Raha Hai Na Tu", "duration": 379, "artist_id": 13, "album_id": 15, "genre_id": 3, "total_plays": 96220, "total_likes": 18550},
    {"song_id": 30, "title": "Tum Hi Ho", "duration": 262, "artist_id": 13, "album_id": 15, "genre_id": 3, "total_plays": 188430, "total_likes": 36220},
    {"song_id": 31, "title": "Satranga", "duration": 271, "artist_id": 13, "album_id": 16, "genre_id": 3, "total_plays": 68440, "total_likes": 12750},
    {"song_id": 32, "title": "Hua Main", "duration": 262, "artist_id": 13, "album_id": 16, "genre_id": 3, "total_plays": 63550, "total_likes": 11840},
    {"song_id": 33, "title": "HUMBLE.", "duration": 177, "artist_id": 14, "album_id": 17, "genre_id": 4, "total_plays": 126210, "total_likes": 24010},
    {"song_id": 34, "title": "DNA.", "duration": 186, "artist_id": 14, "album_id": 17, "genre_id": 4, "total_plays": 110330, "total_likes": 20940},
    {"song_id": 35, "title": "N95", "duration": 195, "artist_id": 14, "album_id": 18, "genre_id": 4, "total_plays": 91330, "total_likes": 17670},
    {"song_id": 36, "title": "Count Me Out", "duration": 284, "artist_id": 14, "album_id": 18, "genre_id": 4, "total_plays": 74220, "total_likes": 14220},
    {"song_id": 37, "title": "Kill Bill", "duration": 153, "artist_id": 15, "album_id": 19, "genre_id": 2, "total_plays": 132450, "total_likes": 25140},
    {"song_id": 38, "title": "Snooze", "duration": 201, "artist_id": 15, "album_id": 19, "genre_id": 2, "total_plays": 108220, "total_likes": 20510},
    {"song_id": 39, "title": "Love Galore", "duration": 275, "artist_id": 15, "album_id": 20, "genre_id": 2, "total_plays": 87420, "total_likes": 16720},
    {"song_id": 40, "title": "The Weekend", "duration": 272, "artist_id": 15, "album_id": 20, "genre_id": 2, "total_plays": 79110, "total_likes": 14980},
    {"song_id": 41, "title": "Circles", "duration": 215, "artist_id": 16, "album_id": 21, "genre_id": 1, "total_plays": 144330, "total_likes": 27660},
    {"song_id": 42, "title": "Sunflower", "duration": 158, "artist_id": 16, "album_id": 21, "genre_id": 1, "total_plays": 168450, "total_likes": 32540},
    {"song_id": 43, "title": "Dynamite", "duration": 199, "artist_id": 17, "album_id": 22, "genre_id": 1, "total_plays": 170120, "total_likes": 33300},
    {"song_id": 44, "title": "Life Goes On", "duration": 207, "artist_id": 17, "album_id": 22, "genre_id": 1, "total_plays": 89210, "total_likes": 17120},
    {"song_id": 45, "title": "Video Games", "duration": 281, "artist_id": 18, "album_id": 23, "genre_id": 5, "total_plays": 78550, "total_likes": 15010},
    {"song_id": 46, "title": "Born to Die", "duration": 286, "artist_id": 18, "album_id": 23, "genre_id": 5, "total_plays": 80840, "total_likes": 15450},
    {"song_id": 47, "title": "A&W", "duration": 436, "artist_id": 18, "album_id": 24, "genre_id": 5, "total_plays": 62110, "total_likes": 12030},
    {"song_id": 48, "title": "Say Yes to Heaven", "duration": 210, "artist_id": 18, "album_id": 24, "genre_id": 5, "total_plays": 67660, "total_likes": 13140},
]

PLAYLISTS = [
    {"playlist_id": 1, "playlist_name": "Morning Momentum", "description": "Uplifting songs for a strong start to the day.", "user_id": 1},
    {"playlist_id": 2, "playlist_name": "Midnight Drive", "description": "Neon-lit synths and late-night pop.", "user_id": 2},
    {"playlist_id": 3, "playlist_name": "Bollywood Favorites", "description": "Big soundtrack moments and heartfelt vocals.", "user_id": 3},
    {"playlist_id": 4, "playlist_name": "Focus Flow", "description": "Steady songs for deep work sessions.", "user_id": 4},
    {"playlist_id": 5, "playlist_name": "Gym Heat", "description": "High-energy tracks for workouts and runs.", "user_id": 5},
    {"playlist_id": 6, "playlist_name": "Soul Sundays", "description": "Warm vocals and slow-burn evening listens.", "user_id": 6},
    {"playlist_id": 7, "playlist_name": "Campus Repeats", "description": "Catchy pop for study breaks and late nights.", "user_id": 7},
    {"playlist_id": 8, "playlist_name": "Coastal Calm", "description": "Dreamy alt-pop for slow afternoons.", "user_id": 8},
]

PLAYLIST_SONGS = [
    {"playlist_id": 1, "song_id": 1}, {"playlist_id": 1, "song_id": 8}, {"playlist_id": 1, "song_id": 17},
    {"playlist_id": 2, "song_id": 3}, {"playlist_id": 2, "song_id": 7}, {"playlist_id": 2, "song_id": 9},
    {"playlist_id": 3, "song_id": 5}, {"playlist_id": 3, "song_id": 6}, {"playlist_id": 3, "song_id": 11},
    {"playlist_id": 4, "song_id": 2}, {"playlist_id": 4, "song_id": 10}, {"playlist_id": 4, "song_id": 18},
    {"playlist_id": 5, "song_id": 13}, {"playlist_id": 5, "song_id": 25}, {"playlist_id": 5, "song_id": 33},
    {"playlist_id": 6, "song_id": 15}, {"playlist_id": 6, "song_id": 37}, {"playlist_id": 6, "song_id": 38},
    {"playlist_id": 7, "song_id": 19}, {"playlist_id": 7, "song_id": 22}, {"playlist_id": 7, "song_id": 43},
    {"playlist_id": 8, "song_id": 23}, {"playlist_id": 8, "song_id": 45}, {"playlist_id": 8, "song_id": 48},
]

FOLLOWS = [
    {"user_id": 1, "artist_id": 1}, {"user_id": 1, "artist_id": 5}, {"user_id": 2, "artist_id": 2},
    {"user_id": 3, "artist_id": 3}, {"user_id": 3, "artist_id": 13}, {"user_id": 4, "artist_id": 4},
    {"user_id": 4, "artist_id": 12}, {"user_id": 5, "artist_id": 14}, {"user_id": 5, "artist_id": 7},
    {"user_id": 6, "artist_id": 8}, {"user_id": 6, "artist_id": 15}, {"user_id": 7, "artist_id": 10},
    {"user_id": 7, "artist_id": 17}, {"user_id": 8, "artist_id": 18}, {"user_id": 8, "artist_id": 11},
]

USER_INTEREST = [
    {"user_id": 1, "genre_id": 1, "interest_score": 9.4},
    {"user_id": 1, "genre_id": 5, "interest_score": 8.3},
    {"user_id": 2, "genre_id": 2, "interest_score": 9.1},
    {"user_id": 2, "genre_id": 6, "interest_score": 8.4},
    {"user_id": 3, "genre_id": 3, "interest_score": 9.8},
    {"user_id": 3, "genre_id": 7, "interest_score": 7.2},
    {"user_id": 4, "genre_id": 6, "interest_score": 8.7},
    {"user_id": 4, "genre_id": 5, "interest_score": 8.1},
    {"user_id": 5, "genre_id": 4, "interest_score": 8.9},
    {"user_id": 5, "genre_id": 5, "interest_score": 7.4},
    {"user_id": 6, "genre_id": 7, "interest_score": 9.0},
    {"user_id": 6, "genre_id": 2, "interest_score": 8.8},
    {"user_id": 7, "genre_id": 1, "interest_score": 8.1},
    {"user_id": 7, "genre_id": 6, "interest_score": 7.9},
    {"user_id": 8, "genre_id": 5, "interest_score": 9.2},
    {"user_id": 8, "genre_id": 7, "interest_score": 8.0},
]

RECOMMENDATIONS = [
    {"recommendation_id": 1, "user_id": 1, "song_id": 41, "score": 9.7},
    {"recommendation_id": 2, "user_id": 1, "song_id": 43, "score": 9.4},
    {"recommendation_id": 3, "user_id": 2, "song_id": 37, "score": 9.6},
    {"recommendation_id": 4, "user_id": 2, "song_id": 38, "score": 9.2},
    {"recommendation_id": 5, "user_id": 3, "song_id": 29, "score": 9.8},
    {"recommendation_id": 6, "user_id": 3, "song_id": 30, "score": 9.3},
    {"recommendation_id": 7, "user_id": 4, "song_id": 26, "score": 8.9},
    {"recommendation_id": 8, "user_id": 4, "song_id": 27, "score": 8.5},
    {"recommendation_id": 9, "user_id": 5, "song_id": 35, "score": 9.1},
    {"recommendation_id": 10, "user_id": 5, "song_id": 36, "score": 8.8},
    {"recommendation_id": 11, "user_id": 6, "song_id": 16, "score": 9.3},
    {"recommendation_id": 12, "user_id": 6, "song_id": 40, "score": 9.0},
    {"recommendation_id": 13, "user_id": 7, "song_id": 20, "score": 8.9},
    {"recommendation_id": 14, "user_id": 7, "song_id": 24, "score": 8.6},
    {"recommendation_id": 15, "user_id": 8, "song_id": 46, "score": 9.4},
    {"recommendation_id": 16, "user_id": 8, "song_id": 47, "score": 9.1},
]

SUBSCRIPTION_PLANS = [
    {"plan_id": 1, "plan_name": "Free", "description": "Ad-supported streaming on one device.", "price": 0.00, "duration_days": 30},
    {"plan_id": 2, "plan_name": "Mini", "description": "Mobile-first listening with offline downloads.", "price": 79.00, "duration_days": 30},
    {"plan_id": 3, "plan_name": "Premium", "description": "Unlimited ad-free streaming and downloads.", "price": 199.00, "duration_days": 30},
    {"plan_id": 4, "plan_name": "Family", "description": "Six accounts with shared billing for households.", "price": 299.00, "duration_days": 30},
    {"plan_id": 5, "plan_name": "Annual Premium", "description": "Twelve months of premium access at a discount.", "price": 1999.00, "duration_days": 365},
]

USER_SUBSCRIPTIONS = [
    {"subscription_id": 1, "user_id": 1, "plan_id": 5, "start_date": date(2026, 1, 1), "end_date": date(2026, 12, 31), "status": "active"},
    {"subscription_id": 2, "user_id": 2, "plan_id": 3, "start_date": date(2026, 3, 1), "end_date": date(2026, 3, 31), "status": "active"},
    {"subscription_id": 3, "user_id": 3, "plan_id": 2, "start_date": date(2026, 3, 20), "end_date": date(2026, 4, 18), "status": "active"},
    {"subscription_id": 4, "user_id": 4, "plan_id": 4, "start_date": date(2026, 3, 15), "end_date": date(2026, 4, 14), "status": "active"},
    {"subscription_id": 5, "user_id": 6, "plan_id": 3, "start_date": date(2026, 2, 10), "end_date": date(2026, 3, 11), "status": "expired"},
    {"subscription_id": 6, "user_id": 7, "plan_id": 4, "start_date": date(2026, 3, 5), "end_date": date(2026, 4, 4), "status": "active"},
    {"subscription_id": 7, "user_id": 8, "plan_id": 2, "start_date": date(2026, 3, 25), "end_date": date(2026, 4, 23), "status": "active"},
]

TRANSACTIONS = [
    {"transaction_id": 1, "user_id": 1, "subscription_id": 1, "amount": 1999.00, "payment_method": "card", "status": "completed"},
    {"transaction_id": 2, "user_id": 2, "subscription_id": 2, "amount": 199.00, "payment_method": "upi", "status": "completed"},
    {"transaction_id": 3, "user_id": 3, "subscription_id": 3, "amount": 79.00, "payment_method": "upi", "status": "completed"},
    {"transaction_id": 4, "user_id": 4, "subscription_id": 4, "amount": 299.00, "payment_method": "card", "status": "completed"},
    {"transaction_id": 5, "user_id": 6, "subscription_id": 5, "amount": 199.00, "payment_method": "netbanking", "status": "completed"},
    {"transaction_id": 6, "user_id": 7, "subscription_id": 6, "amount": 299.00, "payment_method": "card", "status": "completed"},
    {"transaction_id": 7, "user_id": 8, "subscription_id": 7, "amount": 79.00, "payment_method": "upi", "status": "completed"},
]

DEVICES = [
    {"device_id": 1, "user_id": 1, "device_name": "Aarav MacBook", "device_type": "Laptop"},
    {"device_id": 2, "user_id": 2, "device_name": "Riya iPhone", "device_type": "Phone"},
    {"device_id": 3, "user_id": 3, "device_name": "Karan Windows PC", "device_type": "Desktop"},
    {"device_id": 4, "user_id": 4, "device_name": "Sneha Android", "device_type": "Phone"},
    {"device_id": 5, "user_id": 5, "device_name": "Aditya iPad", "device_type": "Tablet"},
    {"device_id": 6, "user_id": 6, "device_name": "Neha Work Laptop", "device_type": "Laptop"},
    {"device_id": 7, "user_id": 7, "device_name": "Kabir Phone", "device_type": "Phone"},
    {"device_id": 8, "user_id": 8, "device_name": "Isha Surface", "device_type": "Laptop"},
]

SESSIONS = [
    {"session_id": 1, "user_id": 1, "device_id": 1, "status": "active"},
    {"session_id": 2, "user_id": 2, "device_id": 2, "status": "active"},
    {"session_id": 3, "user_id": 3, "device_id": 3, "status": "active"},
    {"session_id": 4, "user_id": 4, "device_id": 4, "status": "active"},
    {"session_id": 5, "user_id": 5, "device_id": 5, "status": "inactive"},
    {"session_id": 6, "user_id": 6, "device_id": 6, "status": "inactive"},
]

PLAY_HISTORY = [
    {"play_id": 1, "user_id": 1, "song_id": 1}, {"play_id": 2, "user_id": 1, "song_id": 17},
    {"play_id": 3, "user_id": 1, "song_id": 9}, {"play_id": 4, "user_id": 2, "song_id": 3},
    {"play_id": 5, "user_id": 2, "song_id": 4}, {"play_id": 6, "user_id": 3, "song_id": 5},
    {"play_id": 7, "user_id": 3, "song_id": 11}, {"play_id": 8, "user_id": 4, "song_id": 7},
    {"play_id": 9, "user_id": 4, "song_id": 8}, {"play_id": 10, "user_id": 5, "song_id": 13},
    {"play_id": 11, "user_id": 5, "song_id": 14}, {"play_id": 12, "user_id": 6, "song_id": 15},
    {"play_id": 13, "user_id": 6, "song_id": 37}, {"play_id": 14, "user_id": 7, "song_id": 19},
    {"play_id": 15, "user_id": 7, "song_id": 43}, {"play_id": 16, "user_id": 8, "song_id": 45},
    {"play_id": 17, "user_id": 8, "song_id": 48},
]

LIKES = [
    {"user_id": 1, "song_id": 1}, {"user_id": 1, "song_id": 17}, {"user_id": 2, "song_id": 3},
    {"user_id": 2, "song_id": 4}, {"user_id": 3, "song_id": 5}, {"user_id": 4, "song_id": 7},
    {"user_id": 5, "song_id": 13}, {"user_id": 5, "song_id": 33}, {"user_id": 6, "song_id": 15},
    {"user_id": 6, "song_id": 38}, {"user_id": 7, "song_id": 18}, {"user_id": 7, "song_id": 43},
    {"user_id": 8, "song_id": 45}, {"user_id": 8, "song_id": 48},
]

DOWNLOADS = [
    {"download_id": 1, "user_id": 1, "song_id": 1},
    {"download_id": 2, "user_id": 2, "song_id": 3},
    {"download_id": 3, "user_id": 3, "song_id": 5},
    {"download_id": 4, "user_id": 4, "song_id": 7},
]

SEARCH_HISTORY = [
    {"search_id": 1, "user_id": 1, "search_query": "Taylor Swift"},
    {"search_id": 2, "user_id": 1, "search_query": "Morning playlist"},
    {"search_id": 3, "user_id": 2, "search_query": "The Weeknd"},
    {"search_id": 4, "user_id": 3, "search_query": "Bollywood hits"},
    {"search_id": 5, "user_id": 4, "search_query": "focus music"},
    {"search_id": 6, "user_id": 5, "search_query": "workout rap"},
    {"search_id": 7, "user_id": 6, "search_query": "soul chill"},
    {"search_id": 8, "user_id": 7, "search_query": "campus pop"},
    {"search_id": 9, "user_id": 8, "search_query": "dreamy alternative"},
]

NOTIFICATIONS = [
    {"notification_id": 1, "user_id": 1, "message": "Your Annual Premium plan renews in 30 days.", "is_read": 0},
    {"notification_id": 2, "user_id": 2, "message": "New personalized recommendations are ready for you.", "is_read": 0},
    {"notification_id": 3, "user_id": 3, "message": "Bollywood Favorites has new tracks you might like.", "is_read": 1},
    {"notification_id": 4, "user_id": 4, "message": "Family plan members can now download playlists offline.", "is_read": 0},
    {"notification_id": 5, "user_id": 5, "message": "Gym Heat picked up fresh hip-hop recommendations today.", "is_read": 0},
    {"notification_id": 6, "user_id": 6, "message": "Your Free plan is active and Soul Sundays is ready to stream.", "is_read": 1},
    {"notification_id": 7, "user_id": 7, "message": "Campus Repeats has new pop picks based on your recent likes.", "is_read": 0},
    {"notification_id": 8, "user_id": 8, "message": "Coastal Calm inspired a new alternative mix for tonight.", "is_read": 0},
]

AUDIT_LOGS = [
    {"log_id": 1, "user_id": 1, "action": "seed_admin_login", "ip_address": "127.0.0.1"},
    {"log_id": 2, "user_id": 2, "action": "playlist_created", "ip_address": "127.0.0.1"},
    {"log_id": 3, "user_id": 3, "action": "song_liked", "ip_address": "127.0.0.1"},
]

OTP_ROWS = [
    {"otp_id": 1, "user_id": 2, "otp_code": "483920", "is_used": 1},
    {"otp_id": 2, "user_id": 4, "otp_code": "901114", "is_used": 0},
]


def ensure_columns(engine) -> None:
    inspector = inspect(engine)
    column_names = {table: {column["name"] for column in inspector.get_columns(table)} for table in inspector.get_table_names()}

    with engine.begin() as conn:
        if "password" not in column_names.get("users", set()):
            conn.execute(text("ALTER TABLE users ADD COLUMN password VARCHAR(255) NULL AFTER email"))
        if "description" not in column_names.get("playlists", set()):
            conn.execute(text("ALTER TABLE playlists ADD COLUMN description TEXT NULL AFTER playlist_name"))
        if "description" not in column_names.get("subscription_plans", set()):
            conn.execute(text("ALTER TABLE subscription_plans ADD COLUMN description TEXT NULL AFTER plan_name"))


def truncate_tables(engine) -> None:
    table_order = [
        "audit_logs",
        "otp",
        "transactions",
        "user_subscriptions",
        "recommendations",
        "user_interest",
        "search_history",
        "downloads",
        "likes",
        "play_history",
        "playlist_songs",
        "playlists",
        "sessions",
        "devices",
        "follows",
        "authentication",
        "user_roles",
        "roles",
        "songs",
        "albums",
        "artists",
        "genres",
        "notifications",
        "users",
        "subscription_plans",
    ]

    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in table_order:
            conn.execute(text(f"TRUNCATE TABLE `{table}`"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))


def insert_many(conn, table: str, rows: list[dict], sql: str) -> None:
    if rows:
        conn.execute(text(sql), rows)


def seed_database(engine) -> None:
    password_hash = generate_password_hash(DEFAULT_PASSWORD).decode("utf-8")
    now = datetime(2026, 4, 1, 9, 0, 0)

    users_rows = [
        {
            **row,
            "password": password_hash,
            "is_deleted": 0,
            "created_at": now,
            "updated_at": now,
        }
        for row in USERS
    ]
    auth_rows = [
        {
            "auth_id": row["user_id"],
            "user_id": row["user_id"],
            "password_hash": password_hash,
            "failed_attempts": 0,
            "account_status": "active",
            "last_login": now,
        }
        for row in USERS
    ]
    artist_rows = [{**row, "is_deleted": 0, "created_at": now} for row in ARTISTS]
    album_rows = [{**row, "is_deleted": 0} for row in ALBUMS]
    song_rows = [{**row, "is_deleted": 0} for row in SONGS]
    playlist_rows = [{**row, "is_deleted": 0, "created_at": now} for row in PLAYLISTS]
    playlist_song_rows = [
        {**row, "added_at": now + timedelta(minutes=index)}
        for index, row in enumerate(PLAYLIST_SONGS, start=1)
    ]
    device_rows = [{**row, "last_active": now - timedelta(hours=row["device_id"])} for row in DEVICES]
    session_rows = [
        {
            **row,
            "login_time": now - timedelta(days=row["session_id"]),
            "logout_time": None if row["status"] == "active" else now - timedelta(days=row["session_id"] - 1, hours=20),
        }
        for row in SESSIONS
    ]
    play_history_rows = [
        {**row, "played_at": now - timedelta(hours=index * 3)}
        for index, row in enumerate(PLAY_HISTORY, start=1)
    ]
    like_rows = [
        {**row, "liked_at": now - timedelta(days=index)}
        for index, row in enumerate(LIKES, start=1)
    ]
    download_rows = [
        {**row, "downloaded_at": now - timedelta(days=index * 2)}
        for index, row in enumerate(DOWNLOADS, start=1)
    ]
    search_rows = [
        {**row, "searched_at": now - timedelta(hours=index * 5)}
        for index, row in enumerate(SEARCH_HISTORY, start=1)
    ]
    recommendation_rows = [
        {**row, "generated_at": now - timedelta(days=index)}
        for index, row in enumerate(RECOMMENDATIONS, start=1)
    ]
    notification_rows = [
        {**row, "created_at": now - timedelta(days=index)}
        for index, row in enumerate(NOTIFICATIONS, start=1)
    ]
    transaction_rows = [
        {**row, "transaction_date": now - timedelta(days=index * 7)}
        for index, row in enumerate(TRANSACTIONS, start=1)
    ]
    audit_rows = [
        {**row, "created_at": now - timedelta(minutes=index * 12)}
        for index, row in enumerate(AUDIT_LOGS, start=1)
    ]
    otp_rows = [
        {**row, "expiry_time": now + timedelta(minutes=10 if row["is_used"] == 0 else -10)}
        for row in OTP_ROWS
    ]

    with engine.begin() as conn:
        insert_many(
            conn,
            "roles",
            ROLES,
            "INSERT INTO roles (role_id, role_name) VALUES (:role_id, :role_name)",
        )
        insert_many(
            conn,
            "users",
            users_rows,
            """
            INSERT INTO users (user_id, name, email, password, date_of_birth, is_deleted, created_at, updated_at)
            VALUES (:user_id, :name, :email, :password, :date_of_birth, :is_deleted, :created_at, :updated_at)
            """,
        )
        insert_many(
            conn,
            "authentication",
            auth_rows,
            """
            INSERT INTO authentication (auth_id, user_id, password_hash, failed_attempts, account_status, last_login)
            VALUES (:auth_id, :user_id, :password_hash, :failed_attempts, :account_status, :last_login)
            """,
        )
        insert_many(
            conn,
            "user_roles",
            USER_ROLES,
            "INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)",
        )
        insert_many(
            conn,
            "genres",
            GENRES,
            "INSERT INTO genres (genre_id, genre_name) VALUES (:genre_id, :genre_name)",
        )
        insert_many(
            conn,
            "artists",
            artist_rows,
            """
            INSERT INTO artists (artist_id, artist_name, bio, is_deleted, created_at)
            VALUES (:artist_id, :artist_name, :bio, :is_deleted, :created_at)
            """,
        )
        insert_many(
            conn,
            "albums",
            album_rows,
            """
            INSERT INTO albums (album_id, album_name, artist_id, release_date, is_deleted)
            VALUES (:album_id, :album_name, :artist_id, :release_date, :is_deleted)
            """,
        )
        insert_many(
            conn,
            "songs",
            song_rows,
            """
            INSERT INTO songs (song_id, title, duration, artist_id, album_id, genre_id, total_plays, total_likes, is_deleted)
            VALUES (:song_id, :title, :duration, :artist_id, :album_id, :genre_id, :total_plays, :total_likes, :is_deleted)
            """,
        )
        insert_many(
            conn,
            "subscription_plans",
            SUBSCRIPTION_PLANS,
            """
            INSERT INTO subscription_plans (plan_id, plan_name, description, price, duration_days)
            VALUES (:plan_id, :plan_name, :description, :price, :duration_days)
            """,
        )
        insert_many(
            conn,
            "user_subscriptions",
            USER_SUBSCRIPTIONS,
            """
            INSERT INTO user_subscriptions (subscription_id, user_id, plan_id, start_date, end_date, status)
            VALUES (:subscription_id, :user_id, :plan_id, :start_date, :end_date, :status)
            """,
        )
        insert_many(
            conn,
            "transactions",
            transaction_rows,
            """
            INSERT INTO transactions (transaction_id, user_id, subscription_id, amount, payment_method, transaction_date, status)
            VALUES (:transaction_id, :user_id, :subscription_id, :amount, :payment_method, :transaction_date, :status)
            """,
        )
        insert_many(
            conn,
            "devices",
            device_rows,
            """
            INSERT INTO devices (device_id, user_id, device_name, device_type, last_active)
            VALUES (:device_id, :user_id, :device_name, :device_type, :last_active)
            """,
        )
        insert_many(
            conn,
            "sessions",
            session_rows,
            """
            INSERT INTO sessions (session_id, user_id, device_id, login_time, logout_time, status)
            VALUES (:session_id, :user_id, :device_id, :login_time, :logout_time, :status)
            """,
        )
        insert_many(
            conn,
            "playlists",
            playlist_rows,
            """
            INSERT INTO playlists (playlist_id, playlist_name, description, user_id, is_deleted, created_at)
            VALUES (:playlist_id, :playlist_name, :description, :user_id, :is_deleted, :created_at)
            """,
        )
        insert_many(
            conn,
            "playlist_songs",
            playlist_song_rows,
            """
            INSERT INTO playlist_songs (playlist_id, song_id, added_at)
            VALUES (:playlist_id, :song_id, :added_at)
            """,
        )
        insert_many(
            conn,
            "play_history",
            play_history_rows,
            """
            INSERT INTO play_history (play_id, user_id, song_id, played_at)
            VALUES (:play_id, :user_id, :song_id, :played_at)
            """,
        )
        insert_many(
            conn,
            "likes",
            like_rows,
            "INSERT INTO likes (user_id, song_id, liked_at) VALUES (:user_id, :song_id, :liked_at)",
        )
        insert_many(
            conn,
            "downloads",
            download_rows,
            """
            INSERT INTO downloads (download_id, user_id, song_id, downloaded_at)
            VALUES (:download_id, :user_id, :song_id, :downloaded_at)
            """,
        )
        insert_many(
            conn,
            "search_history",
            search_rows,
            """
            INSERT INTO search_history (search_id, user_id, search_query, searched_at)
            VALUES (:search_id, :user_id, :search_query, :searched_at)
            """,
        )
        insert_many(
            conn,
            "user_interest",
            USER_INTEREST,
            """
            INSERT INTO user_interest (user_id, genre_id, interest_score)
            VALUES (:user_id, :genre_id, :interest_score)
            """,
        )
        insert_many(
            conn,
            "recommendations",
            recommendation_rows,
            """
            INSERT INTO recommendations (recommendation_id, user_id, song_id, score, generated_at)
            VALUES (:recommendation_id, :user_id, :song_id, :score, :generated_at)
            """,
        )
        insert_many(
            conn,
            "notifications",
            notification_rows,
            """
            INSERT INTO notifications (notification_id, user_id, message, is_read, created_at)
            VALUES (:notification_id, :user_id, :message, :is_read, :created_at)
            """,
        )
        insert_many(
            conn,
            "follows",
            FOLLOWS,
            "INSERT INTO follows (user_id, artist_id, followed_at) VALUES (:user_id, :artist_id, NOW())",
        )
        insert_many(
            conn,
            "audit_logs",
            audit_rows,
            """
            INSERT INTO audit_logs (log_id, user_id, action, ip_address, created_at)
            VALUES (:log_id, :user_id, :action, :ip_address, :created_at)
            """,
        )
        insert_many(
            conn,
            "otp",
            otp_rows,
            """
            INSERT INTO otp (otp_id, user_id, otp_code, expiry_time, is_used)
            VALUES (:otp_id, :user_id, :otp_code, :expiry_time, :is_used)
            """,
        )


def main() -> None:
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    ensure_columns(engine)
    truncate_tables(engine)
    seed_database(engine)
    print("Database reseeded successfully.")
    print(f"Seeded users can log in with password: {DEFAULT_PASSWORD}")


if __name__ == "__main__":
    main()
