const TOKEN_KEY = "pulse_token";
const USER_KEY = "pulse_user";

export function getStoredToken() {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function persistSession(token, user) {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user ?? null));
}

export function clearSession() {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

async function request(path, options = {}) {
  const token = getStoredToken();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers ?? {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(path, {
    ...options,
    headers,
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok || payload?.ok === false) {
    const message = payload?.message || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return payload;
}

export async function login(credentials) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export async function registerAccount(payload) {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchProfile() {
  return request("/users/me");
}

export async function updateProfile(payload) {
  return request("/users/me", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function fetchSongs() {
  return request("/songs?page=1&per_page=12");
}

export async function likeSong(songId) {
  return request(`/songs/${songId}/like`, { method: "POST" });
}

export async function playSong(songId) {
  return request(`/songs/${songId}/play`, { method: "POST" });
}

export async function fetchPlaylists() {
  return request("/playlists?page=1&per_page=10");
}

export async function createPlaylist(payload) {
  return request("/playlists", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function addSongToPlaylist(playlistId, songId) {
  return request(`/playlists/${playlistId}/songs`, {
    method: "POST",
    body: JSON.stringify({ song_id: songId }),
  });
}

export async function fetchPlans() {
  return request("/plans?page=1&per_page=10");
}

export async function subscribeToPlan(payload) {
  return request("/subscriptions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchSubscriptionStatus() {
  return request("/subscriptions/status");
}

export async function fetchRecommendations() {
  return request("/recommendations?page=1&per_page=8");
}

export async function fetchNotifications() {
  return request("/notifications?page=1&per_page=8");
}

export async function performSearch(query) {
  return request("/search?page=1&per_page=8", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}

export async function fetchSearchHistory() {
  return request("/search/history?page=1&per_page=8");
}

export async function clearSearchHistory() {
  return request("/search/history", {
    method: "DELETE",
  });
}

export async function deleteSearchHistoryItem(searchId) {
  return request(`/search/history/${searchId}`, {
    method: "DELETE",
  });
}
