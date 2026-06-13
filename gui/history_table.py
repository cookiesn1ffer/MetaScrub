"""Job history table backed by the SQLite job logger."""

import json
import os
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from db import logger

COLUMNS = ["Filename", "Type", "Stripped", "Timestamp", ""]


def _format_timestamp(value):
    if not value:
        return "-"
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return value


class HistoryTable(QTableWidget):
    """Read-only table of past scrub jobs, with per-row delete."""

    def __init__(self, db_path, parent=None):
        super().__init__(0, len(COLUMNS), parent)
        self.db_path = db_path

        self.setHorizontalHeaderLabels(COLUMNS)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3, 4):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        self.verticalHeader().setDefaultSectionSize(36)

        self.refresh()

    def refresh(self):
        """Reload the most recent jobs from the database."""
        jobs = logger.get_history(self.db_path, limit=50)
        self.setRowCount(0)

        for job in jobs:
            row = self.rowCount()
            self.insertRow(row)

            self.setItem(row, 0, QTableWidgetItem(job["original_name"] or "-"))
            self.setItem(row, 1, QTableWidgetItem(job["file_type"] or "-"))
            self.setItem(row, 2, QTableWidgetItem(self._stripped_text(job)))
            self.setItem(row, 3, QTableWidgetItem(_format_timestamp(job["timestamp"])))

            delete_btn = QPushButton("delete")
            delete_btn.setObjectName("DeleteButton")
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.clicked.connect(lambda _checked, j=job: self._delete_job(j))
            self.setCellWidget(row, 4, delete_btn)

    @staticmethod
    def _stripped_text(job):
        if job["status"] == "completed":
            try:
                return str(len(json.loads(job["stripped_fields"])))
            except (TypeError, ValueError):
                return "0"
        if job["status"] == "failed":
            return "failed"
        return "-"

    def _delete_job(self, job):
        cleaned_path = job.get("cleaned_filename")
        if cleaned_path and os.path.exists(cleaned_path):
            try:
                os.remove(cleaned_path)
            except OSError:
                pass

        logger.delete_job(self.db_path, job["job_id"])
        self.refresh()
