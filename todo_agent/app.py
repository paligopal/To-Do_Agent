from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QComboBox, QDateEdit, QFrame, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QSplitter, QVBoxLayout, QWidget

from .service import TodoService
from .storage import TodoRepository


APP_STYLES = """
QMainWindow { background: #f6f7fb; }
QWidget { font-family: 'Segoe UI', Arial; font-size: 15px; color: #1d2433; }
QFrame#sidebar, QFrame#content, QFrame#composer { background: white; border: 1px solid #e6e9f0; border-radius: 14px; }
QLabel#appTitle { font-size: 28px; font-weight: 700; color: #18243a; }
QLabel#subtitle, QLabel#hint { color: #6b7280; font-size: 14px; }
QLabel#sectionTitle { font-size: 23px; font-weight: 700; }
QLineEdit, QComboBox, QDateEdit { background: #fff; border: 1px solid #d9deea; border-radius: 9px; min-height: 38px; padding: 2px 10px; }
QLineEdit { font-size: 16px; }
QLineEdit:focus, QComboBox:focus, QDateEdit:focus { border: 2px solid #5b6ee1; }
QPushButton { border: none; border-radius: 9px; padding: 9px 14px; font-weight: 600; min-height: 20px; }
QPushButton#primary { background: #4f61d7; color: white; font-size: 15px; }
QPushButton#primary:hover { background: #4051c4; }
QPushButton#secondary { background: #eef0fb; color: #3e4fb8; }
QPushButton#filter:checked { background: #dfe4ff; color: #3747ae; }
QListWidget { border: none; background: transparent; outline: none; }
QListWidget#sections::item { border-radius: 8px; padding: 11px 10px; margin: 2px 0; }
QListWidget#sections::item:selected { background: #e8ebff; color: #3343ac; font-weight: 700; }
QListWidget#tasks::item { background: white; border: 1px solid #e8eaf0; border-radius: 10px; margin: 4px 2px; padding: 8px 12px; }
QListWidget#tasks::item:hover { border-color: #bec7f5; background: #fbfcff; }
"""


