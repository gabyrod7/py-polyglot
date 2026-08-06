import sys
from PySide6 import QtWidgets
from gui.window import MainWindow, Widget


def main() -> None:
    app = QtWidgets.QApplication([])

    widget = Widget()
    window = MainWindow(widget)
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
