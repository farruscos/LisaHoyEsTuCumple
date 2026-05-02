# Lisa Hoy Es Tu Cumple - Name Replacer

Small Flask web app that generates a personalized birthday audio by replacing fixed "Lisa" moments with a name entered by the user.

The original song/audio is not included in this repository. Add your own local `song.mp3`, set `AUDIO_PATH`, set `AUDIO_URL`, or place a compatible video file in the project folder and run the extraction script.

## Features

- Browser UI for entering a custom name
- Flask backend endpoint for audio generation
- Google TTS for Spanish name synthesis
- FFmpeg-based audio cutting and assembly
- Hard-coded replacement timestamps tuned for the fixed source audio
- Downloadable generated MP3

## Requirements

- Python 3.8+
- FFmpeg available in `PATH`
- Internet access when generating Google TTS audio

## Windows Quick Start

```bat
setup_venv.bat
```

Add `song.mp3` to the project root, or extract it from a local video:

```bat
python extract_audio.py
```

Run the app:

```bat
run_app.bat
```

Open:

```text
http://localhost:5000
```

## Manual Setup

```bat
python -m venv venv
venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python src\app.py
```

## Audio Source Configuration

The app chooses the source audio in this order:

1. `AUDIO_PATH`: local file path, for example `/var/data/song.mp3`.
2. `AUDIO_URL`: public URL to an MP3 file. The app downloads and caches it at startup.
3. Local `song.mp3`, `song.wav`, `audio.mp3`, or `audio.wav` in the project root.
4. A local MP4 video that can be extracted with FFmpeg.

Example:

```text
AUDIO_URL=https://example.r2.dev/song.mp3
```

The Cloudflare dashboard URL is not a public object URL. Use an R2 public bucket URL, an R2 custom domain URL, or a signed URL that Render can access.

## Docker

The Docker image includes FFmpeg and runs the Flask app with Gunicorn.

```bash
docker build -t lisa-name-replacer .
docker run --rm -p 10000:10000 -e AUDIO_URL="https://example.r2.dev/song.mp3" lisa-name-replacer
```

Then open:

```text
http://localhost:10000
```

## Render Deployment With Cloudflare R2

Render can deploy this repository as a Docker web service and provide a public `onrender.com` URL.

Recommended setup with R2 as the source audio:

1. In Cloudflare R2, make the object available through either:
   - a public development `r2.dev` URL, or
   - a custom domain connected to the bucket.
2. Copy the real public object URL for `song.mp3`.
3. In Render, create a **Web Service** from this GitHub repository.
4. Select **Docker** as the runtime.
5. Add this environment variable:

   ```text
   AUDIO_URL=<your public R2 song.mp3 URL>
   ```

6. Deploy.

You do not need a Render persistent disk if `AUDIO_URL` is set.

## Share Links With 24-Hour Persistence

If R2 write credentials are configured, generated MP3 files are uploaded to R2 and the app returns a share link like:

```text
https://your-render-service.onrender.com/s/<id>
```

Set these Render environment variables:

```text
R2_BUCKET=lisa
R2_ACCESS_KEY_ID=<your R2 access key>
R2_SECRET_ACCESS_KEY=<your R2 secret key>
R2_ACCOUNT_ID=<your Cloudflare account id>
SHARE_TTL_HOURS=24
PUBLIC_BASE_URL=https://your-render-service.onrender.com
```

Alternatively, use `R2_ENDPOINT_URL` instead of `R2_ACCOUNT_ID`:

```text
R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
```

Generated files are stored under this R2 prefix:

```text
generated/
```

The app rejects expired share links after `SHARE_TTL_HOURS`. To physically delete old MP3 files from R2, add a Cloudflare R2 lifecycle rule that deletes objects under `generated/` after 1 day.

If these R2 write variables are missing, the app still works, but it returns the generated MP3 directly and share links are not created.

Do not upload copyrighted audio to GitHub. Keep the source audio outside the repo and only use audio you have permission to publish or serve.

## Project Structure

```text
LisaHoyEsTuCumple/
|-- src/
|   |-- app.py
|   |-- audio_processor.py
|   |-- index.html
|   |-- script.js
|   `-- style.css
|-- Dockerfile
|-- extract_audio.py
|-- run_app.bat
|-- setup_venv.bat
|-- requirements.txt
|-- requirements-render.txt
`-- README.md
```

## Audio Files

This repo intentionally ignores generated and source media files:

- `song.mp3`
- `*.mp4`
- `calibration_clips/`
- generated output MP3/WAV files

That keeps the GitHub repository lightweight and avoids publishing copyrighted media.

## Tune Replacement Timings

Replacement windows are defined in `src/audio_processor.py`:

```python
DEFAULT_REPLACEMENT_REGIONS = [
    (10.20, 10.78),
    ...
]
```

Each pair is `(start_seconds, end_seconds)`.

## Notes

GitHub Pages cannot run this app because audio generation requires the Flask backend. Use GitHub for source hosting and deploy the backend on a service such as Render.
