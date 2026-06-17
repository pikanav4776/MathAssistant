#!/usr/bin/env bash
# Production-style start (Render, Linux). Local dev: use start.ps1 instead.
set -euo pipefail
cd "$(dirname "$0")"
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
