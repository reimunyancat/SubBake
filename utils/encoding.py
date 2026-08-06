import chardet
from pathlib import Path

_CONFIDENCE_THRESHOLD = 0.7

def read_with_detected_encoding(filepath: Path, fallback: str = "cp949") -> str:
    raw = filepath.read_bytes()
    detected = chardet.detect(raw)
    encoding = detected.get("encoding")
    confidence = detected.get("confidence") or 0.0
    if raw.startswith(b"\xef\xbb\xbf"):
        encoding = "utf-8-sig"
    elif raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        encoding = "utf-16"
    elif not encoding or confidence < _CONFIDENCE_THRESHOLD:
        encoding = fallback
    try:
        return raw.decode(encoding)
    except (UnicodeDecodeError, LookupError):
        return raw.decode(fallback, errors="replace")