# The Project Management MVP web app

## Current Product State

This project is a local-first Project Management app with:
- Sign in and registration
- A multi-board Kanban workspace per user
- Renameable columns
- Editable cards with drag-and-drop movement
- Card labels and due dates
- AI chat in a sidebar that can create, edit, move, and delete cards
- Search across cards
- Basic user profile and password change flows

## Current Limitations

- Intended to run locally in Docker
- A default `user` / `password` account is still seeded for MVP compatibility
- AI actions are scoped to the currently selected board
- Data is stored in a local SQLite database

## Technical Decisions

- Next.js frontend
- Python FastAPI backend, including serving the static Next.js site at `/`
- Everything packaged into a Docker container
- Use `uv` as the Python package manager in Docker
- Use OpenRouter for AI calls; `OPENROUTER_API_KEY` is loaded from `.env`
- Use `openai/gpt-oss-120b` as the model
- Use SQLite local database, creating a new DB if it does not exist
- Passwords are stored as salted PBKDF2-SHA256 hashes; legacy hashes are upgraded on login
- Start and stop server scripts for Linux live in `scripts/`

## Architecture Notes

- The frontend is no longer a standalone demo; it talks to the FastAPI backend for auth, boards, cards, search, AI chat, and profile operations.
- The app supports multiple boards per user.
- The backend enforces ownership checks on board, column, and card operations.
- AI chat responses are parsed as structured updates and applied only within the requested board.
- Request payloads have explicit length limits to control storage growth and AI prompt size.

## Color Scheme

- Accent Yellow: `#ecad0a`
- Blue Primary: `#209dd7`
- Purple Secondary: `#753991`
- Dark Navy: `#032147`
- Gray Text: `#888888`

## Coding standards

1. Use current idiomatic library APIs.
2. Keep it simple. Do not over-engineer.
3. Be concise. Keep README minimal. No emojis.
4. Fix root causes, not symptoms. Prove the issue before changing code.

## Working documentation

All planning and execution documents live in `docs/`.
Review `docs/PLAN.md` before making substantial changes.
