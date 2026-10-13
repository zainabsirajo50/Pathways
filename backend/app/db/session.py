"""Request-scoped, rollback-only database access for the public API."""
from collections.abc import Iterator
from fastapi import Request
from sqlalchemy import text
from sqlalchemy.orm import Session


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        # Also prevents accidental writes if a future GET handler is implemented incorrectly.
        session.execute(text('SET TRANSACTION READ ONLY'))
        try:
            yield session
        finally:
            session.rollback()
