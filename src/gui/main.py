from PySide6 import QtWidgets

from gui.window import MainWindow, Widget
from core.config import SettingsManager, Settings


def main(settings_manager: SettingsManager | None = None) -> int:
    if settings_manager is None:
        settings = Settings()
        settings_manager = SettingsManager(settings)
        result = settings_manager.load()
        if not result.ok:
            print(result.message)
            return 1

    app = QtWidgets.QApplication([])

    widget = Widget(settings_manager)
    window = MainWindow(widget)
    window.resize(900, 300)
    # window.resize(800, 600)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