class TodoWindow(QMainWindow):
    def __init__(self, service: TodoService) -> None:
        super().__init__()
        self.service = service
        self.setWindowTitle("To-Do Agent")
        self.resize(1080, 700)
        self.setMinimumSize(860, 570)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        root = QWidget(); root_layout = QVBoxLayout(root); root_layout.setContentsMargins(26, 22, 26, 24); root_layout.setSpacing(18)
        header = QHBoxLayout(); heading = QVBoxLayout()
        title = QLabel("To-Do Agent"); title.setObjectName("appTitle")
        subtitle = QLabel("Your focused, local task space"); subtitle.setObjectName("subtitle")
        heading.addWidget(title); heading.addWidget(subtitle); header.addLayout(heading); header.addStretch()
        self.done_filter = QPushButton("Hide completed"); self.done_filter.setObjectName("filter"); self.done_filter.setCheckable(True); self.done_filter.toggled.connect(self.refresh_tasks); header.addWidget(self.done_filter)
        root_layout.addLayout(header)
        splitter = QSplitter(Qt.Orientation.Horizontal); splitter.setChildrenCollapsible(False)
        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar_layout = QVBoxLayout(sidebar); sidebar_layout.setContentsMargins(15, 17, 15, 15); sidebar_layout.setSpacing(10)
        sidebar_label = QLabel("SECTIONS"); sidebar_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #8790a1;"); sidebar_layout.addWidget(sidebar_label)
        self.section_list = QListWidget(); self.section_list.setObjectName("sections"); self.section_list.currentItemChanged.connect(lambda *_: self.refresh_tasks()); sidebar_layout.addWidget(self.section_list)
        new_section = QPushButton("+  New section"); new_section.setObjectName("secondary"); new_section.clicked.connect(self.add_section); sidebar_layout.addWidget(new_section)
        content = QFrame(); content.setObjectName("content"); content_layout = QVBoxLayout(content); content_layout.setContentsMargins(22, 20, 22, 20); content_layout.setSpacing(14)
        task_header = QHBoxLayout(); self.section_title = QLabel("Inbox"); self.section_title.setObjectName("sectionTitle"); self.task_count = QLabel(); self.task_count.setObjectName("subtitle"); task_header.addWidget(self.section_title); task_header.addWidget(self.task_count); task_header.addStretch(); content_layout.addLayout(task_header)
        composer = QFrame(); composer.setObjectName("composer"); composer_layout = QVBoxLayout(composer); composer_layout.setContentsMargins(13, 13, 13, 13); composer_layout.setSpacing(9)
        self.task_input = QLineEdit(); self.task_input.setPlaceholderText("What needs doing?"); self.task_input.returnPressed.connect(self.add_task); composer_layout.addWidget(self.task_input)
        task_controls = QHBoxLayout(); self.priority_box = QComboBox(); self.priority_box.addItems(["normal", "high", "low"]); self.priority_box.setMinimumWidth(120)
        self.due_edit = QDateEdit(); self.due_edit.setCalendarPopup(True); self.due_edit.setSpecialValueText("No due date"); self.due_edit.setMinimumDate(date(2000, 1, 1)); self.due_edit.setDate(date(2000, 1, 1)); self.due_edit.setMinimumWidth(150)
        add_button = QPushButton("Add task"); add_button.setObjectName("primary"); add_button.clicked.connect(self.add_task)
        task_controls.addWidget(QLabel("Priority")); task_controls.addWidget(self.priority_box); task_controls.addSpacing(8); task_controls.addWidget(QLabel("Due")); task_controls.addWidget(self.due_edit); task_controls.addStretch(); task_controls.addWidget(add_button); composer_layout.addLayout(task_controls); content_layout.addWidget(composer)
        self.tasks = QListWidget(); self.tasks.setObjectName("tasks"); self.tasks.itemChanged.connect(self.toggle_task); self.tasks.itemDoubleClicked.connect(self.delete_task); content_layout.addWidget(self.tasks)
        hint = QLabel("Tick a task when it is done. Double-click a task to delete it."); hint.setObjectName("hint"); content_layout.addWidget(hint)
        splitter.addWidget(sidebar); splitter.addWidget(content); splitter.setSizes([250, 760]); root_layout.addWidget(splitter); self.setCentralWidget(root)

    def current_section(self):
        item = self.section_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def refresh(self) -> None:
        current_name = self.current_section().name if self.current_section() else "Inbox"
        self.section_list.blockSignals(True); self.section_list.clear()
        for section in self.service.repository.sections():
            item = QListWidgetItem(section.name); item.setData(Qt.ItemDataRole.UserRole, section); self.section_list.addItem(item)
            if section.name == current_name: self.section_list.setCurrentItem(item)
        if not self.section_list.currentItem() and self.section_list.count(): self.section_list.setCurrentRow(0)
        self.section_list.blockSignals(False); self.refresh_tasks()

    def refresh_tasks(self) -> None:
        section = self.current_section()
        if section is None: return
        visible = self.service.repository.tasks(section.id, include_completed=not self.done_filter.isChecked()); open_count = sum(not task.completed for task in self.service.repository.tasks(section.id))
        self.section_title.setText(section.name); self.task_count.setText(f"{open_count} open task{'s' if open_count != 1 else ''}")
        self.tasks.blockSignals(True); self.tasks.clear()
        for task in visible:
            detail = []
            if task.due_date: detail.append(f"Due {task.due_date:%d %b}")
            if task.priority != "normal": detail.append(f"{task.priority.title()} priority")
            label = task.title + ("\n" + "  |  ".join(detail) if detail else "")
            item = QListWidgetItem(label); item.setData(Qt.ItemDataRole.UserRole, task.id); item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable); item.setCheckState(Qt.CheckState.Checked if task.completed else Qt.CheckState.Unchecked); self.tasks.addItem(item)
        self.tasks.blockSignals(False)

    def add_task(self) -> None:
        section = self.current_section()
        if section is None: return
        try:
            due = self.due_edit.date().toPyDate(); self.service.add_task(self.task_input.text(), section.name, None if due.year == 2000 else due, self.priority_box.currentText())
        except ValueError as error:
            QMessageBox.warning(self, "Cannot add task", str(error)); return
        self.task_input.clear(); self.task_input.setFocus(); self.refresh_tasks()

    def add_section(self) -> None:
        name, accepted = QInputDialog.getText(self, "New section", "Section name:")
        if not accepted: return
        try: self.service.repository.get_or_create_section(name)
        except ValueError as error: QMessageBox.warning(self, "Cannot add section", str(error)); return
        self.refresh()
        for index in range(self.section_list.count()):
            if self.section_list.item(index).text().lower() == name.strip().lower(): self.section_list.setCurrentRow(index); break

    def toggle_task(self, item: QListWidgetItem) -> None:
        self.service.repository.set_completed(item.data(Qt.ItemDataRole.UserRole), item.checkState() == Qt.CheckState.Checked); self.refresh_tasks()

    def delete_task(self, item: QListWidgetItem) -> None:
        task_name = item.text().split("\n", 1)[0]
        if QMessageBox.question(self, "Delete task", f"Delete '{task_name}'?") == QMessageBox.StandardButton.Yes:
            self.service.repository.delete_task(item.data(Qt.ItemDataRole.UserRole)); self.refresh_tasks()

    def closeEvent(self, event) -> None:
        self.service.repository.close(); event.accept()


def main() -> None:
    app = QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(APP_STYLES)
    window = TodoWindow(TodoService(TodoRepository(Path.home() / ".todo_agent" / "todo.db")))
    window.show(); sys.exit(app.exec())
