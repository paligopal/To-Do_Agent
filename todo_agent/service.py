from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

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
        return self.repository.add_task(title, section, due_date, priority)

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
