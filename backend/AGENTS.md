# Backend

FastAPI application serving the static Next.js frontend and API routes.

## Files

- `main.py` -- FastAPI app. Mounts static files at `/`, API routes at `/api/`.
- `pyproject.toml` -- Python project config. Dependencies: fastapi, uvicorn.

## How it runs

Inside Docker, uvicorn runs `main:app` on port 8000. The static frontend is copied to `./static/` during the Docker build. Uses uv for package management.
