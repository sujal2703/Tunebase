from __future__ import annotations

import uuid

from app import create_app


def assert_ok(response, label: str) -> dict:
    payload = response.get_json()
    if response.status_code >= 400:
        raise AssertionError(f"{label} failed with {response.status_code}: {payload}")
    if payload and payload.get("ok") is False:
        raise AssertionError(f"{label} returned ok=false: {payload}")
    return payload or {}


def main() -> None:
    app = create_app()
    client = app.test_client()

    unique_email = f"smoke-{uuid.uuid4().hex[:8]}@example.com"
    password = "Password123!"

    register_payload = {
        "name": "Smoke User",
        "email": unique_email,
        "password": password,
    }
    register_response = client.post("/auth/register", json=register_payload)
    register_data = assert_ok(register_response, "register")

    login_response = client.post(
        "/auth/login",
        json={
            "email": unique_email,
            "password": password,
            "device_identifier": "smoke-suite",
        },
    )
    login_data = assert_ok(login_response, "login")
    token = login_data["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    profile_response = client.get("/users/me", headers=headers)
    profile_data = assert_ok(profile_response, "profile")
    if profile_data["data"]["email"] != unique_email:
        raise AssertionError(f"profile email mismatch: {profile_data}")

    playlist_response = client.post(
        "/playlists",
        headers=headers,
        json={"name": "Smoke Playlist"},
    )
    playlist_data = assert_ok(playlist_response, "create playlist")
    if playlist_data["data"].get("name") != "Smoke Playlist":
        raise AssertionError(f"playlist payload mismatch: {playlist_data}")

    checks = [
        ("/songs?page=1&per_page=3", "songs"),
        ("/playlists?page=1&per_page=3", "playlists"),
        ("/plans?page=1&per_page=3", "plans"),
        ("/recommendations?page=1&per_page=3", "recommendations"),
        ("/notifications?page=1&per_page=3", "notifications"),
    ]

    for path, label in checks:
        assert_ok(client.get(path, headers=headers), label)

    print("Smoke test passed.")
    print(f"Registered user: {unique_email}")


if __name__ == "__main__":
    main()
