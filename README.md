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

Next milestone: add a Telegram adapter with a `.env` bot token and explicit
allowed-chat-ID check. An LLM parser can come later, but it should only emit
validated actions for `TodoService` rather than write to SQLite directly.
