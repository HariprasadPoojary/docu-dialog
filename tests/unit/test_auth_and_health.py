from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1 import health
from app.core.auth import get_current_user
from app.core.config import Settings
from app.models.user import User


def test_authentication_fails_closed_outside_local_environment() -> None:
    session = MagicMock()

    with pytest.raises(HTTPException) as error:
        get_current_user(session, Settings(environment="production"))

    assert error.value.status_code == 503
    session.scalar.assert_not_called()


def test_local_auth_returns_existing_user() -> None:
    user = User(email="developer@local.test")
    session = MagicMock()
    session.scalar.return_value = user

    assert get_current_user(session, Settings(environment="local")) is user
    session.commit.assert_not_called()


def test_local_auth_creates_configured_user_when_missing() -> None:
    session = MagicMock()
    session.scalar.return_value = None
    settings = Settings(environment="local", local_user_email="  DEV@Example.Test ")

    user = get_current_user(session, settings)

    assert user.email == "dev@example.test"
    session.add.assert_called_once_with(user)
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(user)


def test_liveness_check_returns_ok() -> None:
    assert health.healthcheck() == {"status": "ok"}


def test_readiness_check_executes_database_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = MagicMock()
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = connection
    monkeypatch.setattr(health, "get_engine", lambda: engine)

    assert health.readiness() == {"status": "ok", "database": "ok"}
    connection.execute.assert_called_once()


@pytest.mark.parametrize("failure", [RuntimeError("not configured"), SQLAlchemyError("offline")])
def test_readiness_reports_database_failure_as_unavailable(
    monkeypatch: pytest.MonkeyPatch, failure: Exception
) -> None:
    monkeypatch.setattr(health, "get_engine", lambda: _raise(failure))

    with pytest.raises(HTTPException) as error:
        health.readiness()

    assert error.value.status_code == 503
    assert error.value.detail == "Database is unavailable"


def _raise(error: Exception) -> None:
    raise error
