from pathlib import Path
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from core.subtitle_parser import SUB_EXTENSIONS, VIDEO_EXTENSIONS
from utils.i18n import t, on_language_changed

_ACCEPTED_EXTS = VIDEO_EXTENSIONS | set(SUB_EXTENSIONS.keys())

class DropArea(QLabel):
    files_dropped = Signal(list)

    _IDLE_STYLE = """
    QLabel {
        border: 2px dashed #4A4D52;
        border-radius: 8px;
        color: #8B9096;
        font-size: 14px;
        padding: 32px;
        background-color: #26282C;
    }
    """
    _HOVER_STYLE = """
        QLabel {
            border: 2px dashed #5B8DEF;
            border-radius: 8px;
            color: #D6D8DB;
            font-size: 14px;
            padding: 32px;
            background-color: #2A2E35;
        }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(80)
        self.setStyleSheet(self._IDLE_STYLE)
        self.retranslate()
        on_language_changed(lambda code: self.retranslate())

    def retranslate(self):
        self.setText(t("drop.hint"))

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(self._HOVER_STYLE)

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._IDLE_STYLE)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(self._IDLE_STYLE)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(self._IDLE_STYLE)
        paths: list[Path] = []
        for url in event.mimeData().urls():
            p = Path(url.toLocalFile())
            if p.is_dir():
                for f in p.rglob("*"):
                    if f.suffix.lower() in _ACCEPTED_EXTS:
                        paths.append(f)
            elif p.suffix.lower() in _ACCEPTED_EXTS:
                paths.append(p)
        if paths:
            self.files_dropped.emit(paths)