from prometheus_client import Counter, Gauge
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models

projects_total = Gauge(
    "project_service_projects_total",
    "Current number of projects in the database",
)

tasks_total = Gauge(
    "project_service_tasks_total",
    "Current number of tasks in the database",
)

projects_created_total = Counter(
    "project_service_projects_created_total",
    "Total number of projects created since service start",
)

tasks_created_total = Counter(
    "project_service_tasks_created_total",
    "Total number of tasks created since service start",
)


async def refresh_business_metrics(db: AsyncSession) -> None:
    projects_count = await db.scalar(select(func.count()).select_from(models.Project))
    tasks_count = await db.scalar(select(func.count()).select_from(models.Task))
    projects_total.set(projects_count or 0)
    tasks_total.set(tasks_count or 0)


def setup_metrics(app) -> None:
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=False,
        excluded_handlers={"/metrics", "/health"},
    ).instrument(app).expose(
        app,
        endpoint="/metrics",
        include_in_schema=False,
    )
