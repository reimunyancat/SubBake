from pathlib import Path
from core.subtitle_parser import SUB_EXTENSIONS

PRIORITY = {".smi":0,".srt":1,".ass":2,".ssa":3,".vtt":4,".sup":5}

def match_files(mkv_files: list[Path], sub_files: list[Path]) -> list[tuple[Path, Path]]:
    sub_map: dict[tuple[Path, str], list[tuple[int, Path]]] = {}
    for f in sub_files:
        if f.suffix.lower() in SUB_EXTENSIONS:
            key = (f.parent, f.stem.lower())
            priority = PRIORITY.get(f.suffix.lower(), 99)
            sub_map.setdefault(key, []).append((priority, f))
    pairs: list[tuple[Path, Path]] = []
    for mkv in mkv_files:
        key = (mkv.parent, mkv.stem.lower())
        candidates = sub_map.get(key)
        if candidates:
            best = min(candidates, key=lambda x:x[0])
            pairs.append((mkv, best[1]))
    return pairs
