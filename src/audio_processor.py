import io
import os
import platform
import subprocess
import tempfile

from gtts import gTTS


# Timings for the "Lisa" words in the bundled audio.
# They are deliberately data, not hidden logic, so they can be tuned if the
# source audio is replaced by a different cut of the song.
DEFAULT_REPLACEMENT_REGIONS = [
    (10.20, 10.78),
    (22.50, 23.08),
    (26.87, 27.65),
    (28.63, 29.21),
    (32.93, 33.71),
    (46.75, 47.65),
    (51.42, 52.20),
    (53.25, 53.93),
    (57.63, 58.31),
]


class AudioProcessor:
    def __init__(self, original_audio_path=None, replacement_regions=None):
        """
        Initialize the audio processor using FFmpeg directly.

        Args:
            original_audio_path: Path to the original audio file.
            replacement_regions: List of (start_seconds, end_seconds) pairs.
        """
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(self.app_dir)
        configured_audio_path = original_audio_path or os.environ.get("AUDIO_PATH")
        self.original_audio_path = self._resolve_audio_path(configured_audio_path) if configured_audio_path else self._get_default_audio()
        self.replacement_regions = replacement_regions or DEFAULT_REPLACEMENT_REGIONS
        self.audio_loaded = False
        self.original_audio = None
        self.load_original_audio()

    def _resolve_audio_path(self, audio_path):
        """Resolve relative audio paths from the project directory."""
        if os.path.isabs(audio_path):
            return audio_path
        return os.path.join(self.base_dir, audio_path)

    def _get_default_audio(self):
        """Get the default audio file path, extracting it from video if needed."""
        audio_files = ["song.mp3", "song.wav", "audio.mp3", "audio.wav"]
        for filename in audio_files:
            path = os.path.join(self.base_dir, filename)
            if os.path.exists(path):
                return path

        preferred_video_files = ["Lisa hoy es tu cumple - YouTube.mp4", "song.mp4", "audio.mp4"]
        local_mp4_files = [
            filename
            for filename in os.listdir(self.base_dir)
            if filename.lower().endswith(".mp4")
        ]

        for filename in preferred_video_files + local_mp4_files:
            path = os.path.join(self.base_dir, filename)
            if os.path.exists(path):
                print(f"[Info] Found video file: {filename}")
                print("[Info] Attempting to extract audio...")
                if self._extract_audio_from_video(path):
                    return os.path.join(self.base_dir, "song.mp3")

        return os.path.join(self.base_dir, "song.mp3")

    def _run(self, cmd, error_message, timeout=300):
        """Run a subprocess and raise a readable error when it fails."""
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            details = (result.stderr or result.stdout or "Unknown error").strip()
            raise RuntimeError(f"{error_message}: {details}")
        return result

    def _extract_audio_from_video(self, video_path):
        """Extract audio from a video file using FFmpeg."""
        try:
            output_path = os.path.join(self.base_dir, "song.mp3")
            cmd = [
                "ffmpeg",
                "-hide_banner",
                "-y",
                "-i",
                video_path,
                "-vn",
                "-q:a",
                "0",
                "-map",
                "a",
                output_path,
                "-loglevel",
                "error",
            ]

            self._run(cmd, "Failed to extract audio")
            if os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"[Success] Audio extracted: song.mp3 ({size_mb:.2f} MB)")
                return True
            return False
        except FileNotFoundError:
            print("[Error] FFmpeg not found. Please install FFmpeg and try again.")
            return False
        except Exception as exc:
            print(f"[Error] Unexpected error during extraction: {exc}")
            return False

    def load_original_audio(self):
        """Verify the original audio file exists."""
        try:
            if os.path.exists(self.original_audio_path):
                size_mb = os.path.getsize(self.original_audio_path) / (1024 * 1024)
                print(f"[Info] Audio file found: {os.path.basename(self.original_audio_path)} ({size_mb:.2f} MB)")
                self.audio_loaded = True
                self.original_audio = self.original_audio_path
            else:
                print(f"[Warning] Original audio file not found at {self.original_audio_path}")
                self.audio_loaded = False
                self.original_audio = None
        except Exception as exc:
            print(f"[Error] Failed to load audio: {exc}")
            self.audio_loaded = False
            self.original_audio = None

    def _probe_duration(self, audio_path):
        """Return audio duration in seconds."""
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ]
        result = self._run(cmd, f"Failed to read duration for {audio_path}", timeout=30)
        return float(result.stdout.strip())

    def _generate_gtts_audio(self, name, language):
        """Generate text-to-speech audio with Google TTS."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            tts = gTTS(text=name, lang=language, slow=False)
            tts.save(tmp_path)
            return tmp_path
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def _generate_windows_tts_audio(self, name, preferred_culture="es"):
        """Generate a WAV with the Windows speech synthesizer as an offline fallback."""
        if platform.system() != "Windows":
            return None

        fd, output_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        os.unlink(output_path)

        script = """
