from PySide6 import QtWidgets
from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.config import Settings, SettingsManager
from core.result import Result
from core.translate import run_translate


class TranslationThread(QThread):
    result_ready = Signal(object)
    failed = Signal(str)

    def __init__(self, settings: Settings, query: str):
        super().__init__()
        self.settings = settings
        self.query = query

    def run(self):
        try:
            result = run_translate(self.settings, self.query)
            self.result_ready.emit(result)
        except SystemExit as exc:
            self.failed.emit(f"Translation exited with status {exc.code}.")
        except Exception as exc:
            self.failed.emit(str(exc))


class ModelListThread(QThread):
    models_ready = Signal(object)
    failed = Signal(str)

    def __init__(self, settings_manager: SettingsManager):
        super().__init__()
        self.settings_manager = settings_manager

    def run(self):
        try:
            result = self.settings_manager.list_models()

            if result.ok:
                self.models_ready.emit(result.value or [])
            else:
                self.failed.emit(
                    result.message or result.error_code or "Could not load models."
                )
        except Exception as exc:
            self.failed.emit(str(exc))


class Widget(QWidget):
    def __init__(self, settings_manager: SettingsManager):
        super().__init__()

        self.settings_manager = settings_manager

        self.translation_thread: TranslationThread | None = None
        self.model_list_thread: ModelListThread | None = None

        self.left_body = QTextEdit()
        self.left_body.setPlaceholderText("Text to be translated.")
        self.left_body.setPlainText("laufen")
        self.right_body = QTextEdit()

        self.source_language_dropdown = QComboBox()
        self.source_language_dropdown.addItems(settings_manager.allowed_languages)
        source_language = settings_manager.settings.source_language.value
        if source_language is not None:
            self.source_language_dropdown.setCurrentText(source_language)

        self.target_language_dropdown = QComboBox()
        self.target_language_dropdown.addItems(settings_manager.allowed_languages)
        target_language = settings_manager.settings.target_language.value
        if target_language is not None:
            self.target_language_dropdown.setCurrentText(target_language)

        self.provider_dropdown = QComboBox()
        self.provider_dropdown.addItems(
            settings_manager.settings.allowed_providers.keys()
        )
        provider_name = settings_manager.settings.provider_name.value
        if provider_name is not None:
            self.provider_dropdown.setCurrentText(provider_name)

        self.model_selection_dropdown = QComboBox()
        self.model_selection_dropdown.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.model_selection_dropdown.setMaxVisibleItems(10)
        selected_model = settings_manager.get_selected_model()
        if selected_model:
            self.model_selection_dropdown.addItem(selected_model)
            self.model_selection_dropdown.setCurrentText(selected_model)

        self.model_selection_text_box = QLineEdit()
        self.model_selection_text_box.setPlaceholderText("Insert model name.")

        self.translate_button = QPushButton("Translate (Ctrl-T)")

        # layout
        self.left = QVBoxLayout()
        self.left.addWidget(self.source_language_dropdown)
        self.left.addWidget(self.left_body)

        self.right = QVBoxLayout()
        self.right.addWidget(self.target_language_dropdown)
        self.right.addWidget(self.right_body)

        self.columns = QHBoxLayout()
        self.columns.addLayout(self.left, 1)
        self.columns.addLayout(self.right, 1)

        self.model_selection_columns = QHBoxLayout()
        self.model_selection_columns.addWidget(self.model_selection_dropdown, 1)
        self.model_selection_columns.addWidget(self.model_selection_text_box, 1)

        self.main = QVBoxLayout()
        self.main.addLayout(self.columns, 1)
        self.main.addWidget(self.provider_dropdown)
        self.main.addLayout(self.model_selection_columns, 1)
        self.main.addWidget(self.translate_button)

        self.setLayout(self.main)

        self.load_models_async()

        self.translate_button.clicked.connect(self.translate_text)
        self.source_language_dropdown.textActivated.connect(
            self.source_language_changed
        )
        self.target_language_dropdown.textActivated.connect(
            self.target_language_changed
        )
        self.provider_dropdown.textActivated.connect(self.provider_changed)
        self.model_selection_dropdown.textActivated.connect(self.model_changed)
        self.model_selection_text_box.returnPressed.connect(self.set_model_name)

    @Slot()
    def translate_text(self):
        query = self.left_body.toPlainText().strip()

        if not query or self.translation_thread is not None:
            return

        settings = self.settings_manager.settings
        provider_name = settings.provider_name.value
        # settings.source_language.value = self.source_language_dropdown.currentText()
        # settings.target_language.value = self.target_language_dropdown.currentText()

        self.right_body.setEnabled(False)
        self.right_body.setTextColor(QColor("black"))
        self.right_body.setPlainText(f"Waiting for translation from {provider_name}")
        self.translate_button.setEnabled(False)

        self.translation_thread = TranslationThread(settings, query)
        self.translation_thread.result_ready.connect(self.translation_ready)
        self.translation_thread.failed.connect(self.translation_failed)
        self.translation_thread.finished.connect(self.translation_finished)
        self.translation_thread.finished.connect(self.translation_thread.deleteLater)
        self.translation_thread.start()

    @Slot(object)
    def translation_ready(self, result: Result):
        if result.ok:
            self.right_body.setPlainText(result.value or "No translation was returned.")
        else:
            self.right_body.setPlainText(
                result.message or result.error_code or "Translation failed."
            )

    @Slot(str)
    def translation_failed(self, message: str):
        self.right_body.setPlainText(message)

    @Slot()
    def translation_finished(self):
        self.translation_thread = None
        self.translate_button.setEnabled(True)
        self.right_body.setEnabled(True)

    @Slot()
    def source_language_changed(self, new_source_language: str):
        if new_source_language == self.settings_manager.settings.source_language.value:
            return

        if new_source_language == self.settings_manager.settings.target_language.value:
            self.settings_manager.settings.target_language.value = (
                self.settings_manager.settings.source_language.value
            )
            self.target_language_dropdown.setCurrentText(
                self.settings_manager.settings.target_language.value
            )

        self.settings_manager.settings.source_language.value = new_source_language

    @Slot()
    def target_language_changed(self, new_target_language: str):
        if new_target_language == self.settings_manager.settings.target_language.value:
            return

        if new_target_language == self.settings_manager.settings.source_language.value:
            self.settings_manager.settings.source_language.value = (
                self.settings_manager.settings.target_language.value
            )
            self.source_language_dropdown.setCurrentText(
                self.settings_manager.settings.source_language.value
            )

        self.settings_manager.settings.target_language.value = new_target_language

    @Slot(str)
    def provider_changed(self, provider_name: str):
        self.settings_manager.settings.provider_name.value = provider_name

        selected_model = self.settings_manager.get_selected_model()

        self.model_selection_dropdown.clear()
        if selected_model:
            self.model_selection_dropdown.addItem(selected_model)
            # self.model_selection_dropdown.setCurrentText(selected_model)
        self.load_models_async()

    def load_models_async(self):
        if self.model_list_thread is not None:
            return

        self.provider_dropdown.setEnabled(False)
        self.model_selection_dropdown.setEnabled(False)
        self.model_selection_dropdown.setToolTip("Loading available models...")

        self.model_list_thread = ModelListThread(self.settings_manager)
        self.model_list_thread.models_ready.connect(self.models_loaded)
        self.model_list_thread.failed.connect(self.model_loading_failed)
        self.model_list_thread.finished.connect(self.model_loading_finished)
        self.model_list_thread.finished.connect(self.model_list_thread.deleteLater)
        self.model_list_thread.start()

    @Slot(object)
    def models_loaded(self, models: list[str]):
        selected_model = self.settings_manager.get_selected_model()

        if selected_model not in models:
            print(f"{selected_model} not in the models list. Something went wrong!")

        self.model_selection_dropdown.blockSignals(True)
        self.model_selection_dropdown.clear()
        self.model_selection_dropdown.addItems(models)

        if selected_model:
            self.model_selection_dropdown.setCurrentText(selected_model)

        self.model_selection_dropdown.blockSignals(False)
        self.model_selection_dropdown.setToolTip("")

    @Slot(str)
    def model_loading_failed(self, message: str):
        # self.model_selection_dropdown.setToolTip(f"Could not load available models: {message}")
        self.right_body.setPlainText(f"Could not load available models: {message}")

    @Slot()
    def model_loading_finished(self):
        self.model_list_thread = None
        self.provider_dropdown.setEnabled(True)
        self.model_selection_dropdown.setEnabled(True)

    @Slot(str)
    def model_changed(self, model_name: str):
        settings = self.settings_manager.settings
        provider_name = settings.provider_name.value

        if provider_name not in settings.allowed_providers:
            return

        settings.allowed_providers[provider_name]["model"].value = model_name

    @Slot()
    def set_model_name(
        self,
    ):
        entered_model_name = self.model_selection_text_box.text().strip()
        index = self.model_selection_dropdown.findText(entered_model_name)

        if index < 0:
            self.model_selection_text_box.clear()
            self.model_selection_text_box.setPlaceholderText(
                "Inserted model not recognized."
            )
            return

        self.model_selection_dropdown.setCurrentIndex(index)
        self.model_changed(entered_model_name)
        self.model_selection_text_box.clear()
        self.model_selection_text_box.setPlaceholderText("Insert model name.")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, widget):
        super().__init__()
        self.setWindowTitle("Py Polyglot")

        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("File")
        # self.edit_menu = self.menu.addMenu("Edit")
        self.tool_menu = self.menu.addMenu("Tools")

        quit_action = self.file_menu.addAction("Quit", self.close)
        quit_action.setShortcut("Ctrl+Q")

        translate_action = self.tool_menu.addAction("Translate", widget.translate_text)
        translate_action.setShortcut("Ctrl+T")

        self.setCentralWidget(widget)
