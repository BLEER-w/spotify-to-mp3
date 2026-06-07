import os
import re
import uuid
import glob
import subprocess
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, url_for

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

GENIUS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN", "")
SPOTDL_CMD = os.getenv("SPOTDL_PATH", "spotdl")

SPOTIFY_OEMBED = "https://open.spotify.com/oembed"
LYRICS_OVH_URL = "https://api.lyrics.ovh/v1"


def normalize_spotify_url(url: str) -> str:
    artwork = url.strip()
    if artwork.startswith("spotify:"):
        artwork = artwork.replace("spotify:", "https://open.spotify.com/")
    return artwork


def fetch_spotify_metadata(spotify_url: str) -> dict:
    try:
        response = requests.get(SPOTIFY_OEMBED, params={"url": spotify_url}, timeout=10)
        response.raise_for_status()
        data = response.json()
        title = data.get("title", "")
        author = data.get("author_name", "")
        artist = author
        track = title
        return {"artist": artist, "track": track}
    except Exception:
        return {"artist": "Unknown Artist", "track": "Unknown Track"}


def sanitize_filename(value: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9 \-_.()]+", "", value)
    safe = re.sub(r"\s+", " ", safe).strip()
    return safe or "spotify_track"


def find_downloaded_file(prefix: str) -> str | None:
    pattern = str(DOWNLOAD_DIR / f"{prefix}.*")
    matches = glob.glob(pattern)
    return matches[0] if matches else None


def get_lyrics(artist: str, track: str) -> str:
    if artist and track:
        if GENIUS_TOKEN:
            search_url = "https://api.genius.com/search"
            headers = {"Authorization": f"Bearer {GENIUS_TOKEN}"}
            query = f"{artist} {track}"
            try:
                response = requests.get(search_url, headers=headers, params={"q": query}, timeout=10)
                response.raise_for_status()
                hits = response.json().get("response", {}).get("hits", [])
                if hits:
                    path = hits[0]["result"]["path"]
                    page = requests.get(f"https://genius.com{path}", timeout=10)
                    page.raise_for_status()
                    match = re.search(r'<div class="lyrics">(.*?)</div>', page.text, re.S)
                    if not match:
                        match = re.search(r'<div data-lyrics-container="true">(.*?)</div>', page.text, re.S)
                    if match:
                        lyrics_html = match.group(1)
                        lyrics = re.sub(r"<br\s*/?>", "\n", lyrics_html)
                        lyrics = re.sub(r"<.*?>", "", lyrics).strip()
                        return lyrics or "Lyrics not found."
            except Exception:
                pass

        try:
            api_url = f"{LYRICS_OVH_URL}/{requests.utils.quote(artist)}/{requests.utils.quote(track)}"
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                return response.json().get("lyrics", "Lyrics not found.")
        except Exception:
            pass

    return "Lyrics not found."


def download_spotify_track(spotify_url: str, destination: Path) -> tuple[str, str]:
    download_id = uuid.uuid4().hex
    output_template = destination / f"{download_id}.%(ext)s"
    command = [SPOTDL_CMD, spotify_url, "--output", str(output_template)]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
        timeout=420,
    )

    if completed.returncode != 0:
        raise RuntimeError(
            f"Failed to download track: {completed.stderr.strip() or completed.stdout.strip()}"
        )

    file_path = find_downloaded_file(download_id)
    if not file_path:
        raise FileNotFoundError("Downloaded MP3 file could not be located.")

    file_name = Path(file_path).name
    return file_name, file_path


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/convert", methods=["POST"])
def convert():
    data = request.json or {}
    spotify_url = normalize_spotify_url(data.get("spotify_url", ""))

    if not spotify_url:
        return jsonify({"error": "Spotify track URL is required."}), 400

    metadata = fetch_spotify_metadata(spotify_url)
    artist = metadata.get("artist", "Unknown Artist")
    track = metadata.get("track", "Unknown Track")

    try:
        file_name, _ = download_spotify_track(spotify_url, DOWNLOAD_DIR)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    lyrics = get_lyrics(artist, track)
    return jsonify(
        {
            "artist": artist,
            "track": track,
            "lyrics": lyrics,
            "download_url": url_for("download", filename=file_name),
        }
    )


@app.route("/downloads/<path:filename>")
def download(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
