# Lisa Hoy Es Tu Cumple - Video Generator

Small Flask web app that generates a personalized birthday video. It replaces the fixed "Lisa" moments in the song with a custom name, and can optionally overlay an uploaded photo on Lisa's face in the source video.

The original audio and video are not included in this repository. Use your own `song.mp3` and MP4 locally, or configure public media URLs in deployment.

## Features

- Browser UI in Spanish for entering a name and optional photo
- Flask endpoint for MP4 generation
- Google TTS for Spanish name synthesis
- FFmpeg-based audio replacement and video muxing
- FFmpeg-based oval photo overlay using a pre-calibrated face track
- 24-hour share links backed by Cloudflare R2 when configured

## Requirements

- Python 3.8+
- FFmpeg available in `PATH`
- Internet access when generating Google TTS audio

## Windows Quick Start

```bat
setup_venv.bat
run_app.bat
```

Open:

```text
http://localhost:5000
```

For local testing, place these files in the project root:

```text
song.mp3
Lisa hoy es tu cumple - YouTube.mp4
```

Or set `AUDIO_URL` and `VIDEO_URL`.

## Manual Setup

```bat
python -m venv venv
venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python src\app.py
```

## Source Media Configuration

The app chooses the source audio in this order:

1. `AUDIO_PATH`
2. `AUDIO_URL`
3. Local `song.mp3`, `song.wav`, `audio.mp3`, or `audio.wav`
4. A local MP4 that can be extracted with FFmpeg

The app chooses the source video in this order:

1. `VIDEO_PATH`
2. `VIDEO_URL`
3. Local `Lisa hoy es tu cumple - YouTube.mp4`, `song.mp4`, or `video.mp4`

Example Render/R2 values:

```text
AUDIO_URL=https://example.r2.dev/song.mp3
VIDEO_URL=https://example.r2.dev/source-video.mp4
```

The Cloudflare dashboard URL is not a public object URL. Use an R2 public bucket URL, an R2 custom domain URL, or a signed URL that Render can access.

## Docker

The Docker image includes FFmpeg and runs the Flask app with Gunicorn.

```bash
docker build -t lisa-video-generator .
docker run --rm -p 10000:10000 \
  -e AUDIO_URL="https://example.r2.dev/song.mp3" \
  -e VIDEO_URL="https://example.r2.dev/source-video.mp4" \
  lisa-video-generator
```

Then open:

```text
http://localhost:10000
```

## Render Deployment With Cloudflare R2

Render can deploy this repository as a Docker web service and provide a public `onrender.com` URL.

Recommended setup:

1. Put `song.mp3` and the source MP4 in Cloudflare R2.
2. Make both objects available through public URLs or a custom domain.
3. In Render, create a Docker Web Service from this GitHub repository.
4. Add:

   ```text
   AUDIO_URL=<your public R2 song.mp3 URL>
   VIDEO_URL=<your public R2 source MP4 URL>
   ```

5. Deploy.

You do not need a Render persistent disk when `AUDIO_URL` and `VIDEO_URL` are set.

## Share Links With 24-Hour Persistence

If R2 write credentials are configured, generated MP4 files are uploaded to R2 and the app returns a share link like:

```text
https://your-render-service.onrender.com/v/<id>
```

Set these Render environment variables:

```text
R2_BUCKET=lisa
R2_ACCESS_KEY_ID=<your R2 access key>
R2_SECRET_ACCESS_KEY=<your R2 secret key>
R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
SHARE_TTL_HOURS=24
PUBLIC_BASE_URL=https://your-render-service.onrender.com
```

`R2_ACCOUNT_ID` can be used instead of `R2_ENDPOINT_URL`; if both are set, `R2_ENDPOINT_URL` wins.

Generated video files are stored under:

```text
generated/video/
```

The app rejects expired share links after `SHARE_TTL_HOURS`. To physically delete old files from R2, add a Cloudflare R2 lifecycle rule that deletes objects under `generated/` after 1 day.

If R2 write variables are missing, the app still works locally, but it returns the generated MP4 directly and share links are not created.

## Face Track Calibration

Lisa's face positions are predefined in:

```text
src/lisa_face_track.json
```

This file contains manual keyframes in source-video pixels. Runtime generation does not detect faces; it only applies this track.

To inspect the current boxes locally:

```bat
python tools\calibrate_face_track.py
```

The script writes annotated frames to `calibration_clips/video_face_track/`, which is ignored by Git.

## Video Performance

When a photo is uploaded, the app has to re-encode the video to apply the overlay. By default it uses FFmpeg/x264 with the `ultrafast` preset to reduce generation time:

```text
VIDEO_FFMPEG_PRESET=ultrafast
VIDEO_CRF=23
```

`ultrafast` is quicker but creates larger MP4 files. If you prefer smaller files and can accept slower generation, set `VIDEO_FFMPEG_PRESET=veryfast` or `medium`.

## Project Structure

```text
LisaHoyEsTuCumple/
|-- src/
|   |-- app.py
|   |-- audio_processor.py
|   |-- video_processor.py
|   |-- lisa_face_track.json
|   |-- index.html
|   |-- script.js
|   |-- video-share.html
|   |-- video-share.js
|   `-- style.css
|-- tools/
|   `-- calibrate_face_track.py
|-- Dockerfile
|-- run_app.bat
|-- setup_venv.bat
|-- requirements.txt
|-- requirements-render.txt
`-- README.md
```

## Media Files

This repo intentionally ignores generated and source media files:

- `song.mp3`
- `*.mp4`
- `calibration_clips/`
- generated output MP3/WAV/MP4 files

That keeps the GitHub repository lightweight and avoids publishing copyrighted media.

GitHub Pages cannot run this app because generation requires the Flask backend. Use GitHub for source hosting and deploy the backend on a service such as Render.
