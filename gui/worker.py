import tempfile
import shutil
import threading
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QRunnable, Slot
from core.subtitle_parser import SubFormat, detect_format, needs_conversion, parse_subtitle
from core.srt_converter import entries_to_srt
from core.ass_converter import entries_to_ass
from core.muxer import mux_subtitle_file, mux_subtitle_text
from utils.encoding import read_with_detected_encoding
from utils.i18n import t

LANG_NAMES = {
    "kor": "Korean", "eng": "English", "jpn": "Japanese", "chi": "Chinese", "und": "Undefined"
}

_file_name_lock = threading.Lock()

class WorkerSignals(QObject):
    progress = Signal(int, str)
    file_progress = Signal(int, float)
    finished = Signal(int, bool, str)
    log = Signal(int, str)

class MuxTask(QRunnable):
    def __init__(self, index: int, mkv_path: Path, sub_path: Path, output_dir: Path | None, language: str, overwrite: bool, offset_ms: int, set_default: bool, signals: WorkerSignals):
        super().__init__()
        self.index = index
        self.mkv_path = mkv_path
        self.sub_path = sub_path
        self.output_dir = output_dir
        self.language = language
        self.overwrite = overwrite
        self.offset_ms = offset_ms
        self.set_default = set_default
        self.signals = signals
        self._cancelled = False
        self.setAutoDelete(False)

    def cancel(self):
        self._cancelled = True

    def _on_ffmpeg_progress(self, value: float):
        pct = int(value*100)
        self.signals.file_progress.emit(self.index, value)
        self.signals.progress.emit(self.index, t("worker.muxing", pct=pct))

    @Slot()
    def run(self):
        out: Path | None = None
        try:
            if self._cancelled:
                self.signals.finished.emit(self.index, False, t("worker.cancelled"))
                return
            fmt = detect_format(self.sub_path)
            self.signals.log.emit(
                self.index,
                t("worker.format", name=self.mkv_path.name, fmt=fmt.value.upper())
            )
            self.signals.progress.emit(
                self.index, t("worker.processing", fmt=fmt.value.upper())
            )
            video_ext = self.mkv_path.suffix
            if self.overwrite:
                tmp = tempfile.NamedTemporaryFile(
                    suffix=video_ext, delete=False
                )
                out = Path(tmp.name)
                tmp.close()
            else:
                base_dir = self.output_dir or self.mkv_path.parent
                out_name = f"{self.mkv_path.stem}_sub{video_ext}"
                with _file_name_lock:
                    out = base_dir / out_name
                    counter = 1
                    while out.exists():
                        out = base_dir / f"{self.mkv_path.stem}_sub({counter}){video_ext}"
                        counter += 1
                    out.touch()
            if self._cancelled:
                if out is not None and out.exists():
                    if self.overwrite or out.stat().st_size == 0:
                        out.unlink(missing_ok=True)
                self.signals.finished.emit(self.index, False, t("worker.cancelled"))
                return
            track_name = LANG_NAMES.get(self.language, self.language)
            if needs_conversion(fmt):
                self.signals.progress.emit(
                    self.index, t("worker.parsing", fmt=fmt.value.upper())
                )
                content = read_with_detected_encoding(self.sub_path)
                entries = parse_subtitle(content, fmt)
                self.signals.log.emit(
                    self.index,
                    t("worker.parsed", name=self.mkv_path.name, count=len(entries))
                )
                if fmt == SubFormat.SMI:
                    target = "ASS"
                    converted = entries_to_ass(entries)
                    sub_suffix = ".ass"
                else:
                    target = "SRT"
                    converted = entries_to_srt(entries)
                    sub_suffix = ".srt"
                self.signals.progress.emit(self.index, t("worker.converting", fmt=target))
                mux_subtitle_text(
                    self.mkv_path, converted, out, self.language,
                    track_name=track_name,
                    offset_ms=self.offset_ms,
                    set_default=self.set_default,
                    on_progress=self._on_ffmpeg_progress,
                    cancel_check=lambda: self._cancelled,
                    sub_suffix=sub_suffix,
                )
            else:
                mux_subtitle_file(
                    self.mkv_path, self.sub_path, out, self.language,
                    track_name=track_name,
                    offset_ms=self.offset_ms,
                    set_default=self.set_default,
                    on_progress=self._on_ffmpeg_progress,
                    cancel_check=lambda: self._cancelled,
                )
            if self.overwrite:
                shutil.move(str(out), str(self.mkv_path))
            self.signals.log.emit(self.index, t("worker.done_log", name=self.mkv_path.name))
            self.signals.finished.emit(self.index, True, t("worker.done"))
        except Exception as e:
            if out is not None and out.exists():
                out.unlink(missing_ok=True)
            self.signals.log.emit(self.index, t("worker.failed_log", name=self.mkv_path.name, error=e))
            self.signals.finished.emit(self.index, False, str(e))