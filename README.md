# TuneBase

TuneBase is a Spotify-inspired music streaming web app built with Flask, MySQL, and React. It includes JWT authentication, song browsing, playlists, likes, play history, recommendations, subscription plans, notifications, queue-based playback, search history, and a dynamic mini player with real or demo audio support.

## Features

- Secure JWT-based authentication
- Song library with likes and play tracking
- Playlist creation and song management
- Search with recent history and quick reuse
- Recommendations and smart in-app notifications
- Queue-based playback with next, previous, shuffle, repeat, seek, volume, and mute
- Subscription plans with demo checkout flow
- Dashboard summary for library, playlists, recommendations, and active plan
- Real local audio file support with demo preview fallback

## Tech Stack

- Backend: Flask, SQLAlchemy, MySQL
- Frontend: React, Vite
- Auth: JWT
- Styling: Custom CSS

## Project Structure

```text
app/                  Flask backend
app/static/audio/     Real song files placed here
frontend/             React frontend
scripts/              Database setup and reseed scripts
app.py                App entry point
config.py             Configuration
requirements.txt      Python dependencies
```

## Setup

1. Create and activate the virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Create your environment file

```powershell
copy .env.example .env
```

3. Update `.env` with:

- `DATABASE_URL` or the DB connection values
- `JWT_SECRET_KEY`

## Run The Project

Backend:

```powershell
cd "C:\Users\SUJAL\OneDrive\Desktop\dbms project"
.\.venv\Scripts\activate
python app.py
```

Frontend:

```powershell
cd "C:\Users\SUJAL\OneDrive\Desktop\dbms project\frontend"
npm install
npm run dev
```

The frontend runs through Vite and talks to the Flask backend on `http://127.0.0.1:5000`.

## Real Audio Support

If you want the player to use real songs instead of generated demo previews, place audio files in:

```text
app/static/audio
```

Name each file using the database `song_id`.

Examples:

- `1.mp3`
- `2.wav`
- `3.ogg`
- `4.m4a`

If a matching file exists, TuneBase plays the real file automatically.
If no matching file exists, it falls back to demo preview audio.

## Build Frontend For Flask

```powershell
cd frontend
npm run build
```

After building, Flask serves the frontend from `/`.

## Demo Highlights

- Add songs to playlists from the Songs page
- Add songs to the queue and let them play next
- Buy plans through the demo checkout modal
- Dismiss notifications and search history items with `x`
- Control playback using the mini player

## Notes

- Models are mapped to an existing MySQL schema
- The app uses real audio only if matching local files are added
- Demo payment and some player behavior are intentionally mocked for presentation purposes

