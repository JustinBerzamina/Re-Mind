from datetime import datetime

from database.database import Database
from features.tasks.models import Task


class TaskRepository:
    """Handles persistence operations for tasks."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def add(self, task: Task) -> Task:
        """Add a task to the database and return it with its generated ID."""
        query = """
            INSERT INTO tasks (
                user_id,
                title,
                description,
                deadline,
                priority,
                is_completed
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """

        deadline = task.deadline.isoformat() if task.deadline else None

        with self.database.connect() as connection:
            cursor = connection.execute(
                query,
                (
                    task.user_id,
                    task.title,
                    task.description,
                    deadline,
                    task.priority,
                    int(task.is_completed),
                ),
            )

            task.id = cursor.lastrowid

        return task

    def get_by_user_id(self, user_id: int) -> list[Task]:
        """Return all tasks belonging to a specific user."""
        query = """
            SELECT
                id,
                user_id,
                title,
                description,
                deadline,
                priority,
                is_completed
            FROM tasks
            WHERE user_id = ?
        """

        with self.database.connect() as connection:
            rows = connection.execute(query, (user_id,)).fetchall()

        return [self._row_to_task(row) for row in rows]

    def get_by_id(self, task_id: int, user_id: int) -> Task | None:
        """Return a task if it belongs to the specified user."""
        query = """
            SELECT
                id,
                user_id,
                title,
                description,
                deadline,
                priority,
                is_completed
            FROM tasks
            WHERE id = ? AND user_id = ?
        """

        with self.database.connect() as connection:
            row = connection.execute(
                query,
                (task_id, user_id),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_task(row)

    def update(self, task: Task) -> bool:
        """Update a task if it belongs to the specified user."""
        if task.id is None:
            return False

        query = """
            UPDATE tasks
            SET
                title = ?,
                description = ?,
                deadline = ?,
                priority = ?,
                is_completed = ?
            WHERE id = ? AND user_id = ?
        """

        deadline = task.deadline.isoformat() if task.deadline else None

        with self.database.connect() as connection:
            cursor = connection.execute(
                query,
                (
                    task.title,
                    task.description,
                    deadline,
                    task.priority,
                    int(task.is_completed),
                    task.id,
                    task.user_id,
                ),
            )

        return cursor.rowcount > 0

    def delete(self, task_id: int, user_id: int) -> bool:
        """Delete a task if it belongs to the specified user."""
        query = """
            DELETE FROM tasks
            WHERE id = ? AND user_id = ?
        """

        with self.database.connect() as connection:
            cursor = connection.execute(
                query,
                (task_id, user_id),
            )

        return cursor.rowcount > 0

    def toggle_status(self, task_id: int, user_id: int) -> bool:
        """Toggle a task between completed and incomplete."""
        query = """
            UPDATE tasks
            SET is_completed =
                CASE
                    WHEN is_completed = 0 THEN 1
                    ELSE 0
                END
            WHERE id = ? AND user_id = ?
        """

        with self.database.connect() as connection:
            cursor = connection.execute(
                query,
                (task_id, user_id),
            )

        return cursor.rowcount > 0

    @staticmethod
    def _row_to_task(row) -> Task:
        """Convert a SQLite row into a Task object."""
        deadline = (
            datetime.fromisoformat(row["deadline"])
            if row["deadline"]
            else None
        )

        return Task(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            description=row["description"],
            deadline=deadline,
            priority=row["priority"],
            is_completed=bool(row["is_completed"]),
        )