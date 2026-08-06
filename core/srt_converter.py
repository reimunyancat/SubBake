from core.subtitle_parser import SubtitleEntry

def ms_to_srt_time(ms: int) -> str:
    h = ms // 3_600_000
    m = (ms % 3_600_000) // 60_000
    s = (ms % 60_000) // 1_000
    mil = ms % 1_000
    return f"{h:02d}:{m:02d}:{s:02d},{mil:03d}"

def entries_to_srt(entries: list[SubtitleEntry]) -> str:
    lines: list[str] = []
    for idx, e in enumerate(entries, 1):
        lines.append(str(idx))
        lines.append(f"{ms_to_srt_time(e.start_ms)} --> {ms_to_srt_time(e.end_ms)}")
        lines.append(e.text)
        lines.append("")
    return "\n".join(lines)