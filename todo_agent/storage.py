from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from .models import Section, Task


DEFAULT_SECTIONS = ("Inbox", "Work", "Personal")


class TodoRepository:
    """SQLite persistence. All mutations are deliberately kept in this layer."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self._create_schema()
        self._seed_sections()

    def close(self) -> None:
        self.connection.close()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS sections (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                position INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
                completed INTEGER NOT NULL DEFAULT 0,
                due_date TEXT,
                priority TEXT NOT NULL DEFAULT 'normal',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        self.connection.commit()

    def _seed_sections(self) -> None:
        if self.connection.execute("SELECT COUNT(*) FROM sections").fetchone()[0]:
            return
        self.connection.executemany(
            "INSERT INTO sections(name, position) VALUES (?, ?)",
            [(name, index) for index, name in enumerate(DEFAULT_SECTIONS)],
        )
        self.connection.commit()

    def sections(self) -> list[Section]:
        rows = self.connection.execute("SELECT * FROM sections ORDER BY position, name").fetchall()
        return [Section(row["id"], row["name"], row["position"]) for row in rows]

    def get_or_create_section(self, name: str) -> Section:
        name = name.strip()
        if not name:
            raise ValueError("A section needs a name.")
        row = self.connection.execute("SELECT * FROM sections WHERE name = ?", (name,)).fetchone()
        if row is None:
            position = self.connection.execute("SELECT COALESCE(MAX(position), -1) + 1 FROM sections").fetchone()[0]
            cursor = self.connection.execute("INSERT INTO sections(name, position) VALUES (?, ?)", (name, position))
            self.connection.commit()
            return Section(cursor.lastrowid, name, position)
        return Section(row["id"], row["name"], row["position"])

    def add_task(self, title: str, section_name: str = "Inbox", due_date: date | None = None, priority: str = "normal") -> Task:
        title = title.strip()
        if not title:
            raise ValueError("A task needs a title.")
        section = self.get_or_create_section(section_name)
        cursor = self.connection.execute(
            "INSERT INTO tasks(title, section_id, due_date, priority) VALUES (?, ?, ?, ?)",
            (title, section.id, due_date.isoformat() if due_date else None, priority),
        )
        self.connection.commit()
        return self.task(cursor.lastrowid)

    def task(self, task_id: int) -> Task:
        row = self.connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise ValueError(f"Task {task_id} does not exist.")
        return self._to_task(row)

    def tasks(self, section_id: int | None = None, include_completed: bool = True) -> list[Task]:
        clauses, values = [], []
        if section_id is not None:
            clauses.append("section_id = ?")
            values.append(section_id)
        if not include_completed:
            clauses.append("completed = 0")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.connection.execute(
            f"SELECT * FROM tasks {where} ORDER BY completed, CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END, due_date IS NULL, due_date, id DESC",
            values,
        ).fetchall()
        return [self._to_task(row) for row in rows]

    def set_completed(self, task_id: int, completed: bool) -> None:
        self.connection.execute("UPDATE tasks SET completed = ? WHERE id = ?", (int(completed), task_id))
        self.connection.commit()

    def delete_task(self, task_id: int) -> None:
        self.connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.connection.commit()

    @staticmethod
    def _to_task(row: sqlite3.Row) -> Task:
        return Task(row["id"], row["title"], row["section_id"], bool(row["completed"]), date.fromisoformat(row["due_date"]) if row["due_date"] else None, row["priority"], row["created_at"])
