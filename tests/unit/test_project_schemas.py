import pytest
from pydantic import ValidationError

from app.schemas.project import ProjectCreate, ProjectUpdate


def test_project_create_normalizes_name_and_description() -> None:
    request = ProjectCreate(name="  Research  ", description="  notes  ")

    assert request.name == "Research"
    assert request.description == "notes"


@pytest.mark.parametrize("name", ["", " ", "\t\n"])
def test_project_create_rejects_blank_name(name: str) -> None:
    with pytest.raises(ValidationError):
        ProjectCreate(name=name)


def test_project_create_reports_clear_error_for_whitespace_name_and_description() -> None:
    with pytest.raises(ValidationError) as error:
        ProjectCreate(name="   ", description="   ")

    assert error.value.errors()[0]["msg"] == "Value error, Project name cannot be blank"


def test_project_create_enforces_field_lengths() -> None:
    with pytest.raises(ValidationError):
        ProjectCreate(name="x" * 161)
    with pytest.raises(ValidationError):
        ProjectCreate(name="Valid", description="x" * 4001)


def test_project_update_requires_at_least_one_field() -> None:
    with pytest.raises(ValidationError, match="At least one field must be provided"):
        ProjectUpdate()


def test_project_update_distinguishes_omitted_fields_from_null() -> None:
    update = ProjectUpdate(description="  ")

    assert update.model_fields_set == {"description"}
    assert update.description is None
    with pytest.raises(ValidationError, match="Project name cannot be null"):
        ProjectUpdate(name=None)


def test_project_update_normalizes_name() -> None:
    assert ProjectUpdate(name="  Updated  ").name == "Updated"
    with pytest.raises(ValidationError, match="Project name cannot be blank"):
        ProjectUpdate(name=" ")
