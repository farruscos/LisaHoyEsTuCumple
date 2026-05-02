# Lisa Hoy Es Tu Cumple - Name Replacer

Small Flask web app that generates a personalized birthday audio by replacing fixed "Lisa" moments with a name entered by the user.

The original song/audio is not included in this repository. Add your own local `song.mp3`, set `AUDIO_PATH`, or place a compatible video file in the project folder and run the extraction script.

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

## Docker

The Docker image includes FFmpeg and runs the Flask app with Gunicorn.

```bash
docker build -t lisa-name-replacer .
docker run --rm -p 10000:10000 -v "%cd%/song.mp3:/var/data/song.mp3" lisa-name-replacer
```

Then open:

```text
http://localhost:10000
```

## Render Deployment

Render can deploy this repository as a Docker web service and provide a public `onrender.com` URL.

Recommended setup:

1. Create a Render **Web Service** from this GitHub repository.
2. Select **Docker** as the runtime.
3. Add a persistent disk.
4. Mount the disk at:

   ```text
   /var/data
   ```

5. Upload your local audio file to the disk as:

   ```text
   /var/data/song.mp3
   ```

6. Set this environment variable:

   ```text
   AUDIO_PATH=/var/data/song.mp3
   ```

The Dockerfile already sets `AUDIO_PATH=/var/data/song.mp3` by default, but defining it explicitly in Render makes the deployment intent clear.

Do not upload copyrighted audio to GitHub. Keep the source audio on Render's disk or use audio that you have permission to publish.

## Project Structure

```text
LisaHoyEsTuCumple/
├── src/
│   ├── app.py
│   ├── audio_processor.py
│   ├── index.html
│   ├── script.js
│   └── style.css
├── Dockerfile
├── extract_audio.py
├── run_app.bat
├── setup_venv.bat
├── requirements.txt
└── README.md
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
