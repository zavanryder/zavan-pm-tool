# Kanban Studio

A local Dockerized project management app with multi-board Kanban, auth, search, profile management, and an AI chat assistant that can create, move, update, and delete cards.

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

4. Sign in with the seeded account `user` / `password`, or register a new account from the login screen.

To stop:

```bash
bash scripts/stop.sh
```

Data is persisted in `data/kanban.db` (SQLite). Passwords are stored as salted PBKDF2-SHA256 hashes. Legacy password rows are upgraded automatically on login.

## AI chat

Click the "AI Chat" button in the top-right corner to open the chat sidebar. You can ask the AI to:

- Add cards: "Add a card called 'Fix login bug' to Backlog"
- Move cards: "Move 'Fix login bug' to In Progress"
- Update cards: "Update 'Fix login bug' with details 'Repro steps in issue #42'"
- Delete cards: "Delete 'Fix login bug'"
- Ask questions: "What's in my Review column?"

## Notes

- The seeded `user` / `password` account is created on backend startup for MVP compatibility.
- Users can register additional accounts through the app.
- Each user can create multiple boards.
- AI chat updates are scoped to the currently opened board.

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

Frontend E2E:

```bash
cd frontend
npm run test:e2e
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
