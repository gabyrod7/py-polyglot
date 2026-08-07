import random
from dataclasses import dataclass
from pathlib import Path

from PySide6 import QtWidgets
from PySide6.QtCore import QProcess, Qt, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


@dataclass
class DirectoryEntry:
    path: Path
    is_dir: bool
    body: str | None = None
    children_loaded: bool = False


class Widget(QWidget):
    def __init__(self):
        super().__init__()

        self.current_dir = Path.cwd()
        self.process: QProcess | None = None

        self.notes_tree = QTreeWidget()
        self.notes_tree.setHeaderLabel("Files")
        self.note_file_name_edit = QLineEdit()
        self.body_edit = QTextEdit()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search disabled")
        self.search_edit.setEnabled(False)
        self.translation_output = QTextEdit()
        self.translation_output.setReadOnly(True)
        self.translation_output.setMaximumHeight(65)

        self.left = QVBoxLayout()
        self.left.addWidget(QLabel("Files"))
        self.left.addWidget(self.search_edit)
        self.left.addWidget(self.notes_tree)
        self.left.addWidget(QLabel("File Name"))
        self.left.addWidget(self.note_file_name_edit)

        self.right = QVBoxLayout()
        self.right.addWidget(QLabel("Body"))
        self.right.addWidget(self.body_edit)
        self.right.addWidget(QLabel("Translation"))
        self.right.addWidget(self.translation_output)

        self.translate = QPushButton("Translate (Ctrl-T)")
        self.new = QPushButton("New (Ctrl-N)")
        self.save = QPushButton("Save (Ctrl-S)")
        self.delete = QPushButton("Delete")
        self.right.addWidget(self.translate)

        self.buttons_row = QHBoxLayout()
        self.buttons_row.addWidget(self.new)
        self.buttons_row.addWidget(self.save)
        self.buttons_row.addWidget(self.delete)
        self.right.addLayout(self.buttons_row)

        self.translate.clicked.connect(self.translate_text)
        self.new.clicked.connect(self.new_note)
        self.notes_tree.currentItemChanged.connect(self.select_entry)
        self.notes_tree.itemExpanded.connect(self.load_directory_children)
        self.save.clicked.connect(self.save_note)
        self.delete.clicked.connect(self.delete_note)

        self.main = QHBoxLayout()
        self.main.addLayout(self.left, 3)
        self.main.addLayout(self.right, 7)

        self.setLayout(self.main)
        self.load_root_directory(self.current_dir)

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
        text = self.body_edit.textCursor().selectedText().replace("\u2029", "\n")

        if not text or self.process is not None:
            return

        self.process = QProcess(self)
        self.process.finished.connect(self.process_finished)
        self.process.start("py-polyglot", ["translate", text])
        self.translation_output.setPlainText("Waiting for translation")

    def process_finished(self):
        if self.process is None:
            return

        output = self.process.readAllStandardOutput().data().decode()
        error = self.process.readAllStandardError().data().decode()

        self.translation_output.setPlainText(output or error)

        self.process.deleteLater()
        self.process = None


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, widget):
        super().__init__()
        self.setWindowTitle("Py Polyglot")

        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("File")
        self.edit_menu = self.menu.addMenu("Edit")
        self.tool_menu = self.menu.addMenu("Tools")

        new_action = self.file_menu.addAction("New", widget.new_note)
        new_action.setShortcut("Ctrl+N")

        save_action = self.file_menu.addAction("Save", widget.save_note)
        save_action.setShortcut("Ctrl+S")

        quit_action = self.file_menu.addAction("Quit", self.close)
        quit_action.setShortcut("Ctrl+Q")

        self.edit_menu.addAction("Delete", widget.delete_note)

        translate_action = self.tool_menu.addAction("Translate", widget.translate_text)
        translate_action.setShortcut("Ctrl+T")

        self.setCentralWidget(widget)