param([string]$Text, [string]$OutputPath, [string]$PreferredCulture)
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voices = $synth.GetInstalledVoices() | Where-Object { $_.Enabled }
$voice = $voices |
    Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name.StartsWith($PreferredCulture) } |
    Select-Object -First 1
if (-not $voice) {
    $voice = $voices | Select-Object -First 1
}
if ($voice) {
    $synth.SelectVoice($voice.VoiceInfo.Name)
}
$synth.Rate = 0
$synth.Volume = 100
$synth.SetOutputToWaveFile($OutputPath)
$synth.Speak($Text)
$synth.Dispose()
"""

        with tempfile.NamedTemporaryFile(suffix=".ps1", mode="w", encoding="utf-8", delete=False) as script_file:
            script_path = script_file.name
            script_file.write(script)

        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                script_path,
                name,
                output_path,
                preferred_culture,
            ]
            self._run(cmd, "Windows text-to-speech failed", timeout=60)
            if not os.path.exists(output_path) or os.path.getsize(output_path) < 1024:
                raise RuntimeError("Windows text-to-speech created an empty audio file")
            return output_path
        except Exception:
            if os.path.exists(output_path):
                os.unlink(output_path)
            return None
        finally:
            if os.path.exists(script_path):
                os.unlink(script_path)

    def generate_tts_audio(self, name, language="es"):
        """
        Generate text-to-speech audio for the replacement name.

        Google TTS is preferred for Spanish pronunciation. If it cannot connect,
        Windows' built-in speech synthesizer is used so the app still works.
        """
        print(f"[Info] Generating TTS for: {name}")
        try:
            path = self._generate_gtts_audio(name, language)
            size_kb = os.path.getsize(path) / 1024
            print(f"[Info] Google TTS generated: {size_kb:.1f} KB")
            return path
        except Exception as exc:
            print(f"[Warning] Google TTS failed: {exc}")
            print("[Info] Trying offline Windows TTS fallback...")

        fallback_path = self._generate_windows_tts_audio(name, preferred_culture=language)
        if fallback_path:
            size_kb = os.path.getsize(fallback_path) / 1024
            print(f"[Info] Windows TTS generated: {size_kb:.1f} KB")
            return fallback_path

        print("[Error] Failed to generate TTS audio")
        return None

    def _normalise_regions(self, audio_duration):
        """Sort, clamp, and de-overlap replacement windows."""
        cleaned = []
        for start, end in sorted(self.replacement_regions):
            start = max(0.0, min(float(start), audio_duration))
            end = max(0.0, min(float(end), audio_duration))
            if end - start < 0.05:
                continue
            if cleaned and start < cleaned[-1][1]:
                start = cleaned[-1][1]
            if end - start >= 0.05:
                cleaned.append((start, end))
        return cleaned

    def _atempo_filter(self, ratio):
        """Build one or more atempo filters for ratios outside FFmpeg's basic range."""
        factors = []
        ratio = max(ratio, 0.01)
        while ratio > 2.0:
            factors.append(2.0)
            ratio /= 2.0
        while ratio < 0.5:
            factors.append(0.5)
            ratio /= 0.5
        factors.append(ratio)
        return ",".join(f"atempo={factor:.6f}" for factor in factors)

    def _make_original_segment(self, start, end, output_path):
        """Extract a section of the original audio as normalized WAV."""
        duration = max(0.0, end - start)
        if duration < 0.02:
            return False

        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-i",
            self.original_audio_path,
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{duration:.3f}",
            "-vn",
            "-ac",
            "2",
            "-ar",
            "44100",
            "-c:a",
            "pcm_s16le",
            output_path,
            "-loglevel",
            "error",
        ]
        self._run(cmd, "Failed to extract original segment")
        return True

    def _make_name_segment(self, tts_path, target_duration, output_path):
        """Create a replacement name clip that exactly fits a target duration."""
        tts_duration = self._probe_duration(tts_path)
        tempo = tts_duration / target_duration
        fade_duration = min(0.03, target_duration / 4)
        fade_out_start = max(0.0, target_duration - fade_duration)

        filters = [
            self._atempo_filter(tempo),
            "apad",
            f"atrim=0:{target_duration:.6f}",
            "asetpts=PTS-STARTPTS",
            "volume=1.35",
        ]

        if fade_duration > 0:
            filters.extend(
                [
                    f"afade=t=in:st=0:d={fade_duration:.6f}",
                    f"afade=t=out:st={fade_out_start:.6f}:d={fade_duration:.6f}",
                ]
            )

        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-i",
            tts_path,
            "-vn",
            "-af",
            ",".join(filters),
            "-ac",
            "2",
            "-ar",
            "44100",
            "-c:a",
            "pcm_s16le",
            output_path,
            "-loglevel",
            "error",
        ]
        self._run(cmd, "Failed to prepare replacement name segment")

    def _concat_segments(self, segment_paths, output_path):
        """Concatenate normalized WAV segments and encode the final MP3."""
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", encoding="utf-8", delete=False) as list_file:
            concat_path = list_file.name
            for path in segment_paths:
                ffmpeg_path = os.path.abspath(path).replace("\\", "/")
                list_file.write(f"file '{ffmpeg_path}'\n")

        try:
            cmd = [
                "ffmpeg",
                "-hide_banner",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                concat_path,
                "-c:a",
                "libmp3lame",
                "-b:a",
                "192k",
                output_path,
                "-loglevel",
                "error",
            ]
            self._run(cmd, "Failed to concatenate generated audio")
        finally:
            if os.path.exists(concat_path):
                os.unlink(concat_path)

    def generate_custom_audio(self, custom_name):
        """
        Generate audio with the configured "Lisa" regions replaced by custom_name.

        Returns:
            BytesIO object containing MP3 audio.
        """
        tts_path = None
        try:
            if not self.audio_loaded:
                raise RuntimeError("Original audio file is not loaded.")

            print(f"\n[Info] Starting audio generation for: {custom_name}")
            tts_path = self.generate_tts_audio(custom_name, language="es")
            if tts_path is None:
                raise RuntimeError("Failed to generate text-to-speech audio")

            audio_duration = self._probe_duration(self.original_audio_path)
            regions = self._normalise_regions(audio_duration)
            if not regions:
                raise RuntimeError("No valid replacement regions configured")

            print(f"[Info] Replacing {len(regions)} Lisa region(s)")

            with tempfile.TemporaryDirectory(prefix="audio_work_", dir=self.base_dir, ignore_cleanup_errors=True) as tmpdir:
                segment_paths = []
                cursor = 0.0

                for index, (start, end) in enumerate(regions):
                    original_path = os.path.join(tmpdir, f"original_{index:02d}.wav")
                    if self._make_original_segment(cursor, start, original_path):
                        segment_paths.append(original_path)

                    name_path = os.path.join(tmpdir, f"name_{index:02d}.wav")
                    self._make_name_segment(tts_path, end - start, name_path)
                    segment_paths.append(name_path)

                    cursor = end

                tail_path = os.path.join(tmpdir, "tail.wav")
                if self._make_original_segment(cursor, audio_duration, tail_path):
                    segment_paths.append(tail_path)

                output_path = os.path.join(tmpdir, "customized.mp3")
                self._concat_segments(segment_paths, output_path)

                with open(output_path, "rb") as output_file:
                    audio_data = output_file.read()

            audio_buffer = io.BytesIO(audio_data)
            audio_buffer.seek(0)

            print(f"[Success] Audio generated successfully ({len(audio_data) / 1024 / 1024:.2f} MB)")
            return audio_buffer

        except Exception as exc:
            print(f"[Error] Failed to generate custom audio: {exc}")
            raise
        finally:
            if tts_path and os.path.exists(tts_path):
                os.unlink(tts_path)


def demo():
    """Generate a local sample for manual checking."""
    processor = AudioProcessor()
    audio_buffer = processor.generate_custom_audio("Maria")

    with open("output_demo.mp3", "wb") as output_file:
        output_file.write(audio_buffer.getvalue())

    print("Audio generated successfully: output_demo.mp3")


if __name__ == "__main__":
    demo()
