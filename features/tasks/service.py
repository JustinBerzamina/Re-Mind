from datetime import datetime

from features.tasks.models import Task
from features.tasks.repository import TaskRepository


class TaskService:
    """Handles task validation and business logic."""

    VALID_PRIORITIES = {"low", "medium", "high"}

    PRIORITY_ORDER = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def create_task(
        self,
        user_id: int,
        title: str,
        description: str = "",
        deadline: datetime | None = None,
        priority: str = "medium",
    ) -> Task:
        """Validate and create a new task."""
        title = self._validate_title(title)
        priority = self._validate_priority(priority)
        self._validate_deadline(deadline)

        task = Task(
            id=None,
            user_id=user_id,
            title=title,
            description=description.strip(),
            deadline=deadline,
            priority=priority,
            is_completed=False,
        )

        return self.repository.add(task)

    def get_tasks(self, user_id: int) -> list[Task]:
        """Return all tasks belonging to a user."""
        return self.repository.get_by_user_id(user_id)

    def get_task(self, task_id: int, user_id: int) -> Task | None:
        """Return a specific task belonging to a user."""
        return self.repository.get_by_id(task_id, user_id)

    def update_task(
        self,
        task_id: int,
        user_id: int,
        title: str,
        description: str,
        deadline: datetime | None,
        priority: str,
    ) -> Task:
        """Validate and update an existing task."""
        task = self.repository.get_by_id(task_id, user_id)

        if task is None:
            raise ValueError("Task not found.")

        task.title = self._validate_title(title)
        task.description = description.strip()
        task.deadline = deadline
        task.priority = self._validate_priority(priority)

        self._validate_deadline(deadline)

        if not self.repository.update(task):
            raise RuntimeError("Failed to update task.")

        return task

    def delete_task(self, task_id: int, user_id: int) -> None:
        """Delete an existing task."""
        if not self.repository.delete(task_id, user_id):
            raise ValueError("Task not found.")

    def toggle_task_status(self, task_id: int, user_id: int) -> Task:
        """Toggle a task's completion status."""
        if not self.repository.toggle_status(task_id, user_id):
            raise ValueError("Task not found.")

        task = self.repository.get_by_id(task_id, user_id)

        if task is None:
            raise RuntimeError("Task could not be retrieved after update.")

        return task

    def sort_tasks(
        self,
        tasks: list[Task],
        sort_by: str = "deadline",
    ) -> list[Task]:
        """Return a sorted copy of a task list."""
        if sort_by == "priority":
            return sorted(
                tasks,
                key=lambda task: self.PRIORITY_ORDER[task.priority],
            )

        if sort_by == "title":
            return sorted(
                tasks,
                key=lambda task: task.title.lower(),
            )

        if sort_by == "deadline":
            return sorted(
                tasks,
                key=lambda task: (
                    task.deadline is None,
                    task.deadline or datetime.max,
                ),
            )

        raise ValueError(f"Unsupported sorting option: {sort_by}")

    @staticmethod
    def get_urgency(task: Task) -> str:
        """Determine a task's urgency based on its deadline."""
        if task.is_completed:
            return "completed"

        if task.deadline is None:
            return "none"

        now = datetime.now()
        time_remaining = task.deadline - now

        if time_remaining.total_seconds() < 0:
            return "overdue"

        hours_remaining = time_remaining.total_seconds() / 3600

        if hours_remaining <= 24:
            return "urgent"

        if hours_remaining <= 72:
            return "soon"

        return "normal"

    @staticmethod
    def _validate_title(title: str) -> str:
        """Validate and normalize a task title."""
        title = title.strip()

        if not title:
            raise ValueError("Task title cannot be empty.")

        if len(title) > 200:
            raise ValueError(
                "Task title cannot be longer than 200 characters."
            )

        return title

    @classmethod
    def _validate_priority(cls, priority: str) -> str:
        """Validate and normalize task priority."""
        priority = priority.strip().lower()

        if priority not in cls.VALID_PRIORITIES:
            raise ValueError(
                "Priority must be 'low', 'medium', or 'high'."
            )

        return priority

    @staticmethod
    def _validate_deadline(deadline: datetime | None) -> None:
        """Validate a task deadline."""
        if deadline is not None and deadline <= datetime.now():
            raise ValueError("Deadline must be in the future.")