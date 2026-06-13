"""MetaScrub desktop application entry point."""

import sys

from PyQt6.QtWidgets import QApplication

from gui.icon import create_icon
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(create_icon())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
