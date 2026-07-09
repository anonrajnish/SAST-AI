"""baseline (empty) — establishes the Alembic head; no business tables.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-07-10

PostgreSQL 16 provides ``gen_random_uuid()`` in core, so no extension is required here.
Business tables are introduced by later feature tasks (TASK-110+), each in its own
migration per AI_DEVELOPMENT_GUIDE §9.
"""

from __future__ import annotations

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: None = None
depends_on: None = None


def upgrade() -> None:
    """Intentionally empty: this migration only establishes the migration head."""


def downgrade() -> None:
    """Intentionally empty."""
