import { useEffect, useMemo, useRef, useState } from "react";
import {
  addSongToPlaylist,
  clearSession,
  clearSearchHistory,
  createPlaylist,
  deleteSearchHistoryItem,
  fetchNotifications,
  fetchPlans,
  fetchPlaylists,
  fetchProfile,
  fetchRecommendations,
  fetchSearchHistory,
  fetchSongs,
  fetchSubscriptionStatus,
  getStoredToken,
  getStoredUser,
  likeSong,
  login,
  persistSession,
  playSong,
  performSearch,
  registerAccount,
  subscribeToPlan,
  updateProfile,
} from "./api";

const sections = [
  { id: "dashboard", label: "Dashboard" },
  { id: "songs", label: "Songs" },
  { id: "discover", label: "Discover" },
  { id: "playlists", label: "Playlists" },
  { id: "plans", label: "Plans" },
  { id: "profile", label: "Profile" },
];

const initialAuthForm = {
  name: "",
  email: "",
  password: "",
  device_identifier: "web-player",
};

function getSongId(song) {
  return Number(song?.song_id || song?.id);
}

function getSongTitle(song) {
  return song?.title || song?.name || "Untitled track";
}

function getSongArtist(song) {
  return song?.artist || song?.artist_name || "Unknown artist";
}

function getSongDuration(song) {
  const rawDuration = Number(song?.duration);
  return Number.isFinite(rawDuration) && rawDuration > 0 ? rawDuration : 180;
}

