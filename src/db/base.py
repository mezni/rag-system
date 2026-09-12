"""Base module for SQLAlchemy ORM models and session management."""

from .session import engine, Base, SessionLocal

# Convenience function to get a new session
def get_session():
    """Create a new database session."""
    return SessionLocal()