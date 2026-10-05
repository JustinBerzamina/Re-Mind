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
    QListWidget,
    QListWidgetItem,
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
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        heading = QLabel("My Tasks")
        heading.setObjectName("heading")
        layout.addWidget(heading)

        layout.addWidget(QLabel("Create and manage your tasks."))

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

        self.task_list = QListWidget()
        self.task_list.itemDoubleClicked.connect(self.edit_selected_task)
        layout.addWidget(self.task_list)

        buttons = QHBoxLayout()

        add_button = QPushButton("Add Task")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self.add_task)
        buttons.addWidget(add_button)

        edit_button = QPushButton("Edit Task")
        edit_button.setObjectName("secondaryButton")
        edit_button.clicked.connect(self.edit_selected_task)
        buttons.addWidget(edit_button)

        toggle_button = QPushButton("Complete / Reopen")
        toggle_button.setObjectName("secondaryButton")
        toggle_button.clicked.connect(self.toggle_selected_task)
        buttons.addWidget(toggle_button)

        delete_button = QPushButton("Delete Task")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self.delete_selected_task)
        buttons.addWidget(delete_button)

        layout.addLayout(buttons)

    def load_tasks(self):
        try:
            tasks = self.service.get_tasks(self.user_id)

            sort_by = self.sort_combo.currentData()
            tasks = self.service.sort_tasks(tasks, sort_by)

        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(
                self,
                "Unable to Load Tasks",
                str(error),
            )
            return

        self.task_list.clear()
        self.tasks.clear()

        for task in tasks:
            if task.id is None:
                continue

            self.tasks[task.id] = task

            urgency = self.service.get_urgency(task)
            text = self._format_task(task, urgency)

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, task.id)

            self.task_list.addItem(item)

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
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Task Creation Failed",
                str(error),
            )
            return

        self.load_tasks()

    def edit_selected_task(self):
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
            QMessageBox.warning(
                self,
                "Task Update Failed",
                str(error),
            )
            return

        self.load_tasks()

    def delete_selected_task(self):
        task = self._get_selected_task()

        if task is None or task.id is None:
            return

        answer = QMessageBox.question(
            self,
            "Delete Task",
            f'Delete "{task.title}"?',
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.service.delete_task(task.id, self.user_id)
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Task Deletion Failed",
                str(error),
            )
            return

        self.load_tasks()

    def toggle_selected_task(self):
        task = self._get_selected_task()

        if task is None or task.id is None:
            return

        try:
            self.service.toggle_task_status(
                task.id,
                self.user_id,
            )
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(
                self,
                "Task Update Failed",
                str(error),
            )
            return

        self.load_tasks()

    def _get_selected_task(self) -> Task | None:
        item = self.task_list.currentItem()

        if item is None:
            QMessageBox.information(
                self,
                "No Task Selected",
                "Please select a task first.",
            )
            return None

        task_id = item.data(Qt.ItemDataRole.UserRole)
        return self.tasks.get(task_id)

    @staticmethod
    def _format_task(task: Task, urgency: str) -> str:
        status = "Completed" if task.is_completed else "Pending"
        priority = task.priority.capitalize()

        if task.deadline:
            deadline = task.deadline.strftime("%b %d, %Y - %I:%M %p")
        else:
            deadline = "No deadline"

        return (
            f"{task.title}\n"
            f"{priority} priority | {deadline} | "
            f"{status} | {urgency.capitalize()}"
        )


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