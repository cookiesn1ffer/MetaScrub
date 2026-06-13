"""PyInstaller build script for the MetaScrub desktop app.

Produces:
- dist/MetaScrub-windows.exe (Windows, onefile, windowed)
- dist/MetaScrub-linux       (Linux, onefile)
"""

import os
import platform
import sys

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
ICON_PATH = os.path.join(ASSETS_DIR, "icon.ico")
ENTRY_POINT = os.path.join(PROJECT_ROOT, "gui.py")

# Mutagen and Pillow resolve their format-specific modules dynamically, so
# they need to be spelled out for PyInstaller's static import analysis.
HIDDEN_IMPORTS = [
    "mutagen.id3",
    "mutagen.mp3",
    "mutagen.flac",
    "mutagen.oggvorbis",
    "mutagen.mp4",
    "mutagen.easyid3",
    "mutagen.easymp4",
    "PIL.Image",
    "PIL.ImageFile",
    "PIL.JpegImagePlugin",
    "PIL.PngImagePlugin",
    "PIL.TiffImagePlugin",
    "PIL.WebPImagePlugin",
]


def generate_icon():
    """Render assets/icon.ico with QPainter before PyInstaller runs."""
    from PyQt6.QtWidgets import QApplication

    from gui.icon import save_icon_ico

    os.makedirs(ASSETS_DIR, exist_ok=True)

    app = QApplication.instance() or QApplication(sys.argv)
    save_icon_ico(ICON_PATH)
    del app


def build():
    from PyInstaller.__main__ import run as pyinstaller_run

    generate_icon()

    is_windows = platform.system() == "Windows"
    output_name = "MetaScrub-windows" if is_windows else "MetaScrub-linux"
    data_sep = os.pathsep

    args = [
        ENTRY_POINT,
        "--name", output_name,
        "--onefile",
        "--noconfirm",
        "--clean",
        "--distpath", os.path.join(PROJECT_ROOT, "dist"),
        "--workpath", os.path.join(PROJECT_ROOT, "build_pyinstaller"),
        "--specpath", os.path.join(PROJECT_ROOT, "build_pyinstaller"),
        "--icon", ICON_PATH,
        "--add-data", f"{ASSETS_DIR}{data_sep}assets",
        "--add-data", f"{os.path.join(PROJECT_ROOT, 'scrubber')}{data_sep}scrubber",
        "--add-data", f"{os.path.join(PROJECT_ROOT, 'db')}{data_sep}db",
    ]

    for module in HIDDEN_IMPORTS:
        args += ["--hidden-import", module]

    if is_windows:
        args.append("--windowed")
    else:
        args.append("--strip")

    pyinstaller_run(args)


if __name__ == "__main__":
    build()
