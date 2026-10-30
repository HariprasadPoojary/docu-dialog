"""Caller identity dependency, with an explicit local-development identity only."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.user import User


def get_current_user(
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """Return the one fixed local user; fail closed until production auth is configured."""

    if settings.environment.casefold() != "local":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured for this environment",
        )

    email = settings.local_user_email.strip().casefold()
    user = session.scalar(select(User).where(User.email == email))
    if user is not None:
        return user

    user = User(email=email)
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        # A second local request may create the same bootstrap row at the same time.
        session.rollback()
        user = session.scalar(select(User).where(User.email == email))
        if user is None:
            raise
    else:
        session.refresh(user)

    return user
