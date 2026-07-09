#!/usr/bin/env bash
# Apply database migrations to the latest head.
set -euo pipefail
cd "$(dirname "$0")/../backend"
alembic upgrade head
