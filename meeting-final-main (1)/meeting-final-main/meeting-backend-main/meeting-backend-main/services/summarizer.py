import re


_summarizer = None


def _get_summarizer():
    global _summarizer
    if _summarizer is not None:
        return _summarizer

    try:
        from transformers import pipeline

        _summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    except Exception:
        _summarizer = False
    return _summarizer if _summarizer is not False else None


def _fallback_summary(text: str) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return ""

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    if len(sentences) <= 3:
        return text

    scored = []
    for index, sentence in enumerate(sentences):
        words = set(re.findall(r"[a-z0-9]+", sentence.lower()))
        score = len(words) - max(0, index - 3) * 0.05
        scored.append((score, index, sentence))

    selected = sorted(scored, reverse=True)[:3]
    selected = sorted(selected, key=lambda item: item[1])
    return " ".join(item[2] for item in selected)


def generate_summary(text: str) -> str:
    text = (text or "").strip()
    if len(text.split()) < 30:
        return text

    summarizer = _get_summarizer()
    if summarizer is None:
        return _fallback_summary(text)

    try:
        result = summarizer(text, max_length=120, min_length=30, do_sample=False)
        return result[0]["summary_text"]
    except Exception:
        return _fallback_summary(text)