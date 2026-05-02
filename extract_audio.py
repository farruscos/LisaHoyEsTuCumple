import os
import subprocess
import sys


def find_video_file():
    """Find a local MP4 file to use as the source video."""
    preferred = [
        "Lisa hoy es tu cumple - YouTube.mp4",
        "song.mp4",
        "audio.mp4",
    ]

    for filename in preferred:
        if os.path.exists(filename):
            return filename

    mp4_files = sorted(
        filename
        for filename in os.listdir(".")
        if filename.lower().endswith(".mp4")
    )

    return mp4_files[0] if mp4_files else None


def extract_audio():
    """Extract audio from a local MP4 video file to song.mp3."""
    print("\n" + "=" * 50)
    print("Audio Extraction Utility")
    print("=" * 50 + "\n")

    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("[OK] FFmpeg found\n")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("[ERROR] FFmpeg is not installed or not in PATH")
        print("\nInstall FFmpeg:")
        print("  Windows: choco install ffmpeg")
        print("  macOS:   brew install ffmpeg")
        print("  Linux:   sudo apt-get install ffmpeg")
        print("\nDownload: https://ffmpeg.org/download.html\n")
        return False

    video_file = find_video_file()

    if not video_file:
        print("[ERROR] No MP4 video file found")
        print("Place a .mp4 file in this directory or add song.mp3 directly.\n")
        return False

    output_file = "song.mp3"

    print(f"Found: {video_file}")
    print(f"Extracting audio to: {output_file}\n")

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-i",
        video_file,
        "-vn",
        "-q:a",
        "0",
        "-map",
        "a",
        output_file,
    ]

    print("Running: " + " ".join(cmd) + "\n")
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print("\n[ERROR] Failed to extract audio")
        return False

    if not os.path.exists(output_file):
        print("\n[ERROR] Output file was not created")
        return False

    size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"\n[OK] Audio extracted to {output_file}")
    print(f"File size: {size_mb:.2f} MB\n")
    return True


if __name__ == "__main__":
    sys.exit(0 if extract_audio() else 1)
