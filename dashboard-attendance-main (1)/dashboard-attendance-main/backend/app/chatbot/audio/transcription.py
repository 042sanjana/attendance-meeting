import os
import shutil
import subprocess
import tempfile

from faster_whisper import WhisperModel


_model = None


def get_whisper_model():
    global _model

    if _model is None:
        _model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8",
        )

    return _model


def _prepare_whisper_audio(file_path: str) -> tuple[str, str | None]:
    extension = os.path.splitext(file_path)[1].lower()
    if extension == ".wav":
        return file_path, None

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return file_path, None

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    wav_path = handle.name
    handle.close()

    try:
        subprocess.run(
            [ffmpeg, "-v", "error", "-y", "-i", file_path, "-ac", "1", "-ar", "16000", wav_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=600,
        )
        return wav_path, wav_path
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        if os.path.exists(wav_path):
            os.unlink(wav_path)
        return file_path, None


def transcribe_wav(file_path: str) -> dict:
    prepared_path, cleanup_path = _prepare_whisper_audio(file_path)
    try:
        model = get_whisper_model()

        segments, info = model.transcribe(
            prepared_path,
            beam_size=3,
            vad_filter=True,
        )

        transcript_parts = []
        timestamped_segments = []

        for segment in segments:
            text = segment.text.strip()

            if not text:
                continue

            transcript_parts.append(text)

            timestamped_segments.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": text,
            })

        return {
            "language": info.language,
            "duration": info.duration,
            "transcript": " ".join(transcript_parts),
            "segments": timestamped_segments,
        }
    finally:
        if cleanup_path and os.path.exists(cleanup_path):
            os.unlink(cleanup_path)
