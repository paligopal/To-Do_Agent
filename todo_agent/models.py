from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Section:
    id: int
    name: str
    position: int


@dataclass(frozen=True)
class Task:
    id: int
    title: str
    section_id: int
    completed: bool
    due_date: date | None
    priority: str
    created_at: str
