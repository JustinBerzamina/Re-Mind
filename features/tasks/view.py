from datetime import datetime

from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QAbstractItemView,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QCheckBox,
)

from features.tasks.models import Task
from features.tasks.service import TaskService


class TaskView(QWidget):
    """Two switchable task tables, with actions in a right-side column."""

    def __init__(self, service: TaskService, user_id: int):
        super().__init__()
        self.setObjectName("taskView")
        self.service = service
        self.user_id = user_id
        self.tasks: dict[int, Task] = {}
        self.build_ui()
        self.load_tasks()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        heading = QLabel("My Tasks")
        heading.setObjectName("heading")
        layout.addWidget(heading)
        layout.addWidget(QLabel("Switch between pending and completed tasks."))

        controls = QHBoxLayout()
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Deadline", "deadline")
        self.sort_combo.addItem("Priority", "priority")
        self.sort_combo.addItem("Title", "title")
        self.sort_combo.currentIndexChanged.connect(self.load_tasks)
        controls.addWidget(QLabel("Sort by:"))
        controls.addWidget(self.sort_combo)
        controls.addStretch()
        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("secondaryButton")
        refresh_button.clicked.connect(self.load_tasks)
        controls.addWidget(refresh_button)
        layout.addLayout(controls)

        content = QHBoxLayout()
        content.setSpacing(14)
        self.tabs = QTabWidget()
        self.pending_table = self._create_table()
        self.completed_table = self._create_table()
        self.tabs.addTab(self.pending_table, "Pending Tasks")
        self.tabs.addTab(self.completed_table, "Completed Tasks")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        content.addWidget(self.tabs, 1)

        buttons = QVBoxLayout()
        buttons.setSpacing(10)
        self.add_button = QPushButton("Add Task")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.add_task)
        buttons.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit Task")
        self.edit_button.setObjectName("secondaryButton")
        self.edit_button.clicked.connect(self.edit_selected_task)
        buttons.addWidget(self.edit_button)

        self.toggle_button = QPushButton("Complete Task")
        self.toggle_button.setObjectName("secondaryButton")
        self.toggle_button.clicked.connect(self.toggle_selected_task)
        buttons.addWidget(self.toggle_button)

        self.delete_button = QPushButton("Delete Task")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.clicked.connect(self.delete_selected_task)
        buttons.addWidget(self.delete_button)
        buttons.addStretch()
        content.addLayout(buttons)
        layout.addLayout(content, 1)
        self._on_tab_changed(0)

    def _create_table(self) -> QTableWidget:
        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(
            ["Title", "Description", "Priority", "Deadline", "Urgency"]
        )
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.cellDoubleClicked.connect(self.edit_selected_task)
        return table

    def _on_tab_changed(self, index: int):
        # Only the currently visible table can be acted on.
        self.pending_table.clearSelection()
        self.completed_table.clearSelection()
        self.toggle_button.setText("Complete Task" if index == 0 else "Reopen Task")

    def _active_table(self) -> QTableWidget:
        return self.pending_table if self.tabs.currentIndex() == 0 else self.completed_table

    def _populate_table(self, table: QTableWidget, tasks: list[Task]):
        table.setRowCount(0)
        for task in tasks:
            if task.id is None:
                continue
            row = table.rowCount()
            table.insertRow(row)
            deadline = (
                task.deadline.strftime("%b %d, %Y - %I:%M %p")
                if task.deadline else "No deadline"
            )
            values = [
                task.title,
                task.description,
                task.priority.capitalize(),
                deadline,
                self.service.get_urgency(task).capitalize(),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole, task.id)
                if task.description and column == 1:
                    item.setToolTip(task.description)
                table.setItem(row, column, item)
        table.clearSelection()

    def load_tasks(self):
        try:
            tasks = self.service.get_tasks(self.user_id)
            tasks = self.service.sort_tasks(tasks, self.sort_combo.currentData())
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Unable to Load Tasks", str(error))
            return

        self.tasks = {task.id: task for task in tasks if task.id is not None}
        pending = [task for task in tasks if not task.is_completed]
        completed = [task for task in tasks if task.is_completed]
        self._populate_table(self.pending_table, pending)
        self._populate_table(self.completed_table, completed)
        self.tabs.setTabText(0, f"Pending Tasks ({len(pending)})")
        self.tabs.setTabText(1, f"Completed Tasks ({len(completed)})")

    def add_task(self):
        dialog = TaskDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_task_data()
        try:
            self.service.create_task(
                user_id=self.user_id,
                title=data["title"],
                description=data["description"],
                deadline=data["deadline"],
                priority=data["priority"],
            )
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Task Creation Failed", str(error))
            return
        self.load_tasks()
        self.tabs.setCurrentIndex(0)

    def edit_selected_task(self, *_args):
        task = self._get_selected_task()
        if task is None or task.id is None:
            return
        dialog = TaskDialog(self, task)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_task_data()
        try:
            self.service.update_task(
                task_id=task.id,
                user_id=self.user_id,
                title=data["title"],
                description=data["description"],
                deadline=data["deadline"],
                priority=data["priority"],
            )
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Task Update Failed", str(error))
            return
        self.load_tasks()

    def delete_selected_task(self):
        task = self._get_selected_task()
        if task is None or task.id is None:
            return
        answer = QMessageBox.question(
            self, "Delete Task", f'Delete "{task.title}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.service.delete_task(task.id, self.user_id)
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Task Deletion Failed", str(error))
            return
        self.load_tasks()

    def toggle_selected_task(self):
        task = self._get_selected_task()
        if task is None or task.id is None:
            return
        try:
            self.service.toggle_task_status(task.id, self.user_id)
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Task Update Failed", str(error))
            return
        self.load_tasks()

    def _get_selected_task(self) -> Task | None:
        table = self._active_table()
        row = table.currentRow()
        if row < 0 or not table.selectionModel().isRowSelected(row, table.rootIndex()):
            QMessageBox.information(self, "No Task Selected", "Please select a task first.")
            return None
        item = table.item(row, 0)
        if item is None:
            return None
        task_id = item.data(Qt.ItemDataRole.UserRole)
        return self.tasks.get(task_id)


class TaskDialog(QDialog):
    def __init__(
        self,
        parent=None,
        task: Task | None = None,
    ):
        super().__init__(parent)

        self.setObjectName("taskDialog")
        self.task = task

        if task is None:
            self.setWindowTitle("Add Task")
        else:
            self.setWindowTitle("Edit Task")

        self.setMinimumWidth(400)
        self.build_ui()

        if task is not None:
            self.load_task(task)

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        form = QFormLayout()

        # Title
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter task title")
        form.addRow("Title", self.title_input)

        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText(
            "Enter task description"
        )
        self.description_input.setMaximumHeight(100)
        form.addRow("Description", self.description_input)

        # Priority
        self.priority_input = QComboBox()
        self.priority_input.addItem("Low", "low")
        self.priority_input.addItem("Medium", "medium")
        self.priority_input.addItem("High", "high")
        self.priority_input.setCurrentIndex(1)
        form.addRow("Priority", self.priority_input)

        # Deadline input must be created BEFORE the checkbox connection.
        self.deadline_input = QDateTimeEdit()
        self.deadline_input.setCalendarPopup(True)
        self.deadline_input.setDisplayFormat(
            "MMM dd, yyyy - hh:mm AP"
        )
        self.deadline_input.setDateTime(
            QDateTime.currentDateTime().addDays(1)
        )

        # Optional deadline checkbox
        self.has_deadline = QCheckBox("Set deadline")
        self.has_deadline.setChecked(True)
        self.has_deadline.toggled.connect(
            self.deadline_input.setEnabled
        )

        form.addRow("", self.has_deadline)
        form.addRow("Deadline", self.deadline_input)

        layout.addLayout(form)

        # Buttons
        buttons = QHBoxLayout()

        save_button = QPushButton("Save Task")
        save_button.setObjectName("primaryButton")
        save_button.clicked.connect(self.accept)
        buttons.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("secondaryButton")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(cancel_button)

        layout.addLayout(buttons)

    def load_task(self, task: Task):
        self.title_input.setText(task.title)
        self.description_input.setPlainText(task.description)

        priority_index = self.priority_input.findData(
            task.priority
        )

        if priority_index >= 0:
            self.priority_input.setCurrentIndex(
                priority_index
            )

        if task.deadline is not None:
            self.has_deadline.setChecked(True)

            self.deadline_input.setDateTime(
                QDateTime(
                    task.deadline.year,
                    task.deadline.month,
                    task.deadline.day,
                    task.deadline.hour,
                    task.deadline.minute,
                )
            )
        else:
            self.has_deadline.setChecked(False)

    def get_task_data(self) -> dict:
        python_deadline = None

        if self.has_deadline.isChecked():
            deadline = self.deadline_input.dateTime()

            python_deadline = datetime(
                deadline.date().year(),
                deadline.date().month(),
                deadline.date().day(),
                deadline.time().hour(),
                deadline.time().minute(),
            )

        return {
            "title": self.title_input.text(),
            "description": self.description_input.toPlainText(),
            "priority": self.priority_input.currentData(),
            "deadline": python_deadline,
        }