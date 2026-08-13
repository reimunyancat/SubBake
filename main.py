import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from utils.i18n import DEFAULT_LANGUAGE, set_language

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SubBake")
    app.setStyle("Fusion")
    set_language(DEFAULT_LANGUAGE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()