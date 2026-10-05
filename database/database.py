import sqlite3
from pathlib import Path


class Database:
    def __init__(self, database_path: str | Path = "remind.db"):
        self.database_path = Path(database_path)
        self._connection: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self.database_path == Path(":memory:"):
            if self._connection is None:
                self._connection = sqlite3.connect(self.database_path)
                self._connection.row_factory = sqlite3.Row
                self._connection.execute("PRAGMA foreign_keys = ON;")
            return self._connection

        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection

    def create_tables(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    deadline TEXT,
                    priority TEXT NOT NULL DEFAULT 'medium'
                        CHECK (priority IN ('low', 'medium', 'high')),
                    is_completed INTEGER NOT NULL DEFAULT 0
                        CHECK (is_completed IN (0, 1)),
                    FOREIGN KEY (user_id)
                        REFERENCES users (id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_user_id
                    ON tasks (user_id);
                """
            )

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None