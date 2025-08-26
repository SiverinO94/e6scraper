import sys
from PySide6.QtWidgets import QApplication
from downloader_gui import DownloaderGUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DownloaderGUI()
    window.show()
    sys.exit(app.exec())
