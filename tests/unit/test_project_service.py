from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services import project_service


def test_project_crud_is_scoped_to_owner(db_session: Session, users: tuple[User, User]) -> None:
    owner, other_user = users
    project = project_service.create_project(
        db_session, owner, ProjectCreate(name="Knowledge base", description="docs")
    )
    other_project = project_service.create_project(
        db_session, other_user, ProjectCreate(name="Private project")
    )

    assert project_service.list_projects(db_session, owner) == [project]
    assert project_service.get_project(db_session, project.id, owner).id == project.id
    with pytest.raises(HTTPException) as error:
        project_service.get_project(db_session, project.id, other_user)
    assert error.value.status_code == 404

    updated = project_service.update_project(
        db_session, project.id, owner, ProjectUpdate(name="  Updated  ")
    )
    assert updated.name == "Updated"
    assert updated.description == "docs"

    project_service.delete_project(db_session, project.id, owner)
    assert db_session.get(Project, project.id) is None
    assert db_session.get(Project, other_project.id) is not None


@pytest.mark.parametrize("operation", ["create", "update", "delete"])
def test_project_changes_roll_back_when_commit_fails(
    db_session: Session,
    users: tuple[User, User],
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    owner, _ = users
    existing = project_service.create_project(
        db_session, owner, ProjectCreate(name="Original")
    )

    def fail_commit() -> None:
        raise RuntimeError("commit failed")

    monkeypatch.setattr(db_session, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="commit failed"):
        if operation == "create":
            project_service.create_project(db_session, owner, ProjectCreate(name="New"))
        elif operation == "update":
            project_service.update_project(
                db_session, existing.id, owner, ProjectUpdate(name="Changed")
            )
        else:
            project_service.delete_project(db_session, existing.id, owner)

    monkeypatch.undo()
    db_session.expire_all()
    persisted = db_session.get(Project, existing.id)
    assert persisted is not None
    assert persisted.name == "Original"
    assert project_service.list_projects(db_session, owner) == [persisted]


def test_get_project_returns_not_found_for_unknown_id(
    db_session: Session, users: tuple[User, User]
) -> None:
    owner, _ = users

    with pytest.raises(HTTPException) as error:
        project_service.get_project(db_session, uuid4(), owner)

    assert error.value.status_code == 404


def test_list_projects_returns_empty_list_for_user_without_projects(
    db_session: Session, users: tuple[User, User]
) -> None:
    _, owner_without_projects = users

    assert project_service.list_projects(db_session, owner_without_projects) == []
