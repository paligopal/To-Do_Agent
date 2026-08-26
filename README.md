# To-Do Agent

A local-first PyQt6 desktop to-do list. Tasks are saved in SQLite at
`~/.todo_agent/todo.db` on your PC.

## Run it

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/) (or install PyQt6
with pip). From this folder:

```powershell
uv run main.py
```

## Current MVP

- Create sections and add tasks with a due date and priority.
- Mark a task complete; double-click one to delete it.
- `TodoService` is the single safe boundary for both the desktop app and a
  future messaging adapter.

## MCP server

The project now exposes a local Model Context Protocol (MCP) server over
standard input/output. It never exposes the SQLite database itself; clients
can only use validated tools:

- `list_sections`, `list_tasks`
- `add_task`, `update_task`, `complete_task`, `delete_task`

Start it from the project directory:

```powershell
uv run todo-agent-mcp
```

For interactive development and manual testing in the MCP Inspector:

```powershell
uv run mcp dev todo_agent/mcp_server.py
```

The server and desktop GUI read the same database. Keep the server on local
`stdio`; do not expose it as a public HTTP endpoint without authentication.

## Connect Codex

Register the server with Codex once:

```powershell
codex mcp add todo-agent -- ".\.venv\Scripts\todo-agent-mcp.exe"
```

Verify its configuration:

```powershell
codex mcp get todo-agent
```

Open a new Codex session and ask it to list, add, update, complete, or delete
tasks. For example: `Add a high-priority Work task to finish the report
tomorrow.` Remove the integration with `codex mcp remove todo-agent`.

## Agent command format

The service is ready to receive text from a messenger connector:

```text
add Buy milk #Personal tomorrow !high
add Send status update #Work today
list Work
```

## Recommended integration path

Start with **Telegram**: create a bot with BotFather, run a small local Python
polling process, and send each incoming message to
`TodoService.process_message()`. It is the simplest option for a personal
desktop project.

WhatsApp requires the Meta WhatsApp Business Platform (or a provider such as
Twilio), a public HTTPS webhook, and a secure tunnel to your PC. Protect it
with an allow-list of your sender ID; never expose the database or GUI itself.

Next milestone: add an in-app PyQt chat panel or a Telegram adapter. Any LLM
integration should only emit validated actions for `TodoService` or call the
MCP tools; it must never write to SQLite directly.
