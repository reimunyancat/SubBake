from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit
from utils.i18n import t, on_language_changed

class LogPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._toggle_btn = QPushButton()
        self._toggle_btn.setFixedHeight(28)
        self._toggle_btn.setStyleSheet(
            "font-size: 11px; padding: 4px 10px; text-align: left; "
            "color: #8B9096; border: none; border-radius: 4px;"
        )
        self._toggle_btn.clicked.connect(self._toggle)
        layout.addWidget(self._toggle_btn)

        self._text = QTextEdit()
        self._text.setObjectName("logPanel")
        self._text.setReadOnly(True)
        self._text.setFixedHeight(150)
        self._text.setVisible(False)
        layout.addWidget(self._text)

        self._expanded = False
        self.retranslate()

    def retranslate(self):
        label = t("log.hide") if self._expanded else t("log.show")
        arrow = "▲" if self._expanded else "▼"
        self._toggle_btn.setText(f"{label} {arrow}")

    def _toggle(self):
        self._expanded = not self._expanded
        self._text.setVisible(self._expanded)
        self.retranslate()

    def append(self, message: str):
        self._text.append(message)
        sb = self._text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def expand(self):
        if not self._expanded:
            self._toggle()

    def clear(self):
        self._text.clear()