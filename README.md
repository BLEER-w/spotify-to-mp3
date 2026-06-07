# Spotify to MP3 Web App

A simple website to convert Spotify track URLs into MP3 downloads and fetch lyrics.

## Features

- Accepts Spotify track URLs
- Downloads MP3 using `spotdl`
- Fetches metadata and lyrics from public APIs
- Provides a download link for the generated MP3

## Requirements

- Python 3.11+
- `ffmpeg` installed and available on the PATH
- `pip` to install dependencies

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Optional: create a `.env` file and add a Genius API token for improved lyrics lookup:

```text
GENIUS_ACCESS_TOKEN=your_genius_access_token_here
```

3. Start the app:

```bash
python app.py
```

4. Open the website at `http://localhost:5000`

## Usage

- Paste a Spotify track URL like `https://open.spotify.com/track/XXXXXXXXXX`
- Click **Convert to MP3**
- Wait for the site to process the request
- Download the generated MP3 and view the lyrics

## Notes

- The app uses `spotdl` to perform Spotify track conversion.
- Lyrics are retrieved via the Genius API when a token is configured, or via `lyrics.ovh` as fallback.
- Downloaded files are stored in the `downloads/` folder and are ignored by Git.
