
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


def transcribe_wav(file_path: str) -> dict:
    model = get_whisper_model()

    segments, info = model.transcribe(
        file_path,
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
