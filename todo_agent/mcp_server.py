"""Local stdio MCP server for To-Do Agent.

Run with: uv run python -m todo_agent.mcp_server
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from mcp.server.mcpserver import MCPServer

from todo_agent.service import TodoService
from todo_agent.storage import TodoRepository


def create_server(service: TodoService) -> MCPServer:
    mcp = MCPServer(
        "To-Do Agent",
        instructions="Manage the user's local to-do list. Use structured tools; never assume task IDs.",
    )

    @mcp.tool()
    async def list_sections() -> list[dict[str, object]]:
        """List available task sections."""
        return service.list_sections()

    @mcp.tool()
    async def list_tasks(section: str | None = None, include_completed: bool = False) -> list[dict[str, object]]:
        """List tasks, optionally restricted to an existing section."""
        return service.list_tasks(section, include_completed)

    @mcp.tool()
    async def add_task(title: str, section: str = "Inbox", due_date: str | None = None, priority: Literal["high", "normal", "low"] = "normal") -> dict[str, object]:
        """Create a task. due_date, when supplied, must be YYYY-MM-DD."""
        task = service.add_task(title, section, service.parse_due_date(due_date), priority)
        return service.serialize_task(task)

    @mcp.tool()
    async def update_task(task_id: int, title: str | None = None, section: str | None = None, due_date: str | None = None, clear_due_date: bool = False, priority: Literal["high", "normal", "low"] | None = None) -> dict[str, object]:
        """Update a task. Set clear_due_date=true to remove its due date."""
        return service.update_task(task_id, title=title, section=section, due_date=service.parse_due_date(due_date), clear_due_date=clear_due_date, priority=priority)

    @mcp.tool()
    async def complete_task(task_id: int, completed: bool = True) -> dict[str, object]:
        """Mark a task completed or reopen it."""
        return service.set_completed(task_id, completed)

    @mcp.tool()
    async def delete_task(task_id: int) -> dict[str, object]:
        """Permanently delete a task after the user has confirmed the action."""
        return service.delete_task(task_id)

    return mcp


def default_service() -> TodoService:
    return TodoService(TodoRepository(Path.home() / ".todo_agent" / "todo.db"))


mcp = create_server(default_service())


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
