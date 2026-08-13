import platform
import sys
import zipfile
import tarfile
import shutil
import requests
from pathlib import Path
from utils.i18n import t

FFMPEG_DIR = Path(__file__).parent / "ffmpeg"
_MACOS_ARM_FALLBACK = "https://evermeet.cx/ffmpeg/getrelease/zip"

def _get_download_url() -> str:
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Windows":
        return (
            "https://github.com/BtbN/FFmpeg-Builds/releases/download/"
            "latest/ffmpeg-master-latest-win64-gpl.zip"
        )
    elif system == "Darwin":
        if "arm" in machine or "aarch64" in machine:
            return "https://www.osxexperts.net/ffmpeg7arm.zip"
        else:
            return "https://evermeet.cx/ffmpeg/getrelease/zip"
    elif system == "Linux":
        return (
            "https://github.com/BtbN/FFmpeg-Builds/releases/download/"
            "latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
        )
    else:
        raise RuntimeError(t("dl.unsupported_os", system=system))

def _normalize_archive_name(url: str) -> str:
    archive_name = url.split("/")[-1]
    if not any(archive_name.endswith(ext) for ext in (".zip", ".tar.xz", ".tar.gz")): archive_name = "ffmpeg_download.zip"
    return archive_name

def download_ffmpeg():
    url = _get_download_url()
    system = platform.system()
    machine = platform.machine().lower()
    FFMPEG_DIR.mkdir(exist_ok=True)
    archive_name = _normalize_archive_name(url)
    archive_path = FFMPEG_DIR / archive_name
    print(t("dl.downloading", system=system, machine=platform.machine()))
    try:
        resp = requests.get(url, stream=True, timeout=300, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException:
        if system == "Darwin" and ("arm" in machine or "aarch64" in machine):
            print(t("dl.fallback"))
            print(t("dl.rosetta"))
            url = _MACOS_ARM_FALLBACK
            archive_name = _normalize_archive_name(url)
            archive_path = FFMPEG_DIR / archive_name
            resp = requests.get(url, stream=True, timeout=300, allow_redirects=True)
            resp.raise_for_status()
        else:
            raise
    total = int(resp.headers.get("content-length", 0))
    downloaded = 0
    with open(archive_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1 << 20):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded * 100 // total
                print("\r" + t("dl.progress", pct=pct), end="", flush=True)
    print()
    print(t("dl.extracting"))
    tmp_dir = FFMPEG_DIR / "_tmp"
    tmp_dir.mkdir(exist_ok=True)
    try:
        if archive_name.endswith(".zip"):
            with zipfile.ZipFile(archive_path) as zf:
                zf.extractall(tmp_dir)
        elif archive_name.endswith((".tar.xz", ".tar.gz")):
            with tarfile.open(archive_path) as tf:
                if sys.version_info >= (3, 12):
                    tf.extractall(tmp_dir, filter="data")
                else:
                    tf.extractall(tmp_dir)
        else:
            raise RuntimeError(t("dl.unknown_archive", name=archive_name))
        exe_name = "ffmpeg.exe" if system == "Windows" else "ffmpeg"
        found = [f for f in tmp_dir.rglob(exe_name) if f.is_file()]
        if not found:
            raise FileNotFoundError(t("dl.not_in_archive", exe=exe_name))
        dest = FFMPEG_DIR / exe_name
        shutil.copy2(found[0], dest)
        if system != "Windows":
            dest.chmod(0o755)
        print(t("dl.ready", path=dest))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        archive_path.unlink(missing_ok=True)

if __name__ == "__main__":
    download_ffmpeg()