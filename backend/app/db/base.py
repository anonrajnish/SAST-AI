"""SQLAlchemy 2.x declarative base.

All ORM models will inherit from :class:`Base`. No models are declared in the engineering
foundation — they arrive with their feature tasks (TASK-110+).
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
