import random
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from PySide6 import QtWidgets
from PySide6.QtCore import QProcess, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


def current_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class Note:
    id: int
    file_name: str
    body: str
    created_at: str = field(default_factory=current_timestamp)
    updated_at: str = field(default_factory=current_timestamp)

    def update_timestamp(self) -> None:
        self.updated_at = current_timestamp()


class Widget(QWidget):
    def __init__(self):
        super().__init__()

        self.notes_dir = Path("notes")
        self.notes_dir.mkdir(exist_ok=True)
        self.notes = [
            Note(note_id, file.name, file.read_text())
            for note_id, file in enumerate(self.notes_dir.iterdir())
            if file.is_file()
        ]
        self.next_id = len(self.notes)
        self.process: QProcess | None = None

        self.notes_list = QListWidget()
        self.refresh_notes_list()
        self.note_file_name_edit = QLineEdit()
        self.body_edit = QTextEdit()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search notes...")
        self.translation_output = QTextEdit()
        self.translation_output.setReadOnly(True)
        self.translation_output.setMaximumHeight(65)

        self.left = QVBoxLayout()
        self.left.addWidget(QLabel("Files"))
        self.left.addWidget(self.search_edit)
        self.left.addWidget(self.notes_list)
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
        self.notes_list.currentRowChanged.connect(self.select_note)
        self.save.clicked.connect(self.save_note)
        self.delete.clicked.connect(self.delete_note)
        self.search_edit.textChanged.connect(self.filter_notes)

        self.main = QHBoxLayout()
        self.main.addLayout(self.left, 3)
        self.main.addLayout(self.right, 7)

        self.setLayout(self.main)

    @Slot()
    def new_note(self):
        num = random.randint(1, 100000)
        note = Note(
            self.next_note_id(),
            f"tmp{num}.txt",
            f"{[x for x in range(random.randint(1, 100))]}",
        )
        self.notes.append(note)
        self.notes_list.addItem(note.file_name)
        self.notes_list.setCurrentRow(len(self.notes) - 1)

    @Slot(int)
    def select_note(self, row):
        if row < 0 or row >= len(self.notes):
            return

        note = self.notes[row]
        self.note_file_name_edit.setText(note.file_name)
        self.body_edit.setPlainText(note.body)

    @Slot()
    def save_note(self):
        current_row = self.notes_list.currentRow()
        file_name = self.note_file_name_edit.text()
        body = self.body_edit.toPlainText()
        new_path = self.notes_dir / file_name

        if current_row >= 0:
            old_file_name = self.notes[current_row].file_name
            old_path = self.notes_dir / old_file_name

            if old_file_name != file_name and old_path.exists():
                old_path.rename(new_path)

            new_path.write_text(body)

            self.notes[current_row].file_name = file_name
            self.notes[current_row].body = body
            self.notes[current_row].update_timestamp()
            row_to_select = current_row
        else:
            new_path.write_text(body)
            self.notes.append(Note(self.next_note_id(), file_name, body))
            row_to_select = len(self.notes) - 1

        self.refresh_notes_list()
        self.notes_list.setCurrentRow(row_to_select)

    @Slot()
    def delete_note(self):
        current_row = self.notes_list.currentRow()
        if current_row >= 0:
            (self.notes_dir / self.notes[current_row].file_name).unlink()
            del self.notes[current_row]

        self.refresh_notes_list()
        self.body_edit.clear()
        self.note_file_name_edit.clear()

    @Slot(str)
    def filter_notes(self, text):
        text = text.lower()

        for row, note in enumerate(self.notes):
            matches = text in note.file_name.lower() or text in note.body.lower()

            item = self.notes_list.item(row)
            item.setHidden(not matches)

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

    def refresh_notes_list(self):
        self.notes_list.clear()

        for note in self.notes:
            self.notes_list.addItem(note.file_name)

    def next_note_id(self) -> int:
        note_id = self.next_id
        self.next_id += 1
        return note_id


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
