"""Result panel: shows stripped fields, errors, download and copy actions."""

import os
import shutil

from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

NO_METADATA_SENTINEL = "No metadata found"


class ResultPanel(QFrame):
    """Displays the outcome of the most recently processed file."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ResultPanel")
        self._output_path = None
        self.setVisible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        self.header_label = QLabel("// scrub complete")
        self.header_label.setObjectName("ResultHeader")

        self.meta_label = QLabel()
        self.meta_label.setObjectName("MetaLabel")
        self.meta_label.setWordWrap(True)

        self.fields_label = QLabel()
        self.fields_label.setObjectName("FieldsLabel")
        self.fields_label.setWordWrap(True)

        self.button_container = QWidget()
        button_row = QHBoxLayout(self.button_container)
        button_row.setContentsMargins(0, 4, 0, 0)
        button_row.setSpacing(10)

        self.download_btn = QPushButton("> download cleaned file")
        self.download_btn.clicked.connect(self._on_download)

        self.copy_btn = QPushButton("copy output path")
        self.copy_btn.clicked.connect(self._on_copy)

        button_row.addWidget(self.download_btn)
        button_row.addWidget(self.copy_btn)
        button_row.addStretch()

        layout.addWidget(self.header_label)
        layout.addWidget(self.meta_label)
        layout.addWidget(self.fields_label)
        layout.addWidget(self.button_container)

    # -- public API ---------------------------------------------------------

    def show_result(self, original_name, file_type, stripped_fields, output_path):
        """Render a successful scrub result."""
        self._output_path = output_path

        self._set_error_state(False)
        self.header_label.setText("// scrub complete")
        self.meta_label.setText(f"file: {original_name}    type: {file_type}")

        if stripped_fields == [NO_METADATA_SENTINEL]:
            self.fields_label.setText(NO_METADATA_SENTINEL.lower())
        else:
            lines = "\n".join(f"✓ {field}" for field in stripped_fields)
            self.fields_label.setText(lines)

        self.button_container.setVisible(True)
        self.setVisible(True)

    def show_error(self, message):
        """Render an inline error state."""
        self._output_path = None

        self._set_error_state(True)
        self.header_label.setText("// error")
        self.meta_label.setText("")
        self.fields_label.setText(message)

        self.button_container.setVisible(False)
        self.setVisible(True)

    def clear(self):
        """Hide the panel ahead of a new job."""
        self._output_path = None
        self.setVisible(False)

    # -- internals -----------------------------------------------------------

    def _set_error_state(self, is_error):
        value = "true" if is_error else "false"
        for widget in (self, self.header_label, self.fields_label):
            widget.setProperty("errorState", value)
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def _on_download(self):
        if not self._output_path or not os.path.exists(self._output_path):
            self.show_error("Cleaned file is no longer available on disk.")
            return

        default_name = os.path.basename(self._output_path)
        path, _ = QFileDialog.getSaveFileName(self, "Save cleaned file", default_name)
        if not path:
            return

        try:
            shutil.copy(self._output_path, path)
        except OSError as exc:
            self.show_error(f"Could not save file: {exc}")

    def _on_copy(self):
        if self._output_path:
            QApplication.clipboard().setText(self._output_path)
