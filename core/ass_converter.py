import re
from core.subtitle_parser import SubtitleEntry

_NAMED_COLORS = {
    "white": "FFFFFF", "black": "000000", "red": "FF0000", "lime": "00FF00", "green": "008000", "blue": "0000FF", "yellow": "FFFF00",
    "aqua": "00FFFF", "cyan": "00FFFF", "fuchsia": "FF00FF", "magenta": "FF00FF", "orange": "FFA500", "gray": "808080", "grey": "808080"
}

_FONT_COLOR_RE = re.compile(
    r'<font\s+[^>]*color\s*=\s*["\']?([^"\'>\s]+)["\']?[^>]*>',
    re.IGNORECASE
)

_HEADER = """[Script Info]
Title: SubBake subtitle
ScriptType: v4.00+
PlayResX: 640
PlayResY: 360
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,36,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,2,1,2,20,20,24,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def ms_to_ass_time(ms: int) -> str:
    cs_total = (ms + 5) // 10
    h = cs_total // 360_000
    m = (cs_total%360_000) // 6_000
    s = (cs_total%6_000) // 100
    cs = cs_total % 100
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def _smi_color_to_ass(color: str) -> str | None:
    color = color.strip().lstrip("#")
    rgb = _NAMED_COLORS.get(color.lower(), color)
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", rgb):
        return None
    bgr = rgb[4:6]+rgb[2:4]+rgb[0:2]
    return f"\\1c&H{bgr.upper()}&"

def _text_to_ass(text: str) -> str:
    def _open_tag(m: re.Match) -> str:
        code = _smi_color_to_ass(m.group(1))
        return "{"+code+"}" if code else ""
    out = _FONT_COLOR_RE.sub(_open_tag, text)
    out = re.sub(r'</font\s*>', r'{\\r}', out, flags=re.IGNORECASE)
    out = re.sub(r'<[^>]+>', '', out)
    out = out.replace('\n', '\\N')
    return out

def entries_to_ass(entries: list[SubtitleEntry]) -> str:
    lines: list[str] = []
    for e in entries:
        lines.append(
            f"Dialogue: 0,{ms_to_ass_time(e.start_ms)},{ms_to_ass_time(e.end_ms)},"
            f"Default,,0,0,0,,{_text_to_ass(e.text)}"
        )
    return _HEADER + "\n".join(lines) + "\n"