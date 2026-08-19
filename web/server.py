import os
import shutil
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from core.ffmpeg_locator import find_ffmpeg, get_ffmpeg_version
from core.muxer import burn_subtitle, mux_subtitle_file, mux_subtitle_text
from core.srt_converter import entries_to_srt
from core.ass_converter import entries_to_ass
from core.subtitle_parser import SUB_EXTENSIONS, VIDEO_EXTENSIONS, SubFormat, detect_format, needs_conversion,parse_subtitle
from utils.encoding import read_with_detected_encoding

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

WORK_DIR = Path(os.environ.get("SUBBAKE_WORK_DIR", "/var/lib/subbake/jobs"))
MAX_UPLOAD_BYTES = int(os.environ.get("SUBBAKE_MAX_UPLOAD_MB", "512")) * 1024 * 1024
JOB_TTL_SECONDS = int(os.environ.get("SUBBAKE_JOB_TTL", "3600"))
JOB_TIMEOUT_SECONDS = int(os.environ.get("SUBBAKE_JOB_TIMEOUT", "900"))
MAX_ACTIVE_JOBS = int(os.environ.get("SUBBAKE_MAX_ACTIVE_JOBS", "4"))

LANGUAGES = ("kor", "eng", "jpn", "chi", "und")
LANG_NAMES = {
    "kor": "Korean",
    "eng": "English",
    "jpn": "Japanese",
    "chi": "Chinese",
    "und": "Undefined",
}

@dataclass
class Job:
    job_id: str
    work_dir: Path
    video_name: str
    output_name: str
    created_at: float = field(default_factory=time.time)
    status: str = "queued"
    progress: float = 0.0
    message: str = "Queued"
    error: Optional[str] = None
    output_path: Optional[Path] = None
    cancelled: bool = False
    mode: str = "mux"

_jobs: dict[str, Job] = {}
_jobs_lock = threading.Lock()
_slots = threading.Semaphore(MAX_ACTIVE_JOBS)

app = FastAPI(title="SubBake Web", docs_url=None, redoc_url=None)

def _safe_suffix(filename: str, allowed: set[str], label: str = "file") -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported {label} format: {suffix or 'unknown'}. Supported: {', '.join(sorted(allowed))}",
        )
    return suffix

def _save_upload(upload: UploadFile, dest: Path, budget: int) -> int:
    written = 0
    with open(dest, "wb") as f:
        while True:
            chunk = upload.file.read(1 << 20)
            if not chunk:
                break
            written += len(chunk)
            if written > budget:
                f.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Upload is too large.")
            f.write(chunk)
    return written

def _purge_expired() -> None:
    now = time.time()
    with _jobs_lock:
        expired = [j for j in _jobs.values() if now - j.created_at > JOB_TTL_SECONDS]
        for job in expired:
            _jobs.pop(job.job_id, None)
    for job in expired:
        shutil.rmtree(job.work_dir, ignore_errors=True)

def _cleanup_loop() -> None:
    while True:
        time.sleep(300)
        try:
            _purge_expired()
        except Exception:
            pass

def _run_job(job: Job, video_path: Path, sub_path: Path, language: str, offset_ms: int, set_default: bool, mode: str) -> None:
    deadline = time.time() + JOB_TIMEOUT_SECONDS
    if not _slots.acquire(timeout=JOB_TIMEOUT_SECONDS):
        job.status = "failed"
        job.error = "The server is busy. Please try again later."
        job.message = job.error
        return
    try:
        job.status = "running"
        job.message = "Preparing..."

        def cancel_check() -> bool:
            return job.cancelled or time.time() > deadline

        def on_progress(value: float) -> None:
            job.progress = min(max(value, 0.0), 1.0)
            job.message = f"Muxing... {int(job.progress * 100)}%"

        output_path = job.work_dir / job.output_name
        track_name = LANG_NAMES.get(language, language)
        fmt = detect_format(sub_path)

        if mode == "burn":
            if fmt == SubFormat.SUP:
                job.status = "failed"
                job.error = "Bitmap (SUP/PGS) subtitles cannot be burned in. Use mux mode instead."
                job.message = job.error
                return
            if needs_conversion(fmt):
                job.message = f"Parsing {fmt.value.upper()}..."
                content = read_with_detected_encoding(sub_path)
                entries = parse_subtitle(content, fmt)
                if fmt == SubFormat.SMI:
                    target = "ASS"
                    converted = entries_to_ass(entries)
                    sub_suffix = ".ass"
                else:
                    target = "SRT"
                    converted = entries_to_srt(entries)
                    sub_suffix = ".srt"
                job.message = f"Converting {len(entries)} entries to {target}..."
                tmp = NamedTemporaryFile(suffix=sub_suffix, dir=job.work_dir, delete=False)
                try:
                    tmp.write(converted.encode("utf-8"))
                    tmp.close()
                    burn_subtitle(video_path, Path(tmp.name), output_path, offset_ms=offset_ms, on_progress=on_progress, cancel_check=cancel_check)
                finally:
                    Path(tmp.name).unlink(missing_ok=True)
            else:
                burn_subtitle(video_path, sub_path, output_path, offset_ms=offset_ms, on_progress=on_progress, cancel_check=cancel_check)
        elif needs_conversion(fmt):
            job.message = f"Parsing {fmt.value.upper()}..."
            content = read_with_detected_encoding(sub_path)
            entries = parse_subtitle(content, fmt)
            if fmt == SubFormat.SMI:
                target = "ASS"
                converted = entries_to_ass(entries)
                sub_suffix = ".ass"
            else:
                target = "SRT"
                converted = entries_to_srt(entries)
                sub_suffix = ".srt"
            job.message = f"Converting {len(entries)} entries to {target}..."
            mux_subtitle_text(video_path, converted, output_path, language, track_name=track_name, offset_ms=offset_ms, set_default=set_default, on_progress=on_progress, cancel_check=cancel_check,sub_suffix=sub_suffix)
        else:
            mux_subtitle_file(video_path, sub_path, output_path, language, track_name=track_name, offset_ms=offset_ms, set_default=set_default, on_progress=on_progress,cancel_check=cancel_check)

        job.output_path = output_path
        job.progress = 1.0
        job.status = "done"
        job.message = "Done"
        try:
            subprocess.run(
                [find_ffmpeg(), "-y", "-i", str(output_path), "-map", "0:s:0", "-f", "webvtt", str(job.work_dir / "preview.vtt")],
                check=False,
                capture_output=True,
            )
        except Exception:
            pass
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)[:500]
        job.message = "Failed"
    finally:
        _slots.release()
        video_path.unlink(missing_ok=True)
        sub_path.unlink(missing_ok=True)

