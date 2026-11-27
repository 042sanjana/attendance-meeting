import os
import shutil
import subprocess
import tempfile
import re

from faster_whisper import WhisperModel

_model = None


# Text patterns that Whisper commonly invents for silence or background noise.
_HALLUCINATION_PATTERNS = (
    re.compile(r"(?i)^\s*(you\s+)?thank(s)?\s+(for|you)\b.*$"),
    re.compile(r"(?i)^\s*(thanks?\s+for\s+watching|please\s+subscribe|like\s+and\s+subscribe)\b.*$"),
    re.compile(r"(?i)^\s*(the\s+end|bye\s*!?|yeah\.?|um+\.?|uh+\.?)\s*$"),
    re.compile(r"(?i)^\s*(?:\[|\()[^\]\)]*(?:music|noise|applause|laughter)[^\]\)]*(?:\]|\))\s*$"),
)


def get_whisper_model():
    global _model
    if _model is None:
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def _prepare_audio(audio_path: str) -> tuple[str, str | None]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return audio_path, None

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    wav_path = handle.name
    handle.close()

    try:
        subprocess.run(
            [
                ffmpeg,
                "-v", "error",
                "-y",
                "-i", audio_path,
                "-ac", "1",
                "-ar", "16000",
                "-af", "highpass=f=80,lowpass=f=8000,afftdn=nf=-25",
                wav_path,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=600,
        )
        return wav_path, wav_path
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        if os.path.exists(wav_path):
            os.unlink(wav_path)
        return audio_path, None


def _is_hallucinated(text: str, segment) -> bool:
    cleaned = text.strip()
    if not cleaned:
        return True

    # Low-confidence and almost-silent segments are more likely to be noise hallucinations.
    avg_logprob = getattr(segment, "avg_logprob", 0.0)
    no_speech_prob = getattr(segment, "no_speech_prob", 0.0)
    if avg_logprob < -1.0 or no_speech_prob > 0.60:
        return True

    if any(pattern.match(cleaned) for pattern in _HALLUCINATION_PATTERNS):
        return True

    words = re.findall(r"\b[\w']+\b", cleaned.lower())
    if len(words) >= 3:
        unique_words = set(words)
        if len(unique_words) == 1:
            return True

    return False


def transcribe_audio(audio_path):
    prepared_path, cleanup_path = _prepare_audio(audio_path)
    try:
        segments, info = get_whisper_model().transcribe(
            prepared_path,
            beam_size=5,
            best_of=5,
            temperature=0,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters={
                "min_speech_duration_ms": 250,
                "min_silence_duration_ms": 500,
                "speech_pad_ms": 400,
            },
            no_speech_threshold=0.60,
            log_prob_threshold=-1.0,
            compression_ratio_threshold=2.4,
            word_timestamps=False,
        )

        transcript_parts = []
        timestamped_segments = []
        previous_text = None

        for segment in segments:
            text = segment.text.strip()
            if _is_hallucinated(text, segment):
                continue

            normalized = re.sub(r"\s+", " ", text).strip()
            if normalized and normalized.lower() != (previous_text or "").lower():
                transcript_parts.append(normalized)
                timestamped_segments.append({
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "text": normalized,
                })
                previous_text = normalized.lower()

        transcript = " ".join(transcript_parts).strip()
        if not transcript:
            raise ValueError("The recording contained no detectable speech or only silence.")

        return {
            "transcript": transcript,
            "language": getattr(info, "language", "unknown"),
            "duration": getattr(info, "duration", 0),
            "segments": timestamped_segments,
        }
    finally:
        if cleanup_path and os.path.exists(cleanup_path):
            os.unlink(cleanup_path)