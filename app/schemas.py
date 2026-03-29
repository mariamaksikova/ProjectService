from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# ----- Task schemas -----
class TaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "todo"
    priority: str = "medium"

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None

class TaskResponse(TaskBase):
    id: int
    project_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ----- Project schemas -----
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "active"

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    tasks: List[TaskResponse] = []

    class Config:
        from_attributes = True