@app.on_event("startup")
def _on_startup() -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    threading.Thread(target=_cleanup_loop, daemon=True).start()

@app.get("/api/health")
def health() -> dict:
    try:
        version = get_ffmpeg_version()
    except FileNotFoundError:
        return {"ok": False, "ffmpeg": None}
    return {
        "ok": True,
        "ffmpeg": version,
        "maxUploadMb": MAX_UPLOAD_BYTES // (1024 * 1024),
        "videoFormats": sorted(VIDEO_EXTENSIONS),
        "subtitleFormats": sorted(SUB_EXTENSIONS),
        "languages": list(LANGUAGES),
    }

@app.post("/api/jobs")
def create_job(
    video: UploadFile = File(...),
    subtitle: UploadFile = File(...),
    language: str = Form("kor"),
    offset_ms: int = Form(0),
    set_default: bool = Form(True),
    mode: str = Form("mux"),
) -> dict:
    _purge_expired()

    if mode not in ("mux", "burn"):
        raise HTTPException(status_code=400, detail="mode must be 'mux' or 'burn'")
    if language not in LANGUAGES:
        raise HTTPException(status_code=400, detail="Unsupported language tag.")
    if not -30000 <= offset_ms <= 30000:
        raise HTTPException(
            status_code=400,
            detail="Sync offset must be between -30000 and 30000 ms.",
        )

    video_ext = _safe_suffix(video.filename, set(VIDEO_EXTENSIONS), label="video")
    sub_ext = _safe_suffix(subtitle.filename, set(SUB_EXTENSIONS), label="subtitle")

    job_id = uuid.uuid4().hex
    work_dir = WORK_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=False)

    video_path = work_dir / f"input{video_ext}"
    sub_path = work_dir / f"input{sub_ext}"

    try:
        used = _save_upload(video, video_path, MAX_UPLOAD_BYTES)
        _save_upload(subtitle, sub_path, MAX_UPLOAD_BYTES - used)
    except HTTPException:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise

    raw_stem = Path(video.filename).stem[:80]
    safe_stem = "".join(c for c in raw_stem if c.isalnum() or c in " ._-").strip()
    if not safe_stem:
        safe_stem = "output"

    job = Job(job_id=job_id, work_dir=work_dir, video_name=video.filename, output_name=f"{safe_stem}_sub{video_ext}", mode=mode)
    with _jobs_lock:
        _jobs[job_id] = job

    threading.Thread(target=_run_job, args=(job, video_path, sub_path, language, offset_ms, set_default, mode), daemon=True).start()

    return {"jobId": job_id}

@app.get("/api/jobs/{job_id}")
def job_status(job_id: str) -> dict:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found or expired.")
    return {
        "jobId": job.job_id,
        "status": job.status,
        "progress": round(job.progress, 4),
        "message": job.message,
        "error": job.error,
        "fileName": job.output_name,
    }

@app.get("/api/jobs/{job_id}/download")
def download(job_id: str) -> FileResponse:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found or expired.")
    if job.status != "done" or job.output_path is None or not job.output_path.is_file():
        raise HTTPException(status_code=409, detail="The result is not ready.")
    return FileResponse(job.output_path, media_type="application/octet-stream", filename=job.output_name)

@app.delete("/api/jobs/{job_id}")
def cancel_job(job_id: str) -> dict:
    with _jobs_lock:
        job = _jobs.pop(job_id, None)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found or expired.")
    job.cancelled = True
    shutil.rmtree(job.work_dir, ignore_errors=True)
    return {"cancelled": True}

@app.get("/api/jobs/{job_id}/preview")
def preview(job_id: str) -> dict:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found or expired.")
    if job.status != "done" or job.output_path is None:
        raise HTTPException(status_code=404, detail="The result is not ready.")
    vtt = job.work_dir / "preview.vtt"
    return {
        "videoUrl": f"/api/jobs/{job_id}/download",
        "vttUrl": f"/api/jobs/{job_id}/preview.vtt" if vtt.is_file() else None,
        "container": job.output_path.suffix.lower(),
        "playable": job.output_path.suffix.lower() in (".mp4", ".webm"),
        "burned": job.mode == "burn",
    }

@app.get("/api/jobs/{job_id}/preview.vtt")
def preview_vtt(job_id: str) -> FileResponse:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found or expired.")
    vtt = job.work_dir / "preview.vtt"
    if not vtt.is_file():
        raise HTTPException(status_code=404, detail="Preview subtitles not available.")
    return FileResponse(vtt, media_type="text/vtt")

app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")