#!/bin/bash
set -e

# Run Alembic migrations before starting the application
alembic upgrade head
echo "Alembic migrations applied."

# Start uvicorn (replaces current process)
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
