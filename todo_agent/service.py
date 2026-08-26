from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from .models import Task
from .storage import TodoRepository


@dataclass(frozen=True)
class AgentResult:
    message: str
    task: Task | None = None


class TodoService:
    """Application API shared by the GUI and future messaging adapters."""

    def __init__(self, repository: TodoRepository) -> None:
        self.repository = repository

    def add_task(self, title: str, section: str = "Inbox", due_date: date | None = None, priority: str = "normal") -> Task:
        return self.repository.add_task(title, section, due_date, self._validate_priority(priority))

    def list_sections(self) -> list[dict[str, object]]:
        return [{"id": section.id, "name": section.name, "position": section.position} for section in self.repository.sections()]

    def list_tasks(self, section: str | None = None, include_completed: bool = False) -> list[dict[str, object]]:
        section_id = None
        if section is not None:
            match = next((item for item in self.repository.sections() if item.name.casefold() == section.casefold()), None)
            if match is None:
                raise ValueError(f"Section '{section}' does not exist.")
            section_id = match.id
        section_names = {item.id: item.name for item in self.repository.sections()}
        return [self.task_to_dict(task, section_names) for task in self.repository.tasks(section_id, include_completed)]

    def update_task(
        self,
        task_id: int,
        *,
        title: str | None = None,
        section: str | None = None,
        due_date: date | None = None,
        clear_due_date: bool = False,
        priority: str | None = None,
    ) -> dict[str, object]:
        task = self.repository.update_task(task_id, title=title, section_name=section, due_date=due_date, clear_due_date=clear_due_date, priority=self._validate_priority(priority) if priority is not None else None)
        return self.serialize_task(task)

    def set_completed(self, task_id: int, completed: bool = True) -> dict[str, object]:
        self.repository.set_completed(task_id, completed)
        return self.serialize_task(self.repository.task(task_id))

    def delete_task(self, task_id: int) -> dict[str, object]:
        task = self.repository.task(task_id)
        result = self.serialize_task(task)
        self.repository.delete_task(task_id)
        return result

    @staticmethod
    def parse_due_date(value: str | None) -> date | None:
        if value is None:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError as error:
            raise ValueError("due_date must use YYYY-MM-DD format.") from error

    @staticmethod
    def task_to_dict(task: Task, section_names: dict[int, str] | None = None) -> dict[str, object]:
        if section_names is None:
            section_names = {}
        return {"id": task.id, "title": task.title, "section_id": task.section_id, "section": section_names.get(task.section_id), "completed": task.completed, "due_date": task.due_date.isoformat() if task.due_date else None, "priority": task.priority, "created_at": task.created_at}

    def serialize_task(self, task: Task) -> dict[str, object]:
        return self.task_to_dict(task, {section.id: section.name for section in self.repository.sections()})

    @staticmethod
    def _validate_priority(priority: str) -> Literal["high", "normal", "low"]:
        normalized = priority.lower().strip()
        if normalized not in {"high", "normal", "low"}:
            raise ValueError("priority must be one of: high, normal, low.")
        return normalized  # type: ignore[return-value]

    def process_message(self, text: str) -> AgentResult:
        """Parse predictable messages: add Buy milk #Personal tomorrow !high; list Work."""
        text = text.strip()
        if text.lower().startswith("list"):
            section_name = text[4:].strip()
            section = next((item for item in self.repository.sections() if item.name.lower() == section_name.lower()), None)
            tasks = self.repository.tasks(section.id if section else None, include_completed=False)
            return AgentResult("; ".join(task.title for task in tasks) or "No open tasks.")
        if text.lower().startswith("add "):
            text = text[4:].strip()
        section_match = re.search(r"#([^#!]+?)(?=\s(?:tomorrow|today|!\w+)|$)", text, re.IGNORECASE)
        section = section_match.group(1).strip() if section_match else "Inbox"
        if section_match:
            text = text[:section_match.start()] + text[section_match.end():]
        priority_match = re.search(r"!(high|normal|low)\b", text, re.IGNORECASE)
        priority = priority_match.group(1).lower() if priority_match else "normal"
        if priority_match:
            text = text[:priority_match.start()] + text[priority_match.end():]
        due_date = None
        if re.search(r"\btoday\b", text, re.IGNORECASE):
            due_date, text = date.today(), re.sub(r"\btoday\b", "", text, flags=re.IGNORECASE)
        elif re.search(r"\btomorrow\b", text, re.IGNORECASE):
            due_date, text = date.today() + timedelta(days=1), re.sub(r"\btomorrow\b", "", text, flags=re.IGNORECASE)
        task = self.add_task(re.sub(r"\s+", " ", text).strip(), section, due_date, priority)
        return AgentResult(f"Added '{task.title}' to {section}.", task)
