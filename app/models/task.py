from dataclasses import dataclass
from typing import Optional


@dataclass
class Task:
    id: Optional[int]
    title: str
    description: str = ""
    status: str = "todo"
    priority: int = 2
    due_date: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    completed_at: Optional[str] = None
