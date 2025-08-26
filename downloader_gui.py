from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QProgressBar, QLineEdit, QLabel, QSpinBox, QFileDialog
)
from PySide6.QtCore import Qt

from downloader_core import load_config, save_config, DownloadWorker


class DownloaderGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("e621 Downloader")
        self.resize(750, 550)

        # Apply dark theme stylesheet
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #dddddd;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12pt;
            }

            QLabel {
                font-weight: bold;
                color: #bbbbbb;
            }

            /* --- Inputs --- */
            QLineEdit, QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                padding: 6px;
                color: #ffffff;
                selection-background-color: #007acc;
                selection-color: #ffffff;
            }

            /* --- SpinBox --- */
            QSpinBox {
                background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                padding: 6px;
                color: #ffffff;
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #444;
                background-color: #3c3c3c;
            }
            QSpinBox::up-button:hover {
                background-color: #505050;
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                border-left: 1px solid #444;
                background-color: #3c3c3c;
            }
            QSpinBox::down-button:hover {
                background-color: #505050;
            }

            /* --- Buttons --- */
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
            }

            /* --- Progress bars --- */
            QProgressBar {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 6px;
                text-align: center;
                color: #cccccc;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 6px;
            }

            /* --- Scrollbars --- */
            QScrollBar:vertical {
                background: #2a2a2a;
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #777;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }

            QScrollBar:horizontal {
                background: #2a2a2a;
                height: 12px;
                margin: 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #555;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #777;
            }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0;
            }
        """)

        # Load default config
        query, download_output, download_limit = load_config()

        layout = QVBoxLayout()
        layout.setSpacing(12)

        # --- Config Inputs ---
        config_layout = QHBoxLayout()
        config_layout.setSpacing(10)

        self.query_input = QLineEdit(query)
        self.query_input.setPlaceholderText("Search query")
        config_layout.addWidget(QLabel("Query:"))
        config_layout.addWidget(self.query_input)

        self.limit_input = QSpinBox()
        self.limit_input.setMinimum(1)
        self.limit_input.setMaximum(9999999)
        self.limit_input.setValue(download_limit)
        config_layout.addWidget(QLabel("Limit:"))
        config_layout.addWidget(self.limit_input)

        self.output_input = QLineEdit(download_output)
        self.output_input.setPlaceholderText("Download folder")
        config_layout.addWidget(QLabel("Output:"))
        config_layout.addWidget(self.output_input)

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_folder)
        config_layout.addWidget(self.browse_button)

        layout.addLayout(config_layout)

        # --- Log box ---
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        layout.addWidget(self.log_box, stretch=1)

        # --- Progress bars ---
        self.file_progress_bar = QProgressBar()
        self.file_progress_bar.setAlignment(Qt.AlignCenter)
        self.file_progress_bar.setFormat("Current file: %p%")
        layout.addWidget(self.file_progress_bar)

        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setAlignment(Qt.AlignCenter)
        self.overall_progress_bar.setFormat("Overall progress: %p%")
        layout.addWidget(self.overall_progress_bar)

        # --- Buttons ---
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.start_button = QPushButton("Start Download")
        self.start_button.clicked.connect(self.start_download)
        buttons_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Download")
        self.stop_button.clicked.connect(self.stop_download)
        self.stop_button.setEnabled(False)
        buttons_layout.addWidget(self.stop_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select download folder")
        if folder:
            self.output_input.setText(folder)

    def start_download(self):
        # Save current config
        query = self.query_input.text().strip()
        output = self.output_input.text().strip()
        limit = self.limit_input.value()
        save_config(query, output, limit)

        # Start worker
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.worker = DownloadWorker(query, output, limit)
        self.worker.progress_signal.connect(self.overall_progress_bar.setValue)
        self.worker.file_progress_signal.connect(self.file_progress_bar.setValue)
        self.worker.log_signal.connect(self.append_log)
        self.worker.stopped_signal.connect(self.download_finished)
        self.worker.start()

    def stop_download(self):
        if hasattr(self, "worker"):
            self.worker.stop()
            self.stop_button.setEnabled(False)

    def append_log(self, message):
        self.log_box.append(message)
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    def download_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.file_progress_bar.setValue(0)
        self.overall_progress_bar.setValue(0)
