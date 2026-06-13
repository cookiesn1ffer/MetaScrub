"""Programmatic application icon - a green terminal cursor on a dark square.

Generated entirely with QPainter so the app ships with zero external
image assets.
"""

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap

from .styles import ACCENT, BG


def create_icon_pixmap(size=256):
    """Render a ">_" terminal-cursor glyph in accent green on a dark square."""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(BG))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    border = QColor(ACCENT)
    border_width = max(2, size // 32)
    painter.setPen(border)
    inset = border_width / 2
    painter.drawRoundedRect(
        QRectF(inset, inset, size - border_width, size - border_width),
        size * 0.08,
        size * 0.08,
    )

    font = QFont(["JetBrains Mono", "Courier New"])
    font.setBold(True)
    font.setPixelSize(int(size * 0.5))
    painter.setFont(font)
    painter.setPen(QColor(ACCENT))
    painter.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, ">_")

    painter.end()
    return pixmap


def create_icon():
    """Return a QIcon built from the programmatic cursor pixmap."""
    return QIcon(create_icon_pixmap())


def save_icon_ico(path, size=256):
    """Render the icon and save it as a .ico file at ``path``."""
    pixmap = create_icon_pixmap(size)
    pixmap.save(path, "ICO")
