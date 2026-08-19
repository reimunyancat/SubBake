import re
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Callable, Optional
from core.ffmpeg_locator import find_ffmpeg
from utils.i18n import t

SUB_CODEC_MAP = {
    ".srt": "srt",
    ".ass": "ass",
    ".ssa": "ass",
    ".vtt": "webvtt",
    ".sup": "copy",
}
MP4_SUB_CODEC = "mov_text"
WEBM_SUB_CODEC = "webvtt"

def _probe_mkv(ffmpeg: str, mkv_path: Path) -> tuple[Optional[int], int]:
    result = subprocess.run(
        [ffmpeg, "-i", str(mkv_path)],
        capture_output=True, text=True, check=False,
    )
    stderr = result.stderr
    duration_ms: Optional[int] = None
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", stderr)
    if m:
        h, mn, s = int(m[1]), int(m[2]), int(m[3])
        frac = m[4]
        frac_ms = int(frac.ljust(3, "0")[:3])
        duration_ms = (h * 3600 + mn * 60 + s) * 1000 + frac_ms
    sub_count = len(re.findall(r"Stream #\d+:\d+.*?: Subtitle", stderr))
    return duration_ms, sub_count

def mux_subtitle_file(mkv_path: Path, sub_path: Path, output_path: Path, language: str = "kor", track_name: str = "Korean",
    offset_ms: int = 0,
    set_default: bool = False,
    on_progress: Optional[Callable[[float], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> None:
    ffmpeg = find_ffmpeg()
    out_ext = output_path.suffix.lower()
    if out_ext == ".mp4":
        if sub_path.suffix.lower() == ".sup":
            raise ValueError(t("mux.mp4_no_sup"))
        codec = MP4_SUB_CODEC
    elif out_ext == ".webm":
        if sub_path.suffix.lower() == ".sup":
            raise ValueError(t("mux.webm_no_sup"))
        codec = WEBM_SUB_CODEC
    else:
        codec = SUB_CODEC_MAP.get(sub_path.suffix.lower(), "srt")
    duration_ms, sub_index = _probe_mkv(ffmpeg, mkv_path)
    offset_args = ["-itsoffset", f"{offset_ms / 1000:.3f}"] if offset_ms else []
    include_existing_subs = (out_ext == ".mkv")
    if not include_existing_subs:
        sub_index = 0
    sub_codec_args = ["-c:s", "copy"]
    if codec != "copy":
        sub_codec_args += [f"-c:s:{sub_index}", codec]
    existing_sub_map = ["-map", "0:s?"] if include_existing_subs else []
    cmd = [
        ffmpeg,
        "-i", str(mkv_path),
        *offset_args,
        "-i", str(sub_path),
        "-map", "0:v",
        "-map", "0:a?",
        *existing_sub_map,
        "-map", "1:0",
        "-c", "copy",
        *sub_codec_args,
        f"-metadata:s:s:{sub_index}", f"language={language}",
        f"-metadata:s:s:{sub_index}", f"title={track_name}",
        *(["-disposition:s", "0",
           f"-disposition:s:{sub_index}", "default"] if set_default else []),
        "-progress", "pipe:1",
        "-y",
        str(output_path)
    ]
    stderr_chunks: list[str] = []
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    def _drain_stderr() -> None:
        if proc.stderr:
            for chunk in proc.stderr:
                stderr_chunks.append(chunk)
    stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
    stderr_thread.start()
    if proc.stdout:
        for line in proc.stdout:
            if cancel_check and cancel_check():
                proc.terminate()
                proc.wait()
                stderr_thread.join(timeout=2)
                raise RuntimeError(t("mux.cancelled"))
            line = line.strip()
            if not duration_ms or not on_progress:
                continue
            if line.startswith("out_time_us="):
                try:
                    us = int(line.split("=", 1)[1])
                    progress = min(us / (duration_ms * 1000), 1.0)
                    on_progress(progress)
                except (ValueError, ZeroDivisionError):
                    pass
            elif line.startswith("out_time_ms="):
                try:
                    us_val = int(line.split("=", 1)[1])
                    progress = min(us_val / (duration_ms * 1000), 1.0)
                    on_progress(progress)
                except (ValueError, ZeroDivisionError):
                    pass
    proc.wait()
    stderr_thread.join(timeout=2)
    if proc.returncode != 0:
        stderr_output = "".join(stderr_chunks)
        raise RuntimeError(
            t(
                "mux.ffmpeg_error",
                code=proc.returncode,
                stderr=stderr_output[-500:] if stderr_output else t("mux.unknown_error"),
            )
        )

def mux_subtitle_text(mkv_path: Path, sub_content: str, output_path: Path, language: str = "kor", track_name: str = "Korean",
    offset_ms: int = 0,
    set_default: bool = False,
    on_progress: Optional[Callable[[float], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
    sub_suffix: str = ".srt",
) -> None:
    with tempfile.NamedTemporaryFile(
        suffix=sub_suffix, delete=False, mode="w", encoding="utf-8",
    ) as tmp:
        tmp.write(sub_content)
        tmp_path = Path(tmp.name)
    try:
        mux_subtitle_file(
            mkv_path, tmp_path, output_path, language, track_name,
            offset_ms, set_default, on_progress, cancel_check,
        )
    finally:
        tmp_path.unlink(missing_ok=True)

def _escape_filter_path(path: Path) -> str:
    return (
        str(path)
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace(",", "\\,")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )

def burn_subtitle(
    video_path: Path,
    sub_path: Path,
    output_path: Path,
    offset_ms: int = 0,
    on_progress: Optional[Callable[[float], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> None:
    ffmpeg = find_ffmpeg()
    duration_ms, _ = _probe_mkv(ffmpeg, video_path)
    filter_sub = sub_path
    tmp_path: Optional[Path] = None
    try:
        if offset_ms:
            tmp = tempfile.NamedTemporaryFile(suffix=sub_path.suffix, delete=False)
            tmp.close()
            tmp_path = Path(tmp.name)
            result = subprocess.run(
                [ffmpeg, "-y", "-itsoffset", f"{offset_ms / 1000:.3f}", "-i", str(sub_path), "-c", "copy", str(tmp_path)],
                capture_output=True, text=True, check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    t(
                        "mux.ffmpeg_error",
                        code=result.returncode,
                        stderr=result.stderr[-500:] if result.stderr else t("mux.unknown_error"),
                    )
                )
            filter_sub = tmp_path
        cmd = [
            ffmpeg,
            "-i", str(video_path),
            "-map", "0:v:0",
            "-map", "0:a?",
            "-vf", f"subtitles={_escape_filter_path(filter_sub)}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-preset", "medium",
            "-c:a", "copy",
            "-progress", "pipe:1",
            "-y",
            str(output_path),
        ]
        stderr_chunks: list[str] = []
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        def _drain_stderr() -> None:
            if proc.stderr:
                for chunk in proc.stderr:
                    stderr_chunks.append(chunk)
        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stderr_thread.start()
        if proc.stdout:
            for line in proc.stdout:
                if cancel_check and cancel_check():
                    proc.terminate()
                    proc.wait()
                    stderr_thread.join(timeout=2)
                    raise RuntimeError(t("mux.cancelled"))
                line = line.strip()
                if not duration_ms or not on_progress:
                    continue
                if line.startswith("out_time_us="):
                    try:
                        us = int(line.split("=", 1)[1])
                        progress = min(us / (duration_ms * 1000), 1.0)
                        on_progress(progress)
                    except (ValueError, ZeroDivisionError):
                        pass
                elif line.startswith("out_time_ms="):
                    try:
                        us_val = int(line.split("=", 1)[1])
                        progress = min(us_val / (duration_ms * 1000), 1.0)
                        on_progress(progress)
                    except (ValueError, ZeroDivisionError):
                        pass
        proc.wait()
        stderr_thread.join(timeout=2)
        if proc.returncode != 0:
            stderr_output = "".join(stderr_chunks)
            raise RuntimeError(
                t(
                    "mux.ffmpeg_error",
                    code=proc.returncode,
                    stderr=stderr_output[-500:] if stderr_output else t("mux.unknown_error"),
                )
            )
    finally:
        if tmp_path:
            tmp_path.unlink(missing_ok=True)
