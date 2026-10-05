from dataclasses import dataclass
from datetime import datetime


@dataclass
class Task:
    id: int | None
    user_id: int
    title: str
    description: str
    deadline: datetime | None
    priority: str
    is_completed: bool = False