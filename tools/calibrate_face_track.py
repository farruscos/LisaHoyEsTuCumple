import argparse
import json
import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VIDEO = PROJECT_ROOT / "Lisa hoy es tu cumple - YouTube.mp4"
DEFAULT_TRACK = PROJECT_ROOT / "src" / "lisa_face_track.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "calibration_clips" / "video_face_track"


def extract_boxed_frame(video_path, time_seconds, box, output_path):
    x = int(round(float(box["x"])))
    y = int(round(float(box["y"])))
    w = int(round(float(box["w"])))
    h = int(round(float(box["h"])))
    filter_expr = f"drawbox=x={x}:y={y}:w={w}:h={h}:color=red@0.9:t=4"
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-ss",
        f"{time_seconds:.3f}",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-vf",
        filter_expr,
        str(output_path),
        "-loglevel",
        "error",
    ]
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(
        description="Extract keyframe images with Lisa face-track boxes for manual calibration."
    )
    parser.add_argument("--video", default=os.environ.get("VIDEO_PATH", str(DEFAULT_VIDEO)))
    parser.add_argument("--track", default=str(DEFAULT_TRACK))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    video_path = Path(args.video)
    track_path = Path(args.track)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    with track_path.open("r", encoding="utf-8") as track_file:
        track = json.load(track_file)

    for segment in track.get("segments", []):
        label = segment.get("label", "segment").replace(" ", "_")
        for keyframe in segment.get("keyframes", []):
            time_seconds = float(keyframe["time"])
            output_path = output_dir / f"{time_seconds:06.2f}_{label}.jpg"
            extract_boxed_frame(video_path, time_seconds, keyframe, output_path)
            print(output_path)


if __name__ == "__main__":
    main()
