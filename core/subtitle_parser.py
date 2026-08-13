import re
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
from utils.i18n import t

class SubFormat(Enum):
    SMI = "smi"
    SRT = "srt"
    ASS = "ass"
    SSA = "ssa"
    VTT = "vtt"
    SUP = "sup"

DIRECT_MUX_FORMATS = {SubFormat.SRT, SubFormat.ASS, SubFormat.SSA, SubFormat.SUP}
CONVERT_FORMATS = {SubFormat.SMI, SubFormat.VTT}

SUB_EXTENSIONS: dict[str, SubFormat] = {
    ".smi": SubFormat.SMI,
    ".srt": SubFormat.SRT,
    ".ass": SubFormat.ASS,
    ".ssa": SubFormat.SSA,
    ".vtt": SubFormat.VTT,
    ".sup": SubFormat.SUP
}

VIDEO_EXTENSIONS = {".mkv", ".mp4", ".webm"}

@dataclass
class SubtitleEntry:
    start_ms: int
    end_ms: int
    text: str

def detect_format(filepath: Path) -> SubFormat:
    ext = filepath.suffix.lower()
    fmt = SUB_EXTENSIONS.get(ext)
    if fmt is None:
        raise ValueError(t("sub.unsupported_format", ext=ext))
    return fmt

def needs_conversion(fmt: SubFormat) -> bool:
    return fmt in CONVERT_FORMATS

def parse_smi(content: str) -> list[SubtitleEntry]:
    pattern = re.compile(
        r'<SYNC\s+Start\s*=\s*(\d+)\s*>\s*<P[^>]*>\s*(.*?)\s*(?=<SYNC|</BODY>|$)',
        re.IGNORECASE | re.DOTALL,
    )
    raw: list[tuple[int, str]] = []
    for m in pattern.finditer(content):
        ts = int(m.group(1))
        text = m.group(2).strip()
        text = re.sub(r'&nbsp;', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<(?!/?font\b)[^>]+>', '', text, flags=re.IGNORECASE)
        raw.append((ts, text))
    entries: list[SubtitleEntry] = []
    for i, (start, text) in enumerate(raw):
        if not re.sub(r'<[^>]+>', '', text).strip():
            continue
        end = raw[i + 1][0] if i + 1 < len(raw) else start + 3000
        entries.append(SubtitleEntry(start_ms=start, end_ms=end, text=text.strip()))
    return entries

_VTT_TS = r'(?:\d{1,2}:)?\d{2}:\d{2}\.\d{3}'

def _vtt_ts_to_ms(ts: str) -> int:
    parts = ts.strip().split(":")
    if len(parts) == 3:
        h, m, rest = parts
    else:
        h = "0"
        m, rest = parts
    s, ms = rest.split(".")
    return int(h) * 3_600_000 + int(m) * 60_000 + int(s) * 1_000 + int(ms)

def parse_vtt(content: str) -> list[SubtitleEntry]:
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    content = re.sub(r'^WEBVTT.*?\n\n', '', content, count=1, flags=re.DOTALL)
    content = re.sub(
        r'^(?:NOTE|STYLE|REGION)\b[^\n]*(?:\n(?!\n)[^\n]*)*\n?',
        '',
        content,
        flags=re.MULTILINE
    )
    pattern = re.compile(
        rf'({_VTT_TS})\s*-->\s*({_VTT_TS})[^\n]*\n(.*?)(?=\n\n|$)',
        re.DOTALL
    )
    entries: list[SubtitleEntry] = []
    for m in pattern.finditer(content):
        start = _vtt_ts_to_ms(m.group(1))
        end = _vtt_ts_to_ms(m.group(2))
        text = re.sub(r'<[^>]+>', '', m.group(3)).strip()
        if text:
            entries.append(SubtitleEntry(start_ms=start, end_ms=end, text=text))
    return entries

def parse_subtitle(content: str, fmt: SubFormat) -> list[SubtitleEntry]:
    if fmt == SubFormat.SMI:
        return parse_smi(content)
    elif fmt == SubFormat.VTT:
        return parse_vtt(content)
    else:
        raise ValueError(t("sub.no_parse_needed", fmt=fmt.value.upper()))