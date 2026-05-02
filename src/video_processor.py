import io
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
from fractions import Fraction


DEFAULT_TRACK_FILE = "lisa_face_track.json"


class VideoProcessor:
    def __init__(self, original_video_path=None, track_path=None):
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(self.app_dir)
        configured_video_path = original_video_path or os.environ.get("VIDEO_PATH")
        configured_video_url = os.environ.get("VIDEO_URL")

        if configured_video_path:
            self.original_video_path = self._resolve_video_path(configured_video_path)
        elif configured_video_url:
            self.original_video_path = self._download_video_from_url(configured_video_url)
        else:
            self.original_video_path = self._get_default_video()

        self.track_path = track_path or os.path.join(self.app_dir, DEFAULT_TRACK_FILE)
        self.face_track = self._load_face_track()
        self.ffmpeg_preset = os.environ.get("VIDEO_FFMPEG_PRESET", "ultrafast")
        self.video_crf = os.environ.get("VIDEO_CRF", "23")
        self.video_loaded = False
        self.original_video = None
        self.video_info = None
        self.load_original_video()

    def _resolve_video_path(self, video_path):
        if os.path.isabs(video_path):
            return video_path
        return os.path.join(self.base_dir, video_path)

    def _download_video_from_url(self, video_url):
        cache_path = os.environ.get(
            "VIDEO_CACHE_PATH",
            os.path.join(tempfile.gettempdir(), "lisa_source_video.mp4"),
        )

        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
            size_mb = os.path.getsize(cache_path) / (1024 * 1024)
            print(f"[Info] Using cached source video: {cache_path} ({size_mb:.2f} MB)")
            return cache_path

        print("[Info] Downloading source video from VIDEO_URL...")
        try:
            request = urllib.request.Request(
                video_url,
                headers={"User-Agent": "LisaHoyEsTuCumple/1.0"},
            )
            with urllib.request.urlopen(request, timeout=180) as response:
                status = getattr(response, "status", None)
                if status is not None and status >= 400:
                    raise RuntimeError(f"HTTP {status}")

                with open(cache_path, "wb") as output_file:
                    output_file.write(response.read())

            size_mb = os.path.getsize(cache_path) / (1024 * 1024)
            if size_mb <= 0:
                raise RuntimeError("downloaded video file is empty")

            print(f"[Success] Source video downloaded: {cache_path} ({size_mb:.2f} MB)")
            return cache_path
        except (urllib.error.URLError, OSError, RuntimeError) as exc:
            print(f"[Error] Failed to download VIDEO_URL: {exc}")
            return cache_path

    def _get_default_video(self):
        preferred_video_files = [
            "Lisa hoy es tu cumple - YouTube.mp4",
            "song.mp4",
            "video.mp4",
        ]

        local_mp4_files = [
            filename
            for filename in os.listdir(self.base_dir)
            if filename.lower().endswith(".mp4")
        ]

        for filename in preferred_video_files + local_mp4_files:
            path = os.path.join(self.base_dir, filename)
            if os.path.exists(path):
                return path

        return os.path.join(self.base_dir, preferred_video_files[0])

    def _run(self, cmd, error_message, timeout=600):
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            details = (result.stderr or result.stdout or "Unknown error").strip()
            raise RuntimeError(f"{error_message}: {details}")
        return result

    def _load_face_track(self):
        if not os.path.exists(self.track_path):
            print(f"[Warning] Lisa face track not found at {self.track_path}")
            return {"segments": []}

        with open(self.track_path, "r", encoding="utf-8") as track_file:
            track = json.load(track_file)

        segments = track.get("segments", [])
        for segment in segments:
            segment["keyframes"] = sorted(
                segment.get("keyframes", []),
                key=lambda keyframe: float(keyframe["time"]),
            )

        print(f"[Info] Loaded Lisa face track with {len(segments)} segment(s)")
        return track

    def load_original_video(self):
        try:
            if os.path.exists(self.original_video_path):
                self.video_info = self._probe_video(self.original_video_path)
                size_mb = os.path.getsize(self.original_video_path) / (1024 * 1024)
                print(
                    "[Info] Video file found: "
                    f"{os.path.basename(self.original_video_path)} "
                    f"({size_mb:.2f} MB, {self.video_info['width']}x{self.video_info['height']})"
                )
                self.video_loaded = True
                self.original_video = self.original_video_path
            else:
                print(f"[Warning] Original video file not found at {self.original_video_path}")
                self.video_loaded = False
                self.original_video = None
        except Exception as exc:
            print(f"[Error] Failed to load video: {exc}")
            self.video_loaded = False
            self.original_video = None

    def _probe_video(self, video_path):
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,avg_frame_rate,duration",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            video_path,
        ]
        result = self._run(cmd, f"Failed to inspect video {video_path}", timeout=30)
        payload = json.loads(result.stdout)
        stream = payload["streams"][0]
        fps_fraction = stream.get("avg_frame_rate") or "30/1"
        fps = float(Fraction(fps_fraction))
        duration = float(
            stream.get("duration")
            or payload.get("format", {}).get("duration")
            or 0
        )

        return {
            "width": int(stream["width"]),
            "height": int(stream["height"]),
            "fps_fraction": fps_fraction,
            "fps": fps,
            "duration": duration,
        }

    def _segment_box(self, segment):
        keyframes = segment.get("keyframes", [])
        if not keyframes:
            return None

        width = self.video_info["width"]
        height = self.video_info["height"]
        average = {
            name: sum(float(keyframe[name]) for keyframe in keyframes) / len(keyframes)
            for name in ("x", "y", "w", "h")
        }
        x = max(0, min(int(round(average["x"])), width - 1))
        y = max(0, min(int(round(average["y"])), height - 1))
        w = max(1, min(int(round(average["w"])), width - x))
        h = max(1, min(int(round(average["h"])), height - y))
        return x, y, w, h

    def _linear_expr(self, keyframes, field_name, fallback):
        if len(keyframes) < 2:
            return str(int(round(fallback)))

        first = keyframes[0]
        last = keyframes[-1]
        start = float(first["time"])
        end = float(last["time"])
        start_value = float(first[field_name])
        end_value = float(last[field_name])
        if abs(end - start) < 0.001 or abs(end_value - start_value) < 0.001:
            return str(int(round(start_value)))

        return f"{start_value:.3f}+({end_value - start_value:.3f})*(t-{start:.3f})/{end - start:.3f}"

    def _build_overlay_filter(self):
        segments = [
            segment
            for segment in self.face_track.get("segments", [])
            if segment.get("keyframes") and self._segment_box(segment)
        ]
        if not segments:
            raise RuntimeError("No Lisa face-track segments are configured")

        filter_parts = [
            "[0:v]setpts=PTS-STARTPTS[base]",
            (
                "[1:v]scale=512:512:force_original_aspect_ratio=increase,"
                "crop=512:512,format=rgba,"
                "geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
                "a='if(lte(pow((X-W/2)/(W*0.45),2)+pow((Y-H/2)/(H*0.48),2)\\,1)\\,255\\,0)'"
                "[face]"
            ),
        ]

        split_outputs = "".join(f"[face{i}]" for i in range(len(segments)))
        filter_parts.append(f"[face]split={len(segments)}{split_outputs}")

        current_label = "base"
        for index, segment in enumerate(segments):
            x, y, w, h = self._segment_box(segment)
            start = float(segment["start"])
            end = float(segment["end"])
            keyframes = segment["keyframes"]
            x_expr = self._linear_expr(keyframes, "x", x)
            y_expr = self._linear_expr(keyframes, "y", y)
            scaled_label = f"face{index}s"
            output_label = f"v{index}"
            filter_parts.append(f"[face{index}]scale={w}:{h}[{scaled_label}]")
            filter_parts.append(
                f"[{current_label}][{scaled_label}]"
                f"overlay=x='{x_expr}':y='{y_expr}':enable='between(t,{start:.3f},{end:.3f})'"
                f"[{output_label}]"
            )
            current_label = output_label

        return ";".join(filter_parts), current_label

    def _render_overlay_video(self, photo_path, output_path):
        filter_complex, output_label = self._build_overlay_filter()
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-i",
            self.original_video_path,
            "-loop",
            "1",
            "-i",
            photo_path,
            "-filter_complex",
            filter_complex,
            "-map",
            f"[{output_label}]",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            self.ffmpeg_preset,
            "-crf",
            self.video_crf,
            "-pix_fmt",
            "yuv420p",
            "-t",
            f"{self.video_info['duration']:.3f}",
            output_path,
            "-loglevel",
            "error",
        ]
        self._run(cmd, "Failed to render photo overlay", timeout=900)

    def _mux_video_audio(self, video_path, audio_path, output_path):
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-i",
            video_path,
            "-i",
            audio_path,
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            output_path,
            "-loglevel",
            "error",
        ]
        self._run(cmd, "Failed to combine video and customized audio", timeout=600)

    def generate_custom_video(self, audio_buffer, custom_name, photo_file=None):
        if not self.video_loaded:
            raise RuntimeError("Original video file is not loaded.")

        has_photo = photo_file is not None and getattr(photo_file, "filename", "")
        print(f"[Info] Starting video generation for: {custom_name}; photo={bool(has_photo)}")

        with tempfile.TemporaryDirectory(
            prefix="video_work_",
            dir=self.base_dir,
            ignore_cleanup_errors=True,
        ) as tmpdir:
            audio_path = os.path.join(tmpdir, "custom_audio.mp3")
            audio_buffer.seek(0)
            with open(audio_path, "wb") as audio_file:
                audio_file.write(audio_buffer.read())

            if has_photo:
                photo_path = os.path.join(tmpdir, "uploaded_photo")
                photo_file.save(photo_path)
                visual_video_path = os.path.join(tmpdir, "visual_overlay.mp4")
                self._render_overlay_video(photo_path, visual_video_path)
            else:
                visual_video_path = self.original_video_path

            output_path = os.path.join(tmpdir, "custom_video.mp4")
            self._mux_video_audio(visual_video_path, audio_path, output_path)

            with open(output_path, "rb") as output_file:
                video_data = output_file.read()

        if not video_data:
            raise RuntimeError("Generated video is empty")

        video_buffer = io.BytesIO(video_data)
        video_buffer.seek(0)
        print(f"[Success] Video generated successfully ({len(video_data) / 1024 / 1024:.2f} MB)")
        return video_buffer
