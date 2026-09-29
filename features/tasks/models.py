from dataclasses import dataclass
from datetime import datetime


@dataclass
class Task:
    id: int
    user_id: int
    title: str
    priority: int
    completed: bool = False
    deadline: datetime | None = None
    reminder: datetime | None = None

    def __pos__init__(self) -> None:
        self.title = self.title.strip()
        if not self.title:
            raise ValueError("Title cannot be blank.")
