# Project Plan

## Part 1: Plan

Enrich this document with detailed substeps, create frontend/AGENTS.md.

- [x] Review existing frontend codebase
- [x] Create frontend/AGENTS.md describing the existing code
- [x] Write detailed plan for all parts with checklists and success criteria
- [x] Verify OpenRouter model availability
- [x] Update CLAUDE.md (Linux-only scripts)
- [x] Get user approval on this plan

**Success criteria:** User approves the plan before any implementation begins.

---

## Part 2: Scaffolding (DONE)

Set up Docker, FastAPI backend, and Linux start/stop scripts.

- [x] Create `backend/main.py` -- FastAPI app serving static files at `/` and `/api/health` endpoint
- [x] Create `backend/pyproject.toml` -- Python project config with dependencies
- [x] Create `Dockerfile` -- multi-stage build (Node for frontend, Python with uv for backend)
- [x] Create `docker-compose.yml` -- mounts `.env` and `data/` volume
- [x] Create `scripts/start.sh` and `scripts/stop.sh`
- [x] `/api/health` returns `{"status": "ok"}`

---

## Part 3: Add in Frontend (DONE)

Build the Next.js frontend statically and serve it via FastAPI inside Docker.

- [x] Configure Next.js for static export (`output: 'export'`)
- [x] Dockerfile builds frontend and copies `out/` to backend `static/`
- [x] FastAPI serves the static Kanban board at `/`
- [x] Health endpoint still works
- [x] Start/stop scripts work cleanly

**Verified:** `curl localhost:8000/` returns full Kanban HTML, `curl localhost:8000/api/health` returns `{"status":"ok"}`.

---

## Part 4: Add in a fake user sign in experience (DONE)

Auth with hardcoded credentials ("user" / "password"), JWT tokens, login form, logout button.

- [x] `/api/auth/login` POST -- returns JWT token
- [x] `/api/auth/me` GET -- validates token, returns username
- [x] `get_current_user` dependency for protecting routes
- [x] Frontend: LoginForm component, App component manages auth state
- [x] Frontend: logout button in KanbanBoard header
- [x] Token stored in memory via `api.ts` module
- [x] 7 backend tests pass (login success/failure, me with/without token, health)
- [x] 6 frontend tests pass (existing kanban tests updated for new props)
- [x] Integration verified in Docker: login returns token, /me works, invalid creds rejected

Note: Removed `/api/auth/logout` endpoint -- stateless JWT means client just clears the token.

---

## Part 5: Database modeling (DONE)

- [x] Schema: users, boards, columns, cards tables with positions and foreign keys
- [x] `docs/schema.json` and `docs/DATABASE.md` created
- [x] User approved schema

---

## Part 6: Backend (DONE)

- [x] `backend/database.py` -- SQLite init, CRUD operations, all ownership-checked
- [x] API routes: GET /api/board, PUT /api/columns/{id}, POST /api/cards, PUT /api/cards/{id}, DELETE /api/cards/{id}, PUT /api/cards/{id}/move
- [x] DB auto-creates on startup, default 5 columns seeded per user
- [x] 19 backend tests pass (7 auth + 12 board)

---

## Part 7: Frontend + Backend (DONE)

- [x] Frontend fetches board from API, all operations call backend
- [x] Optimistic updates for drag-drop and delete (revert on API failure)
- [x] Loading and error states
- [x] 7 frontend tests pass (4 kanban logic + 3 board component with mocked API)
- [x] Integration verified in Docker: login -> create card -> move -> delete all persist

---

## Part 8: AI connectivity (DONE)

- [x] `backend/ai.py` -- OpenAI SDK pointed at OpenRouter, model `openai/gpt-oss-120b`
- [x] `openai` added to Python dependencies
- [x] Integration test: "What is 2+2?" returns "4" via Docker

---

## Part 9: AI structured output (DONE)

- [x] System prompt includes board state JSON, instructs model to respond with structured JSON
- [x] Response schema: `{message, board_updates[]}` with add/update/move/delete operations
- [x] `POST /api/ai/chat` endpoint: accepts message + history, applies board_updates to DB, returns updated board
- [x] Malformed responses handled gracefully (falls back to plain text message)
- [x] 7 AI unit tests pass (chat call, build_messages, parse_response variants)
- [x] Integration: AI adds 3 cards + moves a card correctly in Docker

---

## Part 10: AI chat sidebar (DONE)

- [x] `ChatSidebar` component: fixed right panel, message history, input + send
- [x] "AI Chat" toggle button (Purple Secondary) in KanbanBoard header
- [x] Sends message + conversation history to `/api/ai/chat`
- [x] Board auto-refreshes when AI makes changes
- [x] Loading indicator ("Thinking...") while AI responds
- [x] Conversation history in component state (resets on refresh)
- [x] 7 frontend tests pass, 26 backend tests pass
- [x] Full E2E verified in Docker: chat creates/moves cards, board updates in real time
