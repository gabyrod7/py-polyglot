import random
from dataclasses import dataclass
from pathlib import Path

from PySide6 import QtWidgets
from PySide6.QtCore import QThread, Signal, Qt, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from core.config import SettingsManager, Settings
from core.result import Result
from core.translate import run_translate


class TranslationThread(QThread):
    result_ready = Signal(object)
    failed = Signal(str)

    #def __init__(self, settings: Settings, query: str, parent=None):
    #    super().__init__(parent)
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
                    result.message
                    or result.error_code
                    or "Could not load models."
                )
        except Exception as exc:
            self.failed.emit(str(exc))

@dataclass
class DirectoryEntry:
    path: Path
    is_dir: bool
    body: str | None = None
    children_loaded: bool = False


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

        self.combobox1 = QComboBox()
        self.combobox1.addItems(settings_manager.allowed_languages)
        source_language = settings_manager.settings.source_language.value
        if source_language is not None:
            self.combobox1.setCurrentText(source_language)
        
        self.combobox2 = QComboBox()
        self.combobox2.addItems(settings_manager.allowed_languages)
        target_language = settings_manager.settings.target_language.value
        if target_language is not None:
            self.combobox2.setCurrentText(target_language)

        self.combobox3 = QComboBox()
        self.combobox3.addItems(settings_manager.settings.allowed_providers.keys())
        provider_name = settings_manager.settings.provider_name.value
        if provider_name is not None:
            self.combobox3.setCurrentText(provider_name)

        self.combobox4 = QComboBox()
        selected_model = settings_manager.get_selected_model()
        if selected_model:
            self.combobox4.addItem(selected_model)
            self.combobox4.setCurrentText(selected_model)

        # layout
        self.left = QVBoxLayout()
        self.left.addWidget(self.combobox1)
        self.left.addWidget(self.left_body)

        self.right = QVBoxLayout()
        self.right.addWidget(self.combobox2)
        self.right.addWidget(self.right_body)

        self.columns = QHBoxLayout()
        self.columns.addLayout(self.left, 1)
        self.columns.addLayout(self.right, 1)

        self.translate_button = QPushButton("Translate (Ctrl-T)")

        self.main = QVBoxLayout()
        self.main.addLayout(self.columns, 1)
        self.main.addWidget(self.combobox3)
        self.main.addWidget(self.combobox4)
        self.main.addWidget(self.translate_button)

        self.setLayout(self.main)

        self.load_models_async()

        self.translate_button.clicked.connect(self.translate_text)
        self.combobox3.textActivated.connect(self.provider_changed)
        self.combobox4.textActivated.connect(self.model_changed)




        #self.current_dir = Path.cwd()

        #self.notes_tree = QTreeWidget()
        #self.notes_tree.setHeaderLabel("Files")
        #self.note_file_name_edit = QLineEdit()
        #self.body_edit = QTextEdit()
        #self.search_edit = QLineEdit()
        #self.search_edit.setPlaceholderText("Search disabled")
        #self.search_edit.setEnabled(False)
        #self.translation_output = QTextEdit()
        #self.translation_output.setReadOnly(True)
        #self.translation_output.setMaximumHeight(65)

        #self.left = QVBoxLayout()
        #self.left.addWidget(QLabel("Files"))
        #self.left.addWidget(self.search_edit)
        #self.left.addWidget(self.notes_tree)
        #self.left.addWidget(QLabel("File Name"))
        #self.left.addWidget(self.note_file_name_edit)

        #self.right = QVBoxLayout()
        #self.right.addWidget(QLabel("Body"))
        #self.right.addWidget(self.body_edit)
        #self.right.addWidget(QLabel("Translation"))
        #self.right.addWidget(self.translation_output)

        #self.translate = QPushButton("Translate (Ctrl-T)")
        #self.new = QPushButton("New (Ctrl-N)")
        #self.save = QPushButton("Save (Ctrl-S)")
        #self.delete = QPushButton("Delete")
        #self.right.addWidget(self.translate)

        #self.buttons_row = QHBoxLayout()
        #self.buttons_row.addWidget(self.new)
        #self.buttons_row.addWidget(self.save)
        #self.buttons_row.addWidget(self.delete)
        #self.right.addLayout(self.buttons_row)

        #self.translate.clicked.connect(self.translate_text)
        #self.new.clicked.connect(self.new_note)
        #self.notes_tree.currentItemChanged.connect(self.select_entry)
        #self.notes_tree.itemClicked.connect(self.load_directory_on_click)
        #self.notes_tree.itemExpanded.connect(self.load_directory_children)
        #self.save.clicked.connect(self.save_note)
        #self.delete.clicked.connect(self.delete_note)

        #self.main = QHBoxLayout()
        #self.main.addLayout(self.left, 5)
        #self.main.addLayout(self.right, 5)

        #self.setLayout(self.main)
        #self.load_root_directory(self.current_dir)

    def load_root_directory(self, directory: Path):
        self.current_dir = directory
        self.notes_tree.clear()

        root_entry = DirectoryEntry(directory, is_dir=True)
        root_item = QTreeWidgetItem([directory.name or str(directory)])
        root_item.setData(0, Qt.ItemDataRole.UserRole, root_entry)
        root_item.setChildIndicatorPolicy(
            QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
        )

        self.notes_tree.addTopLevelItem(root_item)
        self.load_directory_children(root_item)
        root_item.setExpanded(True)

    @Slot(QTreeWidgetItem)
    def load_directory_children(self, item: QTreeWidgetItem):
        entry = item.data(0, Qt.ItemDataRole.UserRole)

        if entry is None or not entry.is_dir or entry.children_loaded:
            return

        try:
            paths = sorted(
                entry.path.iterdir(),
                key=lambda path: (not path.is_dir(), path.name.lower()),
            )
        except OSError:
            entry.children_loaded = True
            return

        for path in paths:
            child_entry = DirectoryEntry(path=path, is_dir=path.is_dir())
            child_item = QTreeWidgetItem([path.name])
            child_item.setData(0, Qt.ItemDataRole.UserRole, child_entry)

            if path.is_dir():
                child_item.setChildIndicatorPolicy(
                    QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
                )

            item.addChild(child_item)

        entry.children_loaded = True

    @Slot(QTreeWidgetItem, int)
    def load_directory_on_click(self, item: QTreeWidgetItem, column: int):
        self.load_directory_children(item)

    @Slot()
    def new_note(self):
        parent_item = self.directory_for_new_note()
        parent_entry = parent_item.data(0, Qt.ItemDataRole.UserRole)

        if not parent_entry.children_loaded:
            self.load_directory_children(parent_item)

        num = random.randint(1, 100000)
        file_name = f"tmp{num}.txt"
        body = f"{[x for x in range(random.randint(1, 100))]}"
        path = parent_entry.path / file_name
        entry = DirectoryEntry(path=path, is_dir=False, body=body)
        item = QTreeWidgetItem([file_name])
        item.setData(0, Qt.ItemDataRole.UserRole, entry)

        parent_item.addChild(item)
        parent_item.setExpanded(True)
        self.notes_tree.setCurrentItem(item)

    def directory_for_new_note(self) -> QTreeWidgetItem:
        item = self.notes_tree.currentItem() or self.notes_tree.topLevelItem(0)
        entry = item.data(0, Qt.ItemDataRole.UserRole)

        if entry.is_dir:
            return item

        return item.parent() or self.notes_tree.topLevelItem(0)

    @Slot(QTreeWidgetItem, QTreeWidgetItem)
    def select_entry(
        self, current: QTreeWidgetItem | None, previous: QTreeWidgetItem | None
    ):
        if current is None:
            return

        entry = current.data(0, Qt.ItemDataRole.UserRole)

        if entry.is_dir:
            self.note_file_name_edit.setText(entry.path.name)
            self.body_edit.clear()
            self.body_edit.setEnabled(False)
            return

        if entry.body is None:
            try:
                entry.body = entry.path.read_text()
            except OSError as error:
                entry.body = f"Could not read file: {error}"
            except UnicodeDecodeError as error:
                entry.body = f"Could not decode file as text: {error}"

        self.body_edit.setEnabled(True)
        self.note_file_name_edit.setText(entry.path.name)
        self.body_edit.setPlainText(entry.body)

    @Slot()
    def save_note(self):
        current_item = self.notes_tree.currentItem()
        if current_item is None:
            return

        entry = current_item.data(0, Qt.ItemDataRole.UserRole)
        if entry.is_dir:
            return

        file_name = self.note_file_name_edit.text()
        if not file_name:
            return

        body = self.body_edit.toPlainText()
        new_path = entry.path.with_name(file_name)

        if new_path != entry.path and entry.path.exists():
            entry.path.rename(new_path)

        new_path.write_text(body)
        entry.path = new_path
        entry.body = body
        current_item.setText(0, file_name)

    @Slot()
    def delete_note(self):
        current_item = self.notes_tree.currentItem()
        if current_item is None:
            return

        entry = current_item.data(0, Qt.ItemDataRole.UserRole)
        if entry.is_dir:
            return

        if entry.path.exists():
            entry.path.unlink()

        parent = current_item.parent()
        if parent is None:
            index = self.notes_tree.indexOfTopLevelItem(current_item)
            self.notes_tree.takeTopLevelItem(index)
        else:
            parent.removeChild(current_item)

        self.body_edit.clear()
        self.note_file_name_edit.clear()

    @Slot(str)
    def filter_notes(self, text):
        return

    @Slot()
    def translate_text(self):
        query = self.left_body.toPlainText().strip()

        if not query or self.translation_thread is not None:
            return

        settings = self.settings_manager.settings
        provider_name = settings.provider_name.value
        settings.source_language.value = self.combobox1.currentText()
        settings.target_language.value = self.combobox2.currentText()

        self.right_body.setPlainText(f"Waiting for translation from {provider_name}")
        self.translate_button.setEnabled(False)

        self.translation_thread = TranslationThread(settings, query)
        self.translation_thread.result_ready.connect(self.translation_ready)
        #self.translation_thread.failed.connect(self.translation_failed)
        self.translation_thread.finished.connect(self.translation_finished)
        self.translation_thread.finished.connect(self.translation_thread.deleteLater)
        self.translation_thread.start()

    @Slot(object)
    def translation_ready(self, result: Result):
        if result.ok:
            self.right_body.setPlainText(
                result.value or "No translation was returned."
            )
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


    @Slot(str)
    def provider_changed(self, provider_name: str):
        self.settings_manager.settings.provider_name.value = provider_name

        selected_model = self.settings_manager.get_selected_model()

        self.combobox4.clear()
        if selected_model:
            self.combobox4.addItem(selected_model)
            #self.combobox4.setCurrentText(selected_model)
        self.load_models_async()

    def load_models_async(self):
        if self.model_list_thread is not None:
            return

        self.combobox3.setEnabled(False)
        self.combobox4.setEnabled(False)
        self.combobox4.setToolTip("Loading available models...")

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

        self.combobox4.blockSignals(True)
        self.combobox4.clear()
        self.combobox4.addItems(models)

        if selected_model:
            self.combobox4.setCurrentText(selected_model)

        self.combobox4.blockSignals(False)
        self.combobox4.setToolTip("")

    @Slot(str)
    def model_loading_failed(self, message: str):
        self.combobox4.setToolTip(f"Could not load available models: {message}")

    @Slot()
    def model_loading_finished(self):
        self.model_list_thread = None
        self.combobox3.setEnabled(True)
        self.combobox4.setEnabled(True)


    @Slot(str)
    def model_changed(self, model_name: str):
        settings = self.settings_manager.settings
        provider_name = settings.provider_name.value

        if provider_name not in settings.allowed_providers:
            return

        settings.allowed_providers[provider_name]["model"].value = model_name

    #@Slot(str)
    #def provider_changed(self, model_name: str):
    #    settings = self.settings_manager.settings
    #    provider_name = settings.provider_name.value

    #    if provider_name not in settings.allowed_providers:
    #        return

    #    model_setting = settings.allowed_providers[provider_name]["model"]
    #    model_setting.value = model_name

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, widget):
        super().__init__()
        self.setWindowTitle("Py Polyglot")

        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("File")
        #self.edit_menu = self.menu.addMenu("Edit")
        self.tool_menu = self.menu.addMenu("Tools")

        #new_action = self.file_menu.addAction("New", widget.new_note)
        #new_action.setShortcut("Ctrl+N")

        #save_action = self.file_menu.addAction("Save", widget.save_note)
        #save_action.setShortcut("Ctrl+S")

        quit_action = self.file_menu.addAction("Quit", self.close)
        quit_action.setShortcut("Ctrl+Q")

        #self.edit_menu.addAction("Delete", widget.delete_note)

        translate_action = self.tool_menu.addAction("Translate", widget.translate_text)
        translate_action.setShortcut("Ctrl+T")

        self.setCentralWidget(widget)
