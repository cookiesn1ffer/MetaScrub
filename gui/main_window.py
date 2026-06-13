"""Main window for the MetaScrub desktop app."""

import os
import sys
import uuid
from datetime import datetime, timezone

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QLabel, QMainWindow, QProgressBar, QVBoxLayout, QWidget

import config
from db import logger
from scrubber import core

from .drop_zone import DropZone
from .history_table import HistoryTable
from .icon import create_icon
from .result_panel import ResultPanel
from .styles import STYLESHEET

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 650


class ScrubWorker(QThread):
    """Runs the scrubber backend off the UI thread."""

    success = pyqtSignal(str, str, str, list, str)  # job_id, original_name, file_type, stripped_fields, output_path
    failure = pyqtSignal(str, str, str)  # job_id, original_name, error_message

    def __init__(self, job_id, input_path, output_path, original_name, parent=None):
        super().__init__(parent)
        self.job_id = job_id
        self.input_path = input_path
        self.output_path = output_path
        self.original_name = original_name

    def run(self):
        try:
            file_type, stripped_fields = core.scrub_file(
                self.input_path, self.output_path, self.original_name
            )
        except Exception as exc:  # noqa: BLE001 - surfaced inline in the result panel
            self.failure.emit(self.job_id, self.original_name, str(exc))
            return

        self.success.emit(
            self.job_id, self.original_name, file_type, stripped_fields, self.output_path
        )


def _resolve_db_path():
    """Pick a writable, persistent DB location for both dev and frozen runs."""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = config.BASE_DIR
    return os.path.join(base_dir, "db", "metascrub.db")


def _cleaned_output_path(input_path):
    stem, ext = os.path.splitext(input_path)
    return f"{stem}_clean{ext}"


class MainWindow(QMainWindow):
    """Single-window MetaScrub desktop application."""

    def __init__(self):
        super().__init__()

        self.db_path = _resolve_db_path()
        logger.init_db(self.db_path)

        self._worker = None

        self.setWindowTitle("MetaScrub")
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowIcon(create_icon())
        self.setStyleSheet(STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title_label = QLabel(">_ MetaScrub")
        title_label.setObjectName("TitleLabel")

        subtitle_label = QLabel("Strip hidden metadata from images, documents & audio.")
        subtitle_label.setObjectName("SubtitleLabel")

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)

        self.drop_zone = DropZone()
        self.drop_zone.fileSelected.connect(self.handle_file)
        layout.addWidget(self.drop_zone)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFormat("processing...")
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.result_panel = ResultPanel()
        layout.addWidget(self.result_panel)

        history_label = QLabel("// job history")
        history_label.setObjectName("SectionLabel")
        layout.addWidget(history_label)

        self.history_table = HistoryTable(self.db_path)
        layout.addWidget(self.history_table, stretch=1)

    # -- file handling --------------------------------------------------------

    def handle_file(self, path):
        if self._worker is not None and self._worker.isRunning():
            return

        if not os.path.isfile(path):
            self.result_panel.show_error(f"File not found: {path}")
            return

        filename = os.path.basename(path)
        stem = os.path.splitext(filename)[0]

        if stem.endswith("_clean") or stem.endswith("_cleaned"):
            self.result_panel.show_error("Cannot scrub an already-cleaned file.")
            return

        file_type = core.get_file_type(filename)

        if file_type is None:
            ext = core.get_extension(filename) or "(none)"
            self.result_panel.show_error(
                f"Unsupported file type: .{ext}\n"
                f"Supported: {', '.join(sorted(config.ALLOWED_EXTENSIONS))}"
            )
            return

        output_path = _cleaned_output_path(path)
        job_id = uuid.uuid4().hex
        timestamp = datetime.now(timezone.utc).isoformat()

        logger.create_job(self.db_path, job_id, filename, file_type, timestamp)
        self.history_table.refresh()

        self.result_panel.clear()
        self.drop_zone.setEnabled(False)
        self.progress_bar.setVisible(True)

        self._worker = ScrubWorker(job_id, path, output_path, filename)
        self._worker.success.connect(self._on_success)
        self._worker.failure.connect(self._on_failure)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_success(self, job_id, original_name, file_type, stripped_fields, output_path):
        logger.update_job_success(self.db_path, job_id, stripped_fields, output_path)
        self.result_panel.show_result(original_name, file_type, stripped_fields, output_path)
        self.history_table.refresh()

    def _on_failure(self, job_id, original_name, error_message):
        logger.update_job_error(self.db_path, job_id, error_message)
        self.result_panel.show_error(f"Failed to process {original_name}: {error_message}")
        self.history_table.refresh()

    def _on_worker_finished(self):
        self.progress_bar.setVisible(False)
        self.drop_zone.setEnabled(True)
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
