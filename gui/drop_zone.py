"""Drag-and-drop / click-to-browse file input widget."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QFrame, QLabel, QVBoxLayout

OPEN_FILE_FILTER = (
    "Supported files (*.jpg *.jpeg *.png *.tiff *.webp *.docx *.mp3 *.flac *.ogg *.m4a);;"
    "All files (*)"
)

HINT_TEXT = "JPG  ·  PNG  ·  TIFF  ·  WEBP  ·  DOCX  ·  MP3  ·  FLAC  ·  OGG  ·  M4A"


class DropZone(QFrame):
    """A dashed drop target that also opens a native file picker on click."""

    fileSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(220)
        self.setProperty("dragActive", False)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        self.icon_label = QLabel("[ + ]")
        self.icon_label.setObjectName("DropZoneIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.text_label = QLabel("Drag & drop a file here, or click to browse")
        self.text_label.setObjectName("DropZoneLabel")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.hint_label = QLabel(HINT_TEXT)
        self.hint_label.setObjectName("DropZoneHint")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addWidget(self.hint_label)

    # -- click to browse -----------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self._open_file_dialog()
        super().mousePressEvent(event)

    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select a file", "", OPEN_FILE_FILTER)
        if path:
            self.fileSelected.emit(path)

    # -- drag and drop ---------------------------------------------------------

    def dragEnterEvent(self, event):
        if self.isEnabled() and event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                self._set_drag_active(True)
                event.acceptProposedAction()
                return
        event.ignore()

    def dragMoveEvent(self, event):
        if self.isEnabled() and event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._set_drag_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._set_drag_active(False)
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            self.fileSelected.emit(urls[0].toLocalFile())
            event.acceptProposedAction()
        else:
            event.ignore()

    def _set_drag_active(self, active):
        self.setProperty("dragActive", active)
        self.style().unpolish(self)
        self.style().polish(self)
