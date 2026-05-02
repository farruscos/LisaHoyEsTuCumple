# Lisa Hoy Es Tu Cumple - Name Replacer

Small Flask web app that generates a personalized version of a local audio file by replacing the hard-coded "Lisa" moments with a name entered by the user.

The original song/audio is not included in this repository. Add your own local `song.mp3` or place a compatible video file in the project folder and run the extraction script.

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
setup_venv_v2.bat
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
python app.py
```

## Audio Files

This repo intentionally ignores generated and source media files:

- `song.mp3`
- `*.mp4`
- `calibration_clips/`
- generated output MP3/WAV files

That keeps the GitHub repository lightweight and avoids publishing copyrighted media.

## Tune Replacement Timings

Replacement windows are defined in `audio_processor.py`:

```python
DEFAULT_REPLACEMENT_REGIONS = [
    (10.20, 10.78),
    ...
]
```

Each pair is `(start_seconds, end_seconds)`.

## Notes

This is a Flask app, so GitHub Pages cannot run the backend. Use GitHub for source hosting; deploy the backend separately if you want a public live app.
