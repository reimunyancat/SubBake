import subprocess
import sys
import shutil
import platform
from pathlib import Path
from functools import lru_cache

def _get_bundle_dir() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

@lru_cache(maxsize=1)
def find_ffmpeg() -> str:
    exe = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
    bundle_dir = _get_bundle_dir()
    candidates = [
        bundle_dir / "ffmpeg" / exe,
        bundle_dir / "_internal" / "ffmpeg" / exe,
        bundle_dir / exe
    ]
    for path in candidates:
        if path.is_file():
            return str(path)
    system_path = shutil.which("ffmpeg")
    if system_path:
        return system_path
    raise FileNotFoundError(
        "FFmpeg was not found.\n"
        "Run download_ffmpeg.py or install FFmpeg on your system."
    )

@lru_cache(maxsize=1)
def get_ffmpeg_version() -> str:
    ffmpeg = find_ffmpeg()
    result = subprocess.run(
        [ffmpeg, "-version"], capture_output=True, text=True, check=False
    )
    first_line = result.stdout.split("\n")[0] if result.stdout else "unknown"
    return first_line