from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QProgressBar, QComboBox, QCheckBox, QLabel, QHeaderView, QMessageBox, QStatusBar, QSpinBox, QApplication, QSystemTrayIcon, QSystemTrayIcon, QListView, QTreeView, QAbstractItemView
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QIcon, QPixmap, QColor
from gui.styles import MAIN_STYLE
from gui.drop_area import DropArea
from gui.log_panel import LogPanel
from gui.worker import MuxTask, WorkerSignals
from utils.file_matcher import match_files
from core.subtitle_parser import SUB_EXTENSIONS, VIDEO_EXTENSIONS
from core.ffmpeg_locator import get_ffmpeg_version
from utils.i18n import t, set_language, get_language, available_languages, language_name, on_language_changed

SUB_EXTS = " ".join(f"*{ext}" for ext in SUB_EXTENSIONS)
VIDEO_EXTS = " ".join(f"*{ext}" for ext in VIDEO_EXTENSIONS)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(900, 650)
        self.setStyleSheet(MAIN_STYLE)
        self.pairs: list[tuple[Path, Path]] = []
        self.thread_pool = QThreadPool.globalInstance()
        self.thread_pool.setMaxThreadCount(4)
        self.completed = 0
        self.total = 0
        self._active_tasks: list = []
        self._row_pending: list[bool] = []
        self.output_dir: Path | None = None
        self._init_tray()
        self._init_ui()
        self._retranslate()
        on_language_changed(lambda code: self._retranslate())
        self._check_ffmpeg()

    def _init_tray(self):
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("#5B8DEF"))
        self.tray = QSystemTrayIcon(QIcon(pixmap), self)
        self.tray.setToolTip("SubBake")
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 12)
        self.lbl_title = QLabel()
        self.lbl_title.setStyleSheet(
            "font-size: 20px; font-weight: 700; color: #E8E9EB; "
            "padding: 6px 0 2px 0;"
        )
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_title)
        self.lbl_subtitle = QLabel()
        self.lbl_subtitle.setStyleSheet("font-size: 12px; color: #8B9096; margin-bottom: 10px;")
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_subtitle)
        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self._on_files_dropped)
        self.drop_area.clicked.connect(self._on_drop_area_clicked)
        layout.addWidget(self.drop_area)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.btn_add_files = QPushButton()
        self.btn_add_folder = QPushButton()
        self.btn_clear = QPushButton()
        btn_row.addWidget(self.btn_add_files)
        btn_row.addWidget(self.btn_add_folder)
        btn_row.addWidget(self.btn_clear)
        btn_row.addStretch()
        self.lbl_ui_language = QLabel()
        btn_row.addWidget(self.lbl_ui_language)
        self.ui_lang_combo = QComboBox()
        for code in available_languages():
            self.ui_lang_combo.addItem(language_name(code), code)
        self.ui_lang_combo.setCurrentIndex(self.ui_lang_combo.findData(get_language()))
        self.ui_lang_combo.setFixedWidth(110)
        self.ui_lang_combo.currentIndexChanged.connect(self._on_ui_language_changed)
        btn_row.addWidget(self.ui_lang_combo)
        self.lbl_count = QLabel()
        self.lbl_count.setStyleSheet("color: #D6D8DB; font-weight: 600;")
        btn_row.addWidget(self.lbl_count)
        layout.addLayout(btn_row)
        self.table = QTableWidget(0, 5)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 60)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 100)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, stretch=1)
        opt_row = QHBoxLayout()
        opt_row.setSpacing(12)
        self.lbl_sub_language = QLabel()
        opt_row.addWidget(self.lbl_sub_language)
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["kor", "eng", "jpn", "chi", "und"])
        self.lang_combo.setFixedWidth(80)
        opt_row.addWidget(self.lang_combo)
        self.chk_overwrite = QCheckBox()
        opt_row.addWidget(self.chk_overwrite)
        self.chk_default_sub = QCheckBox()
        self.chk_default_sub.setChecked(True)
        opt_row.addWidget(self.chk_default_sub)
        self.lbl_sync = QLabel()
        opt_row.addWidget(self.lbl_sync)
        self.spin_offset = QSpinBox()
        self.spin_offset.setRange(-30000, 30000)
        self.spin_offset.setSingleStep(100)
        self.spin_offset.setValue(0)
        self.spin_offset.setFixedWidth(90)
        opt_row.addWidget(self.spin_offset)
        opt_row.addStretch()
        self.btn_output = QPushButton()
        self.btn_output.clicked.connect(self._select_output_dir)
        opt_row.addWidget(self.btn_output)
        self.lbl_output = QLabel()
        self.lbl_output.setStyleSheet("color: #8B9096; font-size: 11px;")
        opt_row.addWidget(self.lbl_output)
        layout.addLayout(opt_row)
        prog_row = QHBoxLayout()
        self.lbl_total_progress = QLabel()
        prog_row.addWidget(self.lbl_total_progress)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFormat("%v / %m  (%p%)")
        prog_row.addWidget(self.progress, stretch=1)
        layout.addLayout(prog_row)
        btn_action_row = QHBoxLayout()
        self.btn_start = QPushButton()
        self.btn_start.setObjectName("startButton")
        btn_action_row.addWidget(self.btn_start, stretch=1)
        self.btn_cancel = QPushButton()
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setFixedWidth(100)
        self.btn_cancel.setStyleSheet(
            "QPushButton { background-color: #7A3535; "
            "color: #fff; font-weight: 600; border: none; border-radius: 5px; }"
            "QPushButton:hover { background-color: #8F4040; }"
            "QPushButton:disabled { background-color: #2B2D31; color: #565A61; "
            "border: 1px solid #33363B; }"
        )
        btn_action_row.addWidget(self.btn_cancel)
        layout.addLayout(btn_action_row)
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.btn_add_files.clicked.connect(self._add_files)
        self.btn_add_folder.clicked.connect(self._add_folder)
        self.btn_clear.clicked.connect(self._clear)
        self.btn_start.clicked.connect(self._start)
        self.btn_cancel.clicked.connect(self._cancel)

    def _retranslate(self):
        self.setWindowTitle(t("app.window_title"))
        self.lbl_title.setText(t("app.title"))
        self.lbl_subtitle.setText(t("app.subtitle"))
        self.btn_add_files.setText(t("btn.add_files"))
        self.btn_add_folder.setText(t("btn.add_folder"))
        self.btn_clear.setText(t("btn.clear"))
        self.btn_output.setText(t("btn.output_dir"))
        self.btn_start.setText(t("btn.start"))
        self.btn_cancel.setText(t("btn.cancel"))
        self.lbl_ui_language.setText(t("label.ui_language"))
        self.lbl_sub_language.setText(t("label.sub_language"))
        self.lbl_sync.setText("  " + t("label.sync"))
        self.lbl_total_progress.setText(t("label.total_progress"))
        self.lbl_count.setText(t("label.file_count", count=len(self.pairs)))
        self.chk_overwrite.setText(t("chk.overwrite"))
        self.chk_default_sub.setText(t("chk.default_sub"))
        self.chk_default_sub.setToolTip(t("tip.default_sub"))
        self.spin_offset.setToolTip(t("tip.offset"))
        self.tray.setToolTip(t("tray.tooltip"))
        self.table.setHorizontalHeaderLabels([t("table.video"), t("table.subtitle"), t("table.format"), t("table.progress"), t("table.status")])
        if self.output_dir is None:
            self.lbl_output.setText(t("label.output_same"))
        for row, pending in enumerate(self._row_pending):
            if pending:
                self.table.setItem(row, 4, QTableWidgetItem(t("status.waiting")))

    def _on_ui_language_changed(self, index: int):
        code = self.ui_lang_combo.itemData(index)
        if code:
            set_language(code)

    def _check_ffmpeg(self):
        try:
            version = get_ffmpeg_version()
            self.status_bar.showMessage(version)
            self.log_panel.append(t("log.system", version=version))
        except FileNotFoundError:
            self.status_bar.showMessage("FFmpeg was not found")
            self.btn_start.setEnabled(False)
            self.log_panel.append(t("log.ffmpeg_missing"))
            QMessageBox.critical(
                self,
                t("msg.ffmpeg_missing_title"),
                t("ffmpeg.not_found"),
            )

    def _on_files_dropped(self, paths: list[Path]):
        mkvs = [p for p in paths if p.suffix.lower() in VIDEO_EXTENSIONS]
        subs = [p for p in paths if p.suffix.lower() in SUB_EXTENSIONS]
        new_pairs = match_files(mkvs, subs)
        self._add_pairs(new_pairs)
        self.log_panel.append(
            t("log.dropped", files=len(paths), pairs=len(new_pairs))
        )

    def _add_files(self):
        filter_str = (t("filter.media", exts=f"{VIDEO_EXTS} {SUB_EXTS}") + ";;" + t("filter.all"))
        files, _ = QFileDialog.getOpenFileNames(self, t("dialog.select_files"), "", filter_str)
        if files:
            paths = [Path(f) for f in files]
            mkvs = [p for p in paths if p.suffix.lower() in VIDEO_EXTENSIONS]
            subs = [p for p in paths if p.suffix.lower() in SUB_EXTENSIONS]
            self._add_pairs(match_files(mkvs, subs))

    def _on_drop_area_clicked(self):
        dialog = QFileDialog(self, t("dialog.select_files"))
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        for view in dialog.findChildren(QListView) + dialog.findChildren(QTreeView):
            view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        if not dialog.exec():
            return
        paths: list[Path] = []
        for selected in dialog.selectedFiles():
            p = Path(selected)
            if p.is_dir():
                for f in p.rglob("*"):
                    if f.suffix.lower() in SUB_EXTENSIONS or f.suffix.lower() in VIDEO_EXTENSIONS:
                        paths.append(f)
            elif p.suffix.lower() in SUB_EXTENSIONS or p.suffix.lower() in VIDEO_EXTENSIONS:
                paths.append(p)
        if paths:
            mkvs = [f for f in paths if f.suffix.lower() in VIDEO_EXTENSIONS]
            subs = [f for f in paths if f.suffix.lower() in SUB_EXTENSIONS]
            new_pairs = match_files(mkvs, subs)
            self._add_pairs(new_pairs)
            self.log_panel.append(t("log.dropped", files=len(paths), pairs=len(new_pairs)))


    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, t("dialog.select_folder"))
        if folder:
            root = Path(folder)
            all_files = list(root.rglob("*"))
            mkvs = [f for f in all_files if f.suffix.lower() in VIDEO_EXTENSIONS]
            subs = [f for f in all_files if f.suffix.lower() in SUB_EXTENSIONS]
            new_pairs = match_files(mkvs, subs)
            self._add_pairs(new_pairs)
            self.log_panel.append(t("log.folder", name=root.name, pairs=len(new_pairs)))

    def _select_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, t("dialog.select_output"))
        if folder:
            self.output_dir = Path(folder)
            self.lbl_output.setText(str(self.output_dir))
            self.lbl_output.setStyleSheet("color: #5B8DEF; font-size: 11px;")

    def _add_pairs(self, new_pairs: list[tuple[Path, Path]]):
        existing = {(m, s) for m, s in self.pairs}
        for mkv, sub in new_pairs:
            if (mkv, sub) not in existing:
                self.pairs.append((mkv, sub))
                row = self.table.rowCount()
                self.table.insertRow(row)
                self._row_pending.append(True)
                self.table.setItem(row, 0, QTableWidgetItem(mkv.name))
                self.table.setItem(row, 1, QTableWidgetItem(sub.name))
                self.table.setItem(row, 2, QTableWidgetItem(sub.suffix.upper().lstrip(".")))
                self.table.setItem(row, 3, QTableWidgetItem("-"))
                self.table.setItem(row, 4, QTableWidgetItem(t("status.waiting")))
        self.lbl_count.setText(t("label.file_count", count=len(self.pairs)))

    def _clear(self):
        self.pairs.clear()
        self._row_pending.clear()
        self.table.setRowCount(0)
        self.progress.setValue(0)
        self.progress.setMaximum(100)
        self.lbl_count.setText(t("label.file_count", count=0))
        self.log_panel.clear()

    def _start(self):
        if not self.pairs:
            QMessageBox.warning(self, t("msg.notice"), t("msg.no_files"))
            return
        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_add_files.setEnabled(False)
        self.btn_add_folder.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self._active_tasks.clear()
        self.completed = 0
        self.total = len(self.pairs)
        self.progress.setMaximum(self.total)
        self.progress.setValue(0)
        self.signals = WorkerSignals()
        self.signals.progress.connect(self._on_progress)
        self.signals.file_progress.connect(self._on_file_progress)
        self.signals.finished.connect(self._on_finished)
        self.signals.log.connect(self._on_log)
        lang = self.lang_combo.currentText()
        overwrite = self.chk_overwrite.isChecked()
        self.log_panel.append(t("log.start", total=self.total, lang=lang, overwrite=t("common.yes") if overwrite else t("common.no")))
        offset = self.spin_offset.value()
        set_default = self.chk_default_sub.isChecked()
        for i, (mkv, sub) in enumerate(self.pairs):
            task = MuxTask(index=i, mkv_path=mkv, sub_path=sub, output_dir=self.output_dir, language=lang, overwrite=overwrite, offset_ms=offset, set_default=set_default, signals=self.signals)
            self._active_tasks.append(task)
            self.thread_pool.start(task)

    def _cancel(self):
        self.thread_pool.clear()
        for task in self._active_tasks:
            task.cancel()
        running = self.thread_pool.activeThreadCount()
        self.total = self.completed + running
        self.progress.setMaximum(max(self.total, 1))
        self.log_panel.append(t("log.cancel"))
        self.btn_cancel.setEnabled(False)
        if running == 0:
            self.btn_start.setEnabled(True)
            self.btn_add_files.setEnabled(True)
            self.btn_add_folder.setEnabled(True)
            self.btn_clear.setEnabled(True)
            self._active_tasks.clear()
            self.log_panel.append(t("log.cancel_done"))

    def _on_progress(self, index: int, msg: str):
        if index < len(self._row_pending):
            self._row_pending[index] = False
        self.table.setItem(index, 4, QTableWidgetItem(msg))

    def _on_file_progress(self, index: int, value: float):
        pct = int(value * 100)
        self.table.setItem(index, 3, QTableWidgetItem(f"{pct}%"))

    def _on_log(self, index: int, msg: str):
        self.log_panel.append(msg)

    def _on_finished(self, index: int, success: bool, msg: str):
        if index < len(self._row_pending):
            self._row_pending[index] = False
        if success:
            self.table.setItem(index, 3, QTableWidgetItem("100%"))
            self.table.setItem(index, 4, QTableWidgetItem(t("worker.done")))
        else:
            self.table.setItem(index, 4, QTableWidgetItem(f"Failed: {msg[:30]}"))
        self.completed += 1
        self.progress.setValue(self.completed)
        if self.completed >= self.total:
            self.btn_start.setEnabled(True)
            self.btn_cancel.setEnabled(False)
            self.btn_add_files.setEnabled(True)
            self.btn_add_folder.setEnabled(True)
            self.btn_clear.setEnabled(True)
            self._active_tasks.clear()
            self.log_panel.append(t("log.all_done", total=self.total))
            QApplication.beep()
            if self.tray.isVisible():
                self.tray.showMessage(t("msg.done_title"), t("msg.done", total=self.total), QSystemTrayIcon.MessageIcon.Information, 3000)
            QMessageBox.information(self, t("msg.done_title"), t("msg.done", total=self.total))