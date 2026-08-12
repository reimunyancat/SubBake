MAIN_STYLE = """
QMainWindow {
    background-color: #1E1F22;
}

QWidget {
    font-family: "SF Pro Display", "Segoe UI", "Apple SD Gothic Neo",
                 "Malgun Gothic", sans-serif;
    font-size: 13px;
    color: #D6D8DB;
}

QTableWidget {
    background-color: #26282C;
    alternate-background-color: #2A2C31;
    border: 1px solid #3A3D42;
    border-radius: 6px;
    gridline-color: #33363B;
    selection-background-color: #37424F;
    selection-color: #E8E9EB;
    outline: none;
}

QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #2F3237;
}

QTableWidget::item:selected {
    background-color: #37424F;
}

QHeaderView::section {
    background-color: #2B2D31;
    color: #8B9096;
    padding: 8px 14px;
    border: none;
    border-bottom: 1px solid #3A3D42;
    font-weight: 600;
    font-size: 12px;
}

QPushButton {
    background-color: #2F3237;
    color: #D6D8DB;
    border: 1px solid #43464C;
    border-radius: 5px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #383B41;
    border-color: #4E5259;
}

QPushButton:pressed {
    background-color: #43464C;
}

QPushButton:disabled {
    background-color: #26282C;
    color: #565A61;
    border-color: #33363B;
}

QPushButton#startButton {
    background-color: #3D5A99;
    color: #FFFFFF;
    font-size: 15px;
    font-weight: 600;
    padding: 12px 24px;
    min-height: 24px;
    border: none;
    border-radius: 6px;
}

QPushButton#startButton:hover {
    background-color: #4768AC;
}

QPushButton#startButton:pressed {
    background-color: #344E86;
}

QPushButton#startButton:disabled {
    background-color: #2B2D31;
    color: #565A61;
}

QProgressBar {
    border: 1px solid #3A3D42;
    border-radius: 5px;
    text-align: center;
    color: #D6D8DB;
    font-weight: 600;
    font-size: 11px;
    background-color: #26282C;
    min-height: 22px;
}

QProgressBar::chunk {
    background-color: #3D5A99;
    border-radius: 4px;
}

QComboBox {
    background-color: #2B2D31;
    border: 1px solid #3A3D42;
    border-radius: 5px;
    padding: 5px 10px;
    color: #D6D8DB;
    min-height: 18px;
}

QComboBox:hover {
    border-color: #4E5259;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #2B2D31;
    border: 1px solid #43464C;
    selection-background-color: #37424F;
    color: #D6D8DB;
    border-radius: 5px;
    outline: none;
    padding: 4px;
}

QCheckBox {
    spacing: 8px;
    color: #C4C7CC;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #4E5259;
    background-color: #26282C;
}

QCheckBox::indicator:hover {
    border-color: #5B6470;
}

QCheckBox::indicator:checked {
    background-color: #3D5A99;
    border-color: #3D5A99;
}

QSpinBox {
    background-color: #2B2D31;
    border: 1px solid #3A3D42;
    border-radius: 5px;
    padding: 4px 8px;
    color: #D6D8DB;
}

QSpinBox:hover {
    border-color: #4E5259;
}

QSpinBox::up-button, QSpinBox::down-button {
    border: none;
    background: transparent;
    width: 16px;
}

QLabel {
    color: #8B9096;
}

QStatusBar {
    background-color: #1A1B1E;
    color: #8B9096;
    font-size: 11px;
    border-top: 1px solid #2F3237;
    padding: 4px 16px;
}

QTextEdit#logPanel {
    background-color: #1A1B1E;
    color: #7E858D;
    border: 1px solid #2F3237;
    border-radius: 5px;
    font-family: "JetBrains Mono", "Cascadia Code", "D2Coding",
                 "Consolas", monospace;
    font-size: 11px;
    padding: 8px 10px;
    selection-background-color: #37424F;
}
"""