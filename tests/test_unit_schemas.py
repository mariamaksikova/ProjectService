from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app import schemas


def test_project_create_defaults():
    p = schemas.ProjectCreate(name="Test", description="d")
    assert p.status == "active"
    assert p.name == "Test"


def test_project_create_requires_name():
    with pytest.raises(ValidationError):
        schemas.ProjectCreate()


def test_project_update_all_optional():
    u = schemas.ProjectUpdate()
    dump = (
        u.model_dump(exclude_unset=True)
        if hasattr(u, "model_dump")
        else u.dict(exclude_unset=True)
    )
    assert dump == {}


def test_task_create_defaults():
    t = schemas.TaskCreate(name="Task1")
    assert t.status == "todo"
    assert t.priority == "medium"


def test_task_response_from_attributes():
    class Row:
        id = 1
        project_id = 2
        name = "n"
        description = None
        status = "todo"
        priority = "low"
        created_at = datetime(2020, 1, 1, tzinfo=timezone.utc)

    tr = schemas.TaskResponse.model_validate(Row(), from_attributes=True)
    assert tr.id == 1
    assert tr.project_id == 2
