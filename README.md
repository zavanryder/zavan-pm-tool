# Kanban Studio

A single-board Kanban app with drag-and-drop cards, inline card editing, and an AI chat assistant that can create, move, and update cards via natural language.

## Requirements

- Docker
- An OpenRouter API key

## Setup

1. Create a `.env` file in the project root:

```
OPENROUTER_API_KEY=your-key-here
```

2. Start the app:

```bash
bash scripts/start.sh
```

3. Open http://localhost:8000 in your browser.

4. Log in with username `user` and password `password`.

To stop:

```bash
bash scripts/stop.sh
```

Data is persisted in `data/kanban.db` (SQLite). This directory is created automatically on first run.

## AI chat

Click the "AI Chat" button in the top-right corner to open the chat sidebar. You can ask the AI to:

- Add cards: "Add a card called 'Fix login bug' to Backlog"
- Move cards: "Move 'Fix login bug' to In Progress"
- Update cards: "Update 'Fix login bug' with details 'Repro steps in issue #42'"
- Delete cards: "Delete 'Fix login bug'"
- Ask questions: "What's in my Review column?"

## Adding users

The MVP has a single hardcoded user (`user` / `password`). To add users, edit `USERS` in `backend/auth.py`:

```python
USERS = {
    "user": "password",
    "alice": "her-password",
}
```

Then rebuild: `bash scripts/start.sh`

New users get their own board with default columns (Backlog, Discovery, In Progress, Review, Done) created on first login.

## Running tests

Backend:

```bash
cd backend
.venv/bin/pytest -v
```

Frontend:

```bash
cd frontend
npm test
```

If the backend venv doesn't exist yet, create it first:

```bash
cd backend
uv sync --no-install-project
```

## Stack

- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS 4, @dnd-kit
- Backend: Python 3.12, FastAPI, SQLite, PyJWT, OpenAI SDK
- AI: OpenRouter (`openai/gpt-oss-120b`)
- Infrastructure: Docker, uv