function formatTime(totalSeconds) {
  const safeSeconds = Math.max(0, Math.floor(totalSeconds));
  const minutes = Math.floor(safeSeconds / 60);
  const seconds = safeSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

function getHistoryQuery(item) {
  return item?.query || item?.search_query || item?.term || item?.q || "";
}

function createAppNotification(title, description, type = "activity") {
  return {
    id: `local-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    title,
    description,
    type,
  };
}

function playlistLabelFromItem(playlist) {
  return playlist?.name || playlist?.playlist_name || playlist?.title || "Untitled playlist";
}

function createSmartNotifications({ userName, currentPlanName, recommendations, playlists, songs }) {
  const smartNotifications = [];
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  smartNotifications.push(
    createAppNotification(
      `${greeting}, ${userName || "listener"}`,
      currentPlanName && currentPlanName !== "Free"
        ? `${currentPlanName} is active. Try something fresh from your recommendations.`
        : "Upgrade a plan to unlock uninterrupted listening and offline access.",
      "welcome",
    ),
  );

  if (recommendations.length > 0) {
    const featured = recommendations[Math.floor(Math.random() * recommendations.length)];
    smartNotifications.push(
      createAppNotification(
        "Recommended for you",
        `${getSongTitle(featured)} by ${getSongArtist(featured)} is a strong match for your taste.`,
        "recommendation",
      ),
    );
  }

  if (playlists.length > 0) {
    const featuredPlaylist = playlists[Math.floor(Math.random() * playlists.length)];
    smartNotifications.push(
      createAppNotification(
        "Playlist ready",
        `${playlistLabelFromItem(featuredPlaylist)} is ready for another session.`,
        "playlist",
      ),
    );
  } else if (songs.length > 0) {
    smartNotifications.push(
      createAppNotification(
        "Queue suggestion",
        "Add a few songs to your queue so playback continues automatically.",
        "queue",
      ),
    );
  }

  return smartNotifications.slice(0, 3);
}

function midiToFrequency(note) {
  return 440 * 2 ** ((note - 69) / 12);
}

function createPreviewAudioUrl(song) {
  const durationSeconds = Math.max(10, Math.min(getSongDuration(song), 18));
  const sampleRate = 22050;
  const totalSamples = durationSeconds * sampleRate;
  const channelCount = 1;
  const bytesPerSample = 2;
  const blockAlign = channelCount * bytesPerSample;
  const byteRate = sampleRate * blockAlign;
  const dataSize = totalSamples * bytesPerSample;
  const buffer = new ArrayBuffer(44 + dataSize);
  const view = new DataView(buffer);
  const title = getSongTitle(song);
  const seed =
    title.split("").reduce((sum, char) => sum + char.charCodeAt(0), 0) + getSongId(song) * 17;
  const baseNotes = [48, 52, 55, 59, 60, 64, 67, 71];
  const melody = Array.from({ length: 8 }, (_, index) => baseNotes[(seed + index) % baseNotes.length]);
  let offset = 0;

  function writeString(value) {
    for (let index = 0; index < value.length; index += 1) {
      view.setUint8(offset, value.charCodeAt(index));
      offset += 1;
    }
  }

  function writeUint32(value) {
    view.setUint32(offset, value, true);
    offset += 4;
  }

  function writeUint16(value) {
    view.setUint16(offset, value, true);
    offset += 2;
  }

  writeString("RIFF");
  writeUint32(36 + dataSize);
  writeString("WAVE");
  writeString("fmt ");
  writeUint32(16);
  writeUint16(1);
  writeUint16(channelCount);
  writeUint32(sampleRate);
  writeUint32(byteRate);
  writeUint16(blockAlign);
  writeUint16(16);
  writeString("data");
  writeUint32(dataSize);

  for (let sampleIndex = 0; sampleIndex < totalSamples; sampleIndex += 1) {
    const time = sampleIndex / sampleRate;
    const step = Math.floor(time * 2) % melody.length;
    const frequency = midiToFrequency(melody[step]);
    const envelope = Math.max(0, 1 - ((time * 2) % 1) * 0.35);
    const sampleValue =
      Math.sin(2 * Math.PI * frequency * time) * 0.45 +
      Math.sin(2 * Math.PI * (frequency / 2) * time) * 0.18;
    const finalValue = Math.max(-1, Math.min(1, sampleValue * envelope));
    view.setInt16(offset, finalValue * 32767, true);
    offset += 2;
  }

  return URL.createObjectURL(new Blob([buffer], { type: "audio/wav" }));
}

function getSongAudioSource(song) {
  return song?.audio_url || null;
}

function App() {
  const [token, setToken] = useState(() => getStoredToken());
  const [activeSection, setActiveSection] = useState("dashboard");
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState(initialAuthForm);
  const [profileForm, setProfileForm] = useState({ name: "", email: "", password: "" });
  const [user, setUser] = useState(() => getStoredUser());
  const [songs, setSongs] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [playlists, setPlaylists] = useState([]);
  const [plans, setPlans] = useState([]);
  const [subscription, setSubscription] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [searchHistory, setSearchHistory] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [query, setQuery] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [newPlaylist, setNewPlaylist] = useState({ name: "" });
  const [selectedPlaylistBySong, setSelectedPlaylistBySong] = useState({});
  const [nowPlaying, setNowPlaying] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackPosition, setPlaybackPosition] = useState(0);
  const [audioDuration, setAudioDuration] = useState(0);
  const [volume, setVolume] = useState(0.8);
  const [isMuted, setIsMuted] = useState(false);
  const [isShuffle, setIsShuffle] = useState(false);
  const [repeatMode, setRepeatMode] = useState("off");
  const [paymentMethod, setPaymentMethod] = useState("upi");
  const [checkoutPlan, setCheckoutPlan] = useState(null);
  const [songQueue, setSongQueue] = useState([]);
  const [paymentForm, setPaymentForm] = useState({
    payerName: "",
    paymentHandle: "",
    cardNumber: "",
    expiry: "",
  });
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const audioRef = useRef(null);
  const previewCacheRef = useRef(new Map());

  const playbackQueue = useMemo(() => {
    const uniqueSongs = new Map();
    const collections = [
      songs,
      recommendations,
      searchResults,
      ...playlists
        .filter((playlist) => Array.isArray(playlist.songs))
        .map((playlist) => playlist.songs),
    ];

    collections.flat().forEach((song) => {
      const id = getSongId(song);
      if (id && !uniqueSongs.has(id)) {
        uniqueSongs.set(id, song);
      }
    });

    return Array.from(uniqueSongs.values());
  }, [playlists, recommendations, searchResults, songs]);

  const currentSongIndex = nowPlaying
    ? playbackQueue.findIndex((song) => getSongId(song) === getSongId(nowPlaying))
    : -1;
  const currentSongDuration = audioDuration || getSongDuration(nowPlaying);
  const progressPercent = nowPlaying
    ? Math.min((playbackPosition / currentSongDuration) * 100, 100)
    : 0;
  const currentPlanName = subscription?.active_plan || subscription?.subscription?.plan_name || "Free";
  const currentPlanPrice =
    subscription?.subscription?.plan_price ??
    subscription?.subscription?.price ??
    0;
  const currentPlanStatus = subscription?.status || subscription?.subscription?.status || "free";
  const currentPlanId = Number(subscription?.subscription?.plan_id || subscription?.subscription?.id || 0);
  const hasPaidPlan = currentPlanName && currentPlanName !== "Free" && currentPlanStatus !== "free";

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) {
      return undefined;
    }

    const handleLoadedMetadata = () => {
      setAudioDuration(audio.duration || 0);
    };
    const handleTimeUpdate = () => {
      setPlaybackPosition(audio.currentTime || 0);
    };
    const handleEnded = () => {
      if (repeatMode === "one" && nowPlaying) {
        audio.currentTime = 0;
        audio.play().catch(() => setIsPlaying(false));
        return;
      }
      handleSkip("next", { autoAdvance: true });
    };

    audio.addEventListener("loadedmetadata", handleLoadedMetadata);
    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("ended", handleEnded);

    return () => {
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("ended", handleEnded);
    };
  }, [nowPlaying, repeatMode, songQueue, playbackQueue, isShuffle, currentSongIndex]);

  useEffect(() => {
    return () => {
      previewCacheRef.current.forEach((url) => URL.revokeObjectURL(url));
      previewCacheRef.current.clear();
    };
  }, []);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    audio.volume = isMuted ? 0 : volume;
  }, [isMuted, volume]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !nowPlaying) {
      return;
    }

    const songId = getSongId(nowPlaying);
    let nextSource = getSongAudioSource(nowPlaying);
    if (!nextSource) {
      if (!previewCacheRef.current.has(songId)) {
        previewCacheRef.current.set(songId, createPreviewAudioUrl(nowPlaying));
      }
      nextSource = previewCacheRef.current.get(songId);
    }
    if (audio.dataset.songId !== String(songId)) {
      audio.src = nextSource;
      audio.dataset.songId = String(songId);
      audio.load();
      setAudioDuration(0);
    }
  }, [nowPlaying]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    if (!nowPlaying) {
      audio.pause();
      audio.removeAttribute("src");
      audio.load();
      setAudioDuration(0);
      return;
    }

    if (isPlaying) {
      audio.play().catch(() => setIsPlaying(false));
    } else {
      audio.pause();
    }
  }, [isPlaying, nowPlaying]);

  function playlistLabel(playlist) {
    return playlistLabelFromItem(playlist);
  }

  function pushNotification(title, description, type = "activity") {
    setNotifications((current) => [createAppNotification(title, description, type), ...current].slice(0, 12));
  }

  function dismissNotification(notificationId) {
    setNotifications((current) =>
      current.filter((item, index) => (item.id || item.notification_id || index) !== notificationId),
    );
  }

  function queueSong(song) {
    if (!song) {
      return;
    }

    const queuedSongId = getSongId(song);
    setSongQueue((current) => {
      if (current.some((item) => getSongId(item) === queuedSongId)) {
        return current;
      }
      return [...current, song];
    });
    pushNotification("Added to queue", `${getSongTitle(song)} will play next.`, "queue");
  }

  function removeQueuedSong(songId) {
    setSongQueue((current) => current.filter((item) => getSongId(item) !== Number(songId)));
  }

  function patchSongCollections(songId, updates) {
    const applyUpdate = (items) =>
      items.map((song) =>
        (song.song_id || song.id) === songId ? { ...song, ...updates } : song,
      );

    setSongs((current) => applyUpdate(current));
    setRecommendations((current) => applyUpdate(current));
    setSearchResults((current) => applyUpdate(current));
    setPlaylists((current) =>
      current.map((playlist) => ({
        ...playlist,
        songs: Array.isArray(playlist.songs) ? applyUpdate(playlist.songs) : playlist.songs,
      })),
    );
    setNowPlaying((current) =>
      current && (current.song_id || current.id) === songId ? { ...current, ...updates } : current,
    );
  }

  function appendSongToPlaylistState(playlistId, songId) {
    const normalizedPlaylistId = Number(playlistId);
    const normalizedSongId = Number(songId);
    const song =
      songs.find((item) => Number(item.song_id || item.id) === normalizedSongId) ||
      searchResults.find((item) => Number(item.song_id || item.id) === normalizedSongId) ||
      recommendations.find((item) => Number(item.song_id || item.id) === normalizedSongId);

    if (!song) {
      return;
    }

    setPlaylists((current) =>
      current.map((playlist) => {
        if (Number(playlist.playlist_id || playlist.id) !== normalizedPlaylistId) {
          return playlist;
        }

        const existingSongs = Array.isArray(playlist.songs) ? playlist.songs : [];
        const alreadyPresent = existingSongs.some(
          (item) => Number(item.song_id || item.id) === normalizedSongId,
        );

        if (alreadyPresent) {
          return {
            ...playlist,
            song_count: existingSongs.length,
            songs: existingSongs,
          };
        }

        return {
          ...playlist,
          song_count: existingSongs.length + 1,
          songs: [...existingSongs, song],
        };
      }),
    );
  }

  async function refreshPlaylists() {
    try {
      const playlistsResponse = await fetchPlaylists();
      setPlaylists(playlistsResponse.data?.items ?? []);
    } catch (error) {
      setStatus(error.message);
    }
  }

  useEffect(() => {
    if (!token) {
      return;
    }

    hydrateApp();
  }, [token]);

  useEffect(() => {
    if (!nowPlaying || !isPlaying) {
      return undefined;
    }

    const timer = window.setInterval(() => {
      setPlaybackPosition((current) => {
        const nextValue = current + 1;

        if (nextValue >= currentSongDuration) {
          window.clearInterval(timer);
          handleSkip("next");
          return 0;
        }

        return nextValue;
      });
    }, 1000);

    return () => window.clearInterval(timer);
  }, [currentSongDuration, isPlaying, nowPlaying, playbackQueue]);

  async function hydrateApp() {
    setLoading(true);
    setStatus("Syncing your library...");

    try {
      const profileResponse = await fetchProfile();
      const profileData = profileResponse.data ?? null;
      setUser(profileData);
      persistSession(getStoredToken(), profileData);
      setProfileForm({
        name: profileData?.name ?? "",
        email: profileData?.email ?? "",
        password: "",
      });

      const results = await Promise.allSettled([
        fetchSongs(),
        fetchRecommendations(),
        fetchPlaylists(),
        fetchPlans(),
        fetchSubscriptionStatus(),
        fetchNotifications(),
        fetchSearchHistory(),
      ]);

      const [
        songsResult,
        recommendationsResult,
        playlistsResult,
        plansResult,
        subscriptionResult,
        notificationsResult,
        searchHistoryResult,
      ] = results;

      setSongs(songsResult.status === "fulfilled" ? songsResult.value.data?.items ?? [] : []);
      setRecommendations(
        recommendationsResult.status === "fulfilled"
          ? recommendationsResult.value.data?.items ?? []
          : [],
      );
      setPlaylists(
        playlistsResult.status === "fulfilled" ? playlistsResult.value.data?.items ?? [] : [],
      );
      setPlans(plansResult.status === "fulfilled" ? plansResult.value.data?.items ?? [] : []);
      setSubscription(
        subscriptionResult.status === "fulfilled" ? subscriptionResult.value.data ?? null : null,
      );
      const serverNotifications =
        notificationsResult.status === "fulfilled"
          ? notificationsResult.value.data?.items ?? []
          : [];
      setNotifications([
        ...createSmartNotifications({
          userName: profileData?.name,
          currentPlanName:
            subscriptionResult.status === "fulfilled"
              ? subscriptionResult.value.data?.active_plan || "Free"
              : "Free",
          recommendations:
            recommendationsResult.status === "fulfilled"
              ? recommendationsResult.value.data?.items ?? []
              : [],
          playlists:
            playlistsResult.status === "fulfilled"
              ? playlistsResult.value.data?.items ?? []
              : [],
          songs: songsResult.status === "fulfilled" ? songsResult.value.data?.items ?? [] : [],
        }),
        ...serverNotifications,
      ]);
      setSearchHistory(
        searchHistoryResult.status === "fulfilled"
          ? searchHistoryResult.value.data?.items ?? []
          : [],
      );

      const failedLoads = results.filter((result) => result.status === "rejected");
      setStatus(
        failedLoads.length > 0
          ? "The app loaded, but some sections could not fetch data from the backend."
          : "Everything is loaded.",
      );
    } catch (error) {
      clearSession();
      setToken(null);
      setUser(null);
      setStatus(
        "Saved session could not be restored. Please sign in again after checking your backend and database.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleAuthSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setStatus(authMode === "login" ? "Signing you in..." : "Creating your account...");

    try {
      const response =
        authMode === "login"
          ? await login({
              email: authForm.email,
              password: authForm.password,
              device_identifier: authForm.device_identifier,
            })
          : await registerAccount({
              name: authForm.name,
              email: authForm.email,
              password: authForm.password,
            });

      const responseUser = {
        id: response.data?.user_id,
        name: authForm.name || authForm.email.split("@")[0],
        email: authForm.email,
      };

      persistSession(response.data?.access_token, responseUser);
      setToken(response.data?.access_token);
      setUser(responseUser);
      setAuthForm(initialAuthForm);
      setStatus(authMode === "login" ? "Welcome back." : "Account created.");
    } catch (error) {
      setStatus(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch(event) {
    event.preventDefault();
    if (!query.trim()) {
      setStatus("Enter a song title to search.");
      return;
    }

    await runSearchQuery(query.trim());
  }

  async function runSearchQuery(searchText) {
    setLoading(true);
    setStatus(`Searching for "${searchText}"...`);
    try {
      const response = await performSearch(searchText);
      setSearchResults(response.data?.items ?? []);
      const historyResponse = await fetchSearchHistory();
      setSearchHistory(historyResponse.data?.items ?? []);
      setQuery(searchText);
      setActiveSection("discover");
      setShowSuggestions(false);
      setStatus("Search completed.");
    } catch (error) {
      setStatus(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleClearSearchHistory() {
    setLoading(true);
    try {
      const response = await clearSearchHistory();
      setSearchHistory([]);
      setShowSuggestions(false);
      setStatus(response.message ?? "Search history cleared.");
    } catch (error) {
      setStatus(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleRemoveSearchHistoryItem(searchId) {
    try {
      const response = await deleteSearchHistoryItem(searchId);
      setSearchHistory((current) =>
        current.filter((item) => Number(item.search_id || item.id) !== Number(searchId)),
      );
      setStatus(response.message ?? "Search removed from history.");
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function handleLike(songId) {
    try {
      const response = await likeSong(songId);
      const likedSong =
        songs.find((item) => getSongId(item) === Number(songId)) ||
        searchResults.find((item) => getSongId(item) === Number(songId)) ||
        recommendations.find((item) => getSongId(item) === Number(songId));
      patchSongCollections(songId, {
        liked_by_user: response.data?.liked ?? false,
        total_likes: response.data?.total_likes,
      });
      pushNotification(
        response.data?.liked ? "Liked track" : "Like removed",
        `${getSongTitle(likedSong)} ${response.data?.liked ? "was added to" : "was removed from"} your liked songs.`,
        "like",
      );
      setStatus(response.message ?? "Song updated.");
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function handlePlay(songId) {
    try {
      const response = await playSong(songId);
      if (response.data?.song) {
        patchSongCollections(songId, {
          total_plays: response.data.song.total_plays,
        });
        setNowPlaying(response.data.song);
        setSongQueue((current) =>
          current.filter((item) => getSongId(item) !== getSongId(response.data.song)),
        );
        setPlaybackPosition(0);
        if (audioRef.current) {
          audioRef.current.currentTime = 0;
        }
        setIsPlaying(true);
        pushNotification(
          "Now playing",
          `${getSongTitle(response.data.song)} by ${getSongArtist(response.data.song)} started playing.`,
          "play",
        );
      }
      setStatus(response.message ?? "Play recorded.");
    } catch (error) {
      setStatus(error.message);
    }
  }

  function handleTogglePlayback() {
    if (!nowPlaying) {
      return;
    }

    setIsPlaying((current) => !current);
  }

  function handleDismissPlayer() {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setNowPlaying(null);
    setIsPlaying(false);
    setPlaybackPosition(0);
    setAudioDuration(0);
  }

  function handleSkip(direction, options = {}) {
    if (direction === "next" && songQueue.length > 0) {
      const nextQueuedSong = songQueue[0];
      setSongQueue((current) => current.slice(1));
      handlePlay(getSongId(nextQueuedSong));
      return;
    }

    if (!playbackQueue.length) {
      return;
    }

    if (direction === "previous" && playbackPosition > 3 && audioRef.current) {
      audioRef.current.currentTime = 0;
      setPlaybackPosition(0);
      return;
    }

    const fallbackIndex = currentSongIndex >= 0 ? currentSongIndex : 0;
    if (direction === "next" && isShuffle && playbackQueue.length > 1) {
      const candidates = playbackQueue.filter((song) => getSongId(song) !== getSongId(nowPlaying));
      const randomSong = candidates[Math.floor(Math.random() * candidates.length)];
      if (randomSong) {
        handlePlay(getSongId(randomSong));
        return;
      }
    }

    if (
      direction === "next" &&
      options.autoAdvance &&
      repeatMode === "off" &&
      fallbackIndex === playbackQueue.length - 1
    ) {
      if (audioRef.current) {
        audioRef.current.currentTime = 0;
      }
      setPlaybackPosition(0);
      setIsPlaying(false);
      return;
    }

    const targetIndex =
      direction === "previous"
        ? (fallbackIndex - 1 + playbackQueue.length) % playbackQueue.length
        : (fallbackIndex + 1) % playbackQueue.length;

    const targetSong = playbackQueue[targetIndex];
    if (targetSong) {
      handlePlay(getSongId(targetSong));
    }
  }

  async function handleCreatePlaylist(event) {
    event.preventDefault();
    if (!newPlaylist.name.trim()) {
      setStatus("Playlist name is required.");
      return;
    }

    setLoading(true);
    setStatus("Creating playlist...");
    try {
      const response = await createPlaylist(newPlaylist);
      setPlaylists((current) => [response.data, ...current]);
      setNewPlaylist({ name: "" });
      pushNotification("Playlist created", `${playlistLabel(response.data)} is ready for new songs.`, "playlist");
      setStatus("Playlist created.");
    } catch (error) {
      setStatus(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAddSongToPlaylist(songId) {
    const playlistId = selectedPlaylistBySong[songId];
    if (!playlistId) {
      setStatus("Choose a playlist first.");
      return;
    }

    setLoading(true);
    setStatus("Adding song to playlist...");
    try {
      const response = await addSongToPlaylist(playlistId, songId);
      appendSongToPlaylistState(playlistId, songId);
      await refreshPlaylists();
      setSelectedPlaylistBySong((current) => {
        const next = { ...current };
        delete next[songId];
        return next;
      });
      const song =
        songs.find((item) => getSongId(item) === Number(songId)) ||
        searchResults.find((item) => getSongId(item) === Number(songId)) ||
        recommendations.find((item) => getSongId(item) === Number(songId));
      const playlist = playlists.find((item) => Number(item.playlist_id || item.id) === Number(playlistId));
      pushNotification(
        "Added to playlist",
        `${getSongTitle(song)} was added to ${playlist ? playlistLabel(playlist) : "your playlist"}.`,
        "playlist",
      );
      setStatus(response.message ?? "Song added to playlist.");
    } catch (error) {
      setStatus(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubscribe(plan) {
    setLoading(true);
    setStatus(`Processing your ${plan.name || plan.plan_name} purchase...`);

    try {
      const subscribeResponse = await subscribeToPlan({
        plan_id: plan.id || plan.plan_id,
        payment_method: paymentMethod,
      });
      const statusResponse = await fetchSubscriptionStatus();
      const purchasedPlanId = Number(plan.id || plan.plan_id);
      const fetchedStatus = statusResponse.data ?? null;
      const fetchedPlanId = Number(
        fetchedStatus?.subscription?.plan_id || fetchedStatus?.subscription?.id || 0,
      );
      const nextSubscription =
        fetchedPlanId === purchasedPlanId
          ? fetchedStatus
          : {
              subscribed: true,
              status: "active",
              active_plan: subscribeResponse.data?.plan_name || plan.name || plan.plan_name,
              subscription: {
                ...subscribeResponse.data,
                plan_id: purchasedPlanId,
                plan_name: subscribeResponse.data?.plan_name || plan.name || plan.plan_name,
                plan_price: subscribeResponse.data?.plan_price ?? plan.price ?? 0,
                status: "active",
              },
            };
      setSubscription(nextSubscription);
      setNotifications((current) => [
        {
          title: "Plan updated",
          description: `${plan.name || plan.plan_name} is now active on your account.`,
        },
        ...current,
      ]);
      setStatus(
        subscribeResponse.message ??
          `${plan.name || plan.plan_name} is now active on your account.`,
      );
      return true;
    } catch (error) {
      setStatus(error.message);
      return false;
    } finally {
      setLoading(false);
    }
  }

  function openCheckout(plan) {
    setCheckoutPlan(plan);
    setPaymentForm({
      payerName: user?.name || "",
      paymentHandle: user?.email || "",
      cardNumber: "",
      expiry: "",
    });
  }

  function closeCheckout() {
    setCheckoutPlan(null);
  }

  function handleSeek(event) {
    const nextPosition = Number(event.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = nextPosition;
    }
    setPlaybackPosition(nextPosition);
  }

  function handleVolumeChange(event) {
    const nextVolume = Number(event.target.value);
    setVolume(nextVolume);
    if (nextVolume > 0 && isMuted) {
      setIsMuted(false);
    }
  }

  function toggleMute() {
    setIsMuted((current) => !current);
  }

  function toggleShuffle() {
    setIsShuffle((current) => !current);
  }

  function cycleRepeatMode() {
    setRepeatMode((current) => {
      if (current === "off") {
        return "all";
      }
      if (current === "all") {
        return "one";
      }
      return "off";
    });
  }

  async function handleCheckoutConfirm(event) {
    event.preventDefault();
    if (!checkoutPlan) {
      return;
    }

    if (!paymentForm.payerName.trim()) {
      setStatus("Enter the account holder name before confirming payment.");
      return;
    }

    if (paymentMethod === "upi" && !paymentForm.paymentHandle.trim()) {
      setStatus("Enter a UPI ID or payment handle.");
      return;
    }

    if ((paymentMethod === "card" || paymentMethod === "netbanking") && !paymentForm.cardNumber.trim()) {
      setStatus("Enter a reference number for this demo payment.");
      return;
    }

    const purchased = await handleSubscribe(checkoutPlan);
    if (purchased) {
      setCheckoutPlan(null);
    }
  }

  async function handleProfileUpdate(event) {
    event.preventDefault();
    const payload = Object.fromEntries(
      Object.entries(profileForm).filter(([, value]) => value),
    );

    if (Object.keys(payload).length === 0) {
      setStatus("Nothing changed.");
      return;
    }

    setLoading(true);
    setStatus("Saving profile...");
    try {
      const response = await updateProfile(payload);
      setUser(response.data ?? null);
      setProfileForm({
        name: response.data?.name ?? "",
        email: response.data?.email ?? "",
        password: "",
      });
      persistSession(getStoredToken(), response.data ?? null);
      setStatus("Profile updated.");
    } catch (error) {
      setStatus(error.message);
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    clearSession();
    setToken(null);
    setUser(null);
    setSongs([]);
    setRecommendations([]);
    setPlaylists([]);
    setPlans([]);
    setSubscription(null);
    setNotifications([]);
    setSongQueue([]);
    setSearchResults([]);
    setSearchHistory([]);
    setSelectedPlaylistBySong({});
    setNowPlaying(null);
    setIsPlaying(false);
    setPlaybackPosition(0);
    setStatus("Signed out.");
  }

  const searchSuggestions =
    !showSuggestions || query.trim().length === 0
      ? []
      : songs
          .filter((song) =>
            (song.title || "").toLowerCase().includes(query.trim().toLowerCase()),
          )
          .slice(0, 6);

  const recentSearchItems = useMemo(() => {
    const library = [
      ...songs,
      ...recommendations,
      ...searchResults,
      ...playlists.flatMap((playlist) => (Array.isArray(playlist.songs) ? playlist.songs : [])),
    ];
    const seen = new Set();

    return searchHistory
      .map((item) => {
        const historyQuery = getHistoryQuery(item).trim();
        if (!historyQuery) {
          return null;
        }

        const loweredQuery = historyQuery.toLowerCase();
        const matchedSong = library.find((song) => {
          const title = getSongTitle(song).toLowerCase();
          return title === loweredQuery || title.includes(loweredQuery) || loweredQuery.includes(title);
        });

        const dedupeKey = matchedSong ? `song-${getSongId(matchedSong)}` : `query-${loweredQuery}`;
        if (seen.has(dedupeKey)) {
          return null;
        }

        seen.add(dedupeKey);
        return {
          id: item.search_id || dedupeKey,
          query: historyQuery,
          song: matchedSong || null,
        };
      })
      .filter(Boolean)
      .slice(0, 6);
  }, [playlists, recommendations, searchHistory, searchResults, songs]);

  const showSearchDropdown =
    showSuggestions && (searchSuggestions.length > 0 || recentSearchItems.length > 0);

  if (!token) {
    return (
      <div className="shell auth-shell">
        <section className="hero-panel">
          <p className="eyebrow">TuneBase</p>
          <h1>TuneBase</h1>
          <p className="hero-copy">
            A streaming dashboard for your Flask and MySQL music platform.
            Sign in to browse songs, create playlists, check plans, and manage your profile.
          </p>
          <div className="hero-metrics">
            <div>
              <strong>Auth</strong>
              <span>JWT-based session flow</span>
            </div>
            <div>
              <strong>Library</strong>
              <span>Songs, search, likes, and plays</span>
            </div>
            <div>
              <strong>Billing</strong>
              <span>Plans and subscription status</span>
            </div>
          </div>
        </section>

        <section className="auth-card">
          <div className="tab-row">
            <button
              className={authMode === "login" ? "active" : ""}
              onClick={() => setAuthMode("login")}
              type="button"
            >
              Login
            </button>
            <button
              className={authMode === "register" ? "active" : ""}
              onClick={() => setAuthMode("register")}
              type="button"
            >
              Register
            </button>
          </div>

          <form className="stack" onSubmit={handleAuthSubmit}>
            {authMode === "register" && (
              <label>
                Name
                <input
                  value={authForm.name}
                  onChange={(event) => setAuthForm({ ...authForm, name: event.target.value })}
                  placeholder="Aarav"
                />
              </label>
            )}

            <label>
              Email
              <input
                type="email"
                value={authForm.email}
                onChange={(event) => setAuthForm({ ...authForm, email: event.target.value })}
                placeholder="you@example.com"
              />
            </label>

            <label>
              Password
              <input
                type="password"
                value={authForm.password}
                onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })}
                placeholder="Password123!"
              />
            </label>

            {authMode === "login" && (
              <label>
                Device identifier
                <input
                  value={authForm.device_identifier}
                  onChange={(event) =>
                    setAuthForm({ ...authForm, device_identifier: event.target.value })
                  }
                  placeholder="web-player"
                />
              </label>
            )}

            <button className="primary" disabled={loading} type="submit">
              {loading ? "Please wait..." : authMode === "login" ? "Enter App" : "Create Account"}
            </button>
          </form>

          <p className="status-text">{status}</p>
        </section>
      </div>
    );
  }

  return (
    <div className="shell app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">TuneBase</p>
          <h2>Music Console</h2>
        </div>

        <nav className="nav-stack">
          {sections.map((section) => (
            <button
              key={section.id}
              className={activeSection === section.id ? "nav-item active" : "nav-item"}
              onClick={() => setActiveSection(section.id)}
              type="button"
            >
              {section.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-card">
          <span>Signed in as</span>
          <strong>{user?.name || user?.email || "Listener"}</strong>
          <button className="ghost" onClick={handleLogout} type="button">
            Sign out
          </button>
        </div>
      </aside>

      <main className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Welcome back</p>
            <h1>{user?.name || "Your streaming workspace"}</h1>
          </div>

          <form className="searchbar" onSubmit={handleSearch}>
            <div className="search-input-wrap">
              <input
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setShowSuggestions(true);
                }}
                onFocus={() => setShowSuggestions(true)}
                placeholder="Search songs by title"
              />
              {showSearchDropdown && (
                <div className="search-suggestions">
                  {query.trim().length === 0 ? (
                    <>
                      <div className="search-suggestions-header">
                        <strong>Recent searches</strong>
                        {recentSearchItems.length > 0 && (
                          <button
                            className="search-clear-button"
                            onClick={handleClearSearchHistory}
                            type="button"
                          >
                            Clear all
                          </button>
                        )}
                      </div>
                      {recentSearchItems.length === 0 ? (
                        <p className="search-empty-state">No recent searches yet.</p>
                      ) : (
                        recentSearchItems.map((item) => (
                          <div key={`recent-${item.id}`} className="search-history-item">
                            <div className="search-history-art" aria-hidden="true">
                              {item.song ? getSongTitle(item.song).slice(0, 2).toUpperCase() : "S"}
                            </div>
                            <button
                              className="search-history-main"
                              onClick={async () => {
                                setQuery(item.song ? getSongTitle(item.song) : item.query);
                                setShowSuggestions(false);
                                if (item.song) {
                                  setSearchResults([item.song]);
                                } else {
                                  await runSearchQuery(item.query);
                                }
                                setActiveSection("discover");
                              }}
                              type="button"
                            >
                              <div className="search-history-copy">
                                <strong>{item.song ? getSongTitle(item.song) : item.query}</strong>
                                <span>
                                  {item.song
                                    ? `Song - ${getSongArtist(item.song)}`
                                    : "Recent search"}
                                </span>
                              </div>
                            </button>
                            <button
                              className="history-close-button"
                              onClick={() => handleRemoveSearchHistoryItem(item.id)}
                              type="button"
                              aria-label={`Remove ${item.query} from history`}
                            >
                              x
                            </button>
                          </div>
                        ))
                      )}
                    </>
                  ) : (
                    <>
                      <div className="search-suggestions-header">
                        <strong>Suggestions</strong>
                        <button
                          className="close-chip"
                          onClick={() => setShowSuggestions(false)}
                          type="button"
                        >
                          x
                        </button>
                      </div>
                      {searchSuggestions.map((song) => (
                        <button
                          key={`suggestion-${song.song_id || song.id}`}
                          className="search-history-item search-history-main"
                          onClick={() => {
                            setQuery(song.title || "");
                            setShowSuggestions(false);
                            setSearchResults([song]);
                            setActiveSection("discover");
                          }}
                          type="button"
                        >
                          <div className="search-history-art" aria-hidden="true">
                            {getSongTitle(song).slice(0, 2).toUpperCase()}
                          </div>
                          <div className="search-history-copy">
                            <strong>{getSongTitle(song)}</strong>
                            <span>Song - {getSongArtist(song)}</span>
                          </div>
                        </button>
                      ))}
                    </>
                  )}
                </div>
              )}
            </div>
            <button className="primary" disabled={loading} type="submit">
              Search
            </button>
          </form>
        </header>

        <p className="status-banner">{status}</p>

        {activeSection === "dashboard" && (
          <section className="grid two-up">
            <article className="panel spotlight">
              <p className="eyebrow">Overview</p>
              <h3>Everything important in one glance</h3>
              <div className="stats-row">
                <div className="stat-tile">
                  <span>Library</span>
                  <strong>{songs.length}</strong>
                </div>
                <div className="stat-tile">
                  <span>Recommendations</span>
                  <strong>{recommendations.length}</strong>
                </div>
                <div className="stat-tile">
                  <span>Playlists</span>
                  <strong>{playlists.length}</strong>
                </div>
                <div className="stat-tile">
                  <span>Current Plan</span>
                  <strong>{currentPlanName}</strong>
                </div>
              </div>
            </article>

            <article className="panel">
              <p className="eyebrow">Subscription</p>
              <h3>{hasPaidPlan ? currentPlanName : "No active plan"}</h3>
              <p className="muted">
                Status: {currentPlanStatus}
              </p>
              <div className="detail-stack compact-detail-stack">
                <div>
                  <span>Billing</span>
                  <strong>{hasPaidPlan && currentPlanPrice ? `Rs. ${currentPlanPrice}` : "Free access"}</strong>
                </div>
                <div>
                  <span>Access</span>
                  <strong>{hasPaidPlan ? "Premium unlocked" : "Ad-supported streaming"}</strong>
                </div>
              </div>
            </article>

            <article className="panel">
              <p className="eyebrow">Latest Recommendations</p>
              <div className="list-stack">
                {recommendations.slice(0, 4).map((song) => (
                  <div className="list-row" key={`rec-${song.id || song.song_id}`}>
                    <div>
                      <strong>{song.title || song.name || "Untitled track"}</strong>
                      <span>{song.artist || song.artist_name || "Unknown artist"}</span>
                    </div>
                    <div className="history-row-actions">
                      <button className="ghost" onClick={() => handlePlay(song.id || song.song_id)} type="button">
                        Play
                      </button>
                      <button className="ghost" onClick={() => queueSong(song)} type="button">
                        Queue
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="panel">
              <p className="eyebrow">Notifications</p>
              <div className="list-stack">
                {notifications.length === 0 && <p className="muted">No notifications yet.</p>}
                {notifications.slice(0, 4).map((item, index) => (
                  <div className="notice" key={`notice-${index}`}>
                    <div className="notice-row">
                      <strong>{item.title || item.message || "Update"}</strong>
                      <button
                        className="history-close-button history-close-button-dark"
                        onClick={() => dismissNotification(item.id || item.notification_id || index)}
                        type="button"
                        aria-label={`Dismiss ${item.title || item.message || "notification"}`}
                      >
                        x
                      </button>
                    </div>
                    <span>{item.description || item.type || "Activity from your account"}</span>
                  </div>
                ))}
              </div>
            </article>

            <article className="panel">
              <p className="eyebrow">Queue</p>
              <h3>Up next</h3>
              <div className="list-stack">
                {songQueue.length === 0 && <p className="muted">Queue songs to keep playback going.</p>}
                {songQueue.map((song, index) => (
                  <div className="list-row" key={`queue-${getSongId(song)}-${index}`}>
                    <div>
                      <strong>{getSongTitle(song)}</strong>
                      <span>{getSongArtist(song)}</span>
                    </div>
                    <div className="history-row-actions">
                      <button className="ghost" onClick={() => handlePlay(getSongId(song))} type="button">
                        Play now
                      </button>
                      <button
                        className="history-close-button history-close-button-dark"
                        onClick={() => removeQueuedSong(getSongId(song))}
                        type="button"
                        aria-label={`Remove ${getSongTitle(song)} from queue`}
                      >
                        x
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </section>
        )}

        {activeSection === "songs" && (
          <section className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Library</p>
                <h3>Available songs</h3>
              </div>
            </div>
            <div className="card-grid">
              {songs.map((song) => (
                <article className="song-card" key={song.id || song.song_id}>
                  <div>
                    <h4>{song.title || song.name || "Untitled track"}</h4>
                    <p>{song.artist || song.artist_name || "Unknown artist"}</p>
                  </div>
                  <div className="song-meta">
                    <span>{song.genre || song.genre_name || "Genre pending"}</span>
                    <span>{song.duration ? `${song.duration}s` : "Length unavailable"}</span>
                  </div>
                  <div className="song-stats">
                    <span>{song.total_plays ?? 0} plays</span>
                    <span>{song.total_likes ?? 0} likes</span>
                  </div>
                  <div className="action-row">
                    <button className="primary" onClick={() => handlePlay(song.id || song.song_id)} type="button">
                      Play
                    </button>
                    <button className="ghost" onClick={() => queueSong(song)} type="button">
                      Queue
                    </button>
                    <button
                      className={song.liked_by_user ? "heart-button active" : "heart-button"}
                      onClick={() => handleLike(song.id || song.song_id)}
                      type="button"
                    >
                      ♥
                    </button>
                  </div>
                  <div className="playlist-adder">
                    <select
                      value={selectedPlaylistBySong[song.song_id || song.id] || ""}
                      onChange={(event) =>
                        setSelectedPlaylistBySong((current) => ({
                          ...current,
                          [song.song_id || song.id]: event.target.value,
                        }))
                      }
                    >
                      <option value="">Add to playlist</option>
                      {playlists.map((playlist) => (
                        <option key={`playlist-option-${playlist.playlist_id || playlist.id}`} value={playlist.playlist_id || playlist.id}>
                          {playlistLabel(playlist)}
                        </option>
                      ))}
                    </select>
                    <button className="ghost" onClick={() => handleAddSongToPlaylist(song.song_id || song.id)} type="button">
                      Add
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}

        {activeSection === "discover" && (
          <section className="grid two-up">
            <article className="panel">
              <p className="eyebrow">Search Results</p>
              <h3>Results for "{query || "your last search"}"</h3>
              <div className="list-stack">
                {searchResults.length === 0 && <p className="muted">Run a search to see matching songs.</p>}
                {searchResults.map((song) => (
                  <div className="list-row" key={`search-${song.id || song.song_id}`}>
                    <div>
                      <strong>{song.title || song.name || "Untitled track"}</strong>
                      <span>{song.artist || song.artist_name || "Unknown artist"}</span>
                    </div>
                    <div className="history-row-actions">
                      <button className="ghost" onClick={() => handlePlay(song.id || song.song_id)} type="button">
                        Play
                      </button>
                      <button className="ghost" onClick={() => queueSong(song)} type="button">
                        Queue
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="panel">
              <p className="eyebrow">Recent Searches</p>
              <h3>Search history</h3>
              <div className="list-stack">
                {searchHistory.length === 0 && <p className="muted">Search history will appear here.</p>}
                {searchHistory.map((item, index) => (
                  <div className="list-row" key={`history-${index}`}>
                    <div>
                      <strong>{item.query || item.search_query || item.term || "Unknown query"}</strong>
                      <span>{item.created_at || item.id || "Recorded in history"}</span>
                    </div>
                    <div className="history-row-actions">
                      <button
                        className="ghost"
                        onClick={() => {
                          setQuery(item.query || item.search_query || item.term || "");
                        }}
                        type="button"
                      >
                        Reuse
                      </button>
                      <button
                        className="history-close-button history-close-button-dark"
                        onClick={() => handleRemoveSearchHistoryItem(item.search_id || item.id)}
                        type="button"
                        aria-label={`Remove ${getHistoryQuery(item)} from history`}
                      >
                        x
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </section>
        )}

        {activeSection === "playlists" && (
          <section className="grid two-up">
            <article className="panel">
              <p className="eyebrow">Create Playlist</p>
              <h3>Save a new collection</h3>
              <form className="stack" onSubmit={handleCreatePlaylist}>
                <label>
                  Playlist name
                  <input
                    value={newPlaylist.name}
                    onChange={(event) =>
                      setNewPlaylist({ ...newPlaylist, name: event.target.value })
                    }
                    placeholder="Late Night Drive"
                  />
                </label>
                <button className="primary" disabled={loading} type="submit">
                  Create playlist
                </button>
              </form>
            </article>

            <article className="panel">
              <p className="eyebrow">Your Playlists</p>
              <h3>Collections in your library</h3>
              <div className="list-stack">
                {playlists.length === 0 && <p className="muted">You have not created any playlists yet.</p>}
                {playlists.map((playlist, index) => (
                  <div className="notice" key={`playlist-${playlist.playlist_id || playlist.id || index}`}>
                    <strong>{playlistLabel(playlist)}</strong>
                    <span>{typeof playlist.song_count === "number" ? `${playlist.song_count} songs` : "0 songs"}</span>
                    {Array.isArray(playlist.songs) && playlist.songs.length > 0 && (
                      <div className="playlist-song-list">
                        {playlist.songs.map((song) => (
                          <button
                            key={`playlist-song-${playlist.playlist_id || playlist.id}-${song.song_id || song.id}`}
                            className="playlist-song-row"
                            onClick={() => handlePlay(song.song_id || song.id)}
                            type="button"
                          >
                            <strong>{song.title}</strong>
                            <span>{song.artist_name || "Unknown artist"}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </article>
          </section>
        )}

        {activeSection === "plans" && (
          <section className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Billing</p>
                <h3>Subscription plans</h3>
              </div>
              <span className="pill">
                {currentPlanName ? `Current: ${currentPlanName}` : "Current: Free"}
              </span>
            </div>
            <div className="billing-toolbar">
              <label className="billing-select">
                Payment method
                <select value={paymentMethod} onChange={(event) => setPaymentMethod(event.target.value)}>
                  <option value="upi">UPI</option>
                  <option value="card">Card</option>
                  <option value="netbanking">Net banking</option>
                </select>
              </label>
              <p className="muted">
                Demo checkout is instant for now. Buying a plan updates the current user immediately.
              </p>
            </div>
            <div className="card-grid">
              {plans.map((plan, index) => (
                <article
                  className={
                    currentPlanId === Number(plan.id || plan.plan_id)
                      ? "plan-card active-plan-card"
                      : "plan-card"
                  }
                  key={`plan-${plan.id || index}`}
                >
                  <h4>{plan.name || plan.plan_name || `Plan ${index + 1}`}</h4>
                  <p>{plan.description || "Streaming benefits tailored for TuneBase listeners."}</p>
                  <strong>
                    {plan.price !== null && plan.price !== undefined
                      ? Number(plan.price) === 0
                        ? "Free"
                        : `Rs. ${plan.price}`
                      : "Contact admin"}
                  </strong>
                  <span className="muted">
                    {plan.duration_days ? `${plan.duration_days} days access` : "Monthly access"}
                  </span>
                  <button
                    className="primary"
                    disabled={loading || currentPlanId === Number(plan.id || plan.plan_id)}
                    onClick={() => openCheckout(plan)}
                    type="button"
                  >
                    {currentPlanId === Number(plan.id || plan.plan_id)
                      ? "Current plan"
                      : Number(plan.price) > 0
                        ? "Buy plan"
                        : "Switch to free"}
                  </button>
                </article>
              ))}
            </div>
          </section>
        )}

        {activeSection === "profile" && (
          <section className="grid two-up">
            <article className="panel">
              <p className="eyebrow">Account</p>
              <h3>Edit profile</h3>
              <form className="stack" onSubmit={handleProfileUpdate}>
                <label>
                  Name
                  <input
                    value={profileForm.name}
                    onChange={(event) => setProfileForm({ ...profileForm, name: event.target.value })}
                  />
                </label>
                <label>
                  Email
                  <input
                    type="email"
                    value={profileForm.email}
                    onChange={(event) => setProfileForm({ ...profileForm, email: event.target.value })}
                  />
                </label>
                <label>
                  New password
                  <input
                    type="password"
                    value={profileForm.password}
                    onChange={(event) =>
                      setProfileForm({ ...profileForm, password: event.target.value })
                    }
                    placeholder="Leave blank to keep the current password"
                  />
                </label>
                <button className="primary" disabled={loading} type="submit">
                  Save changes
                </button>
              </form>
            </article>

            <article className="panel">
              <p className="eyebrow">Session Snapshot</p>
              <h3>Current account details</h3>
              <div className="detail-stack">
                <div>
                  <span>Name</span>
                  <strong>{user?.name || "Unknown"}</strong>
                </div>
                <div>
                  <span>Email</span>
                  <strong>{user?.email || "Unknown"}</strong>
                </div>
                <div>
                  <span>Access</span>
                  <strong>{subscription?.subscribed ? currentPlanName : "Standard user"}</strong>
                </div>
                <div>
                  <span>Plan status</span>
                  <strong>{currentPlanStatus}</strong>
                </div>
              </div>
            </article>
          </section>
        )}
      </main>
      <audio ref={audioRef} preload="auto" />
      {nowPlaying && (
        <div className="player-bar">
          <div className="player-topline">
            <div className="player-art" aria-hidden="true">
              {getSongTitle(nowPlaying).slice(0, 2).toUpperCase()}
            </div>
            <div className="player-copy">
              <p className="eyebrow">Now Playing</p>
              <strong>{getSongTitle(nowPlaying)}</strong>
              <span>{getSongArtist(nowPlaying)}</span>
            </div>
            <div className={isPlaying ? "sound-bars active" : "sound-bars"} aria-hidden="true">
              <span />
              <span />
              <span />
              <span />
            </div>
          </div>

          <div className="player-progress">
            <span>{formatTime(playbackPosition)}</span>
            <div className="player-progress-track">
              <div className="player-progress-fill" style={{ width: `${progressPercent}%` }} />
              <input
                className="player-progress-range"
                max={currentSongDuration || 0}
                min="0"
                onChange={handleSeek}
                step="0.1"
                type="range"
                value={Math.min(playbackPosition, currentSongDuration || 0)}
              />
            </div>
            <span>-{formatTime(currentSongDuration - playbackPosition)}</span>
          </div>

          <div className="player-controls">
            <button
              className={isShuffle ? "player-toggle active" : "player-toggle"}
              onClick={toggleShuffle}
              type="button"
            >
              Shuffle
            </button>
            <button className="player-icon-button" onClick={() => handleSkip("previous")} type="button">
              &#9198;
            </button>
            <button className="player-icon-button player-icon-button-primary" onClick={handleTogglePlayback} type="button">
              {isPlaying ? "||" : ">"}
            </button>
            <button className="player-icon-button" onClick={() => handleSkip("next")} type="button">
              &#9197;
            </button>
            <button
              className={repeatMode !== "off" ? "player-toggle active" : "player-toggle"}
              onClick={cycleRepeatMode}
              type="button"
            >
              {repeatMode === "one" ? "Repeat 1" : "Repeat"}
            </button>
            <button className="player-close" onClick={handleDismissPlayer} type="button">
              x
            </button>
          </div>

          <div className="player-volume-row">
            <button className="player-toggle" onClick={toggleMute} type="button">
              {isMuted || volume === 0 ? "Muted" : "Volume"}
            </button>
            <input
              className="player-volume-range"
              max="1"
              min="0"
              onChange={handleVolumeChange}
              step="0.01"
              type="range"
              value={isMuted ? 0 : volume}
            />
          </div>

          <div className="player-stats">
            <span>{nowPlaying.total_plays ?? 0} plays</span>
            <span>{nowPlaying.total_likes ?? 0} likes</span>
            <span>{formatTime(currentSongDuration)} total</span>
            <span>{songQueue.length} queued</span>
          </div>
        </div>
      )}
      {checkoutPlan && (
        <div className="checkout-overlay" onClick={closeCheckout} role="presentation">
          <section className="checkout-modal" onClick={(event) => event.stopPropagation()}>
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Demo Checkout</p>
                <h3>{checkoutPlan.name || checkoutPlan.plan_name}</h3>
              </div>
              <button className="history-close-button history-close-button-dark" onClick={closeCheckout} type="button">
                x
              </button>
            </div>
            <p className="muted">
              Confirm this demo payment to activate {checkoutPlan.name || checkoutPlan.plan_name} immediately.
            </p>
            <div className="detail-stack checkout-summary">
              <div>
                <span>Plan price</span>
                <strong>{checkoutPlan.price ? `Rs. ${checkoutPlan.price}` : "Free"}</strong>
              </div>
              <div>
                <span>Payment method</span>
                <strong>{paymentMethod.toUpperCase()}</strong>
              </div>
            </div>
            <form className="stack" onSubmit={handleCheckoutConfirm}>
              <label>
                Account holder
                <input
                  value={paymentForm.payerName}
                  onChange={(event) =>
                    setPaymentForm((current) => ({ ...current, payerName: event.target.value }))
                  }
                  placeholder="Name on payment account"
                />
              </label>
              {paymentMethod === "upi" ? (
                <label>
                  UPI ID
                  <input
                    value={paymentForm.paymentHandle}
                    onChange={(event) =>
                      setPaymentForm((current) => ({ ...current, paymentHandle: event.target.value }))
                    }
                    placeholder="name@bank"
                  />
                </label>
              ) : (
                <>
                  <label>
                    {paymentMethod === "card" ? "Card number" : "Bank reference"}
                    <input
                      value={paymentForm.cardNumber}
                      onChange={(event) =>
                        setPaymentForm((current) => ({ ...current, cardNumber: event.target.value }))
                      }
                      placeholder={paymentMethod === "card" ? "1234 5678 9012 3456" : "Reference number"}
                    />
                  </label>
                  <label>
                    {paymentMethod === "card" ? "Expiry" : "Approval code"}
                    <input
                      value={paymentForm.expiry}
                      onChange={(event) =>
                        setPaymentForm((current) => ({ ...current, expiry: event.target.value }))
                      }
                      placeholder={paymentMethod === "card" ? "MM/YY" : "Optional code"}
                    />
                  </label>
                </>
              )}
              <div className="action-row">
                <button className="ghost" onClick={closeCheckout} type="button">
                  Cancel
                </button>
                <button className="primary" disabled={loading} type="submit">
                  {loading ? "Processing..." : "Confirm payment"}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}

export default App;
