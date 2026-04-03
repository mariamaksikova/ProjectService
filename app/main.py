from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import List
import asyncio
from datetime import datetime
from app.notifications import publish_notification

from app import schemas, models
from app.database import get_db, async_engine

app = FastAPI(
    title="Project Service API",
    description="Сервис для управления проектами и задачами",
    version="1.0.0"
)

# ----- Фоновая задача (пример асинхронности) -----
async def log_action(action: str, item_id: int):
    """Имитация логирования действий (например, в отдельную таблицу или файл)"""
    await asyncio.sleep(1)  # имитация долгой операции
    print(f"[{datetime.now()}] LOG: {action} for item {item_id}")
    # Здесь можно отправить событие в analytics-service
    # или записать в отдельную таблицу логов

async def update_user_skills(task_name: str):
    """Имитация прокачки навыков при завершении задачи"""
    await asyncio.sleep(0.5)
    print(f"🎓 Skill updated based on task: {task_name}")

# ----- Корневой эндпоинт -----
@app.get("/")
def root():
    return {
        "message": "Project Service API",
        "docs": "/docs",
        "status": "running with PostgreSQL"
    }

# ----- Projects -----
@app.get("/projects", response_model=List[schemas.ProjectResponse])
async def get_projects(
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Получить список всех проектов (асинхронно)"""
    # Асинхронный запрос с подгрузкой задач
    result = await db.execute(
        select(models.Project).options(selectinload(models.Project.tasks))
    )
    projects = result.scalars().all()
    
    # Фоновая задача (не блокирует ответ)
    if background_tasks:
        background_tasks.add_task(log_action, "GET_ALL_PROJECTS", 0)
    
    return projects

@app.get("/projects/{project_id}", response_model=schemas.ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить проект по ID (с задачами)"""
    result = await db.execute(
        select(models.Project)
        .where(models.Project.id == project_id)
        .options(selectinload(models.Project.tasks))
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project

@app.post("/projects", response_model=schemas.ProjectResponse, status_code=201)
async def create_project(
    project: schemas.ProjectCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Создать новый проект"""
    db_project = models.Project(**project.dict())
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    
    # Отправляем уведомление о создании проекта
    background_tasks.add_task(
        publish_notification,
        user_id=1,  # TODO: брать из JWT
        title="Создан проект",
        content=f'Проект "{db_project.name}" успешно создан'
    )
    
    background_tasks.add_task(log_action, "CREATE_PROJECT", db_project.id)

    project_result = await db.execute(
        select(models.Project).where(models.Project.id == db_project.id)
    )
    project_row = project_result.scalar_one()

    tasks_result = await db.execute(
        select(models.Task).where(models.Task.project_id == db_project.id)
    )
    tasks_rows = tasks_result.scalars().all()
    tasks_out = [
        schemas.TaskResponse.model_validate(t, from_attributes=True)
        for t in tasks_rows
    ]

    return schemas.ProjectResponse(
        id=project_row.id,
        name=project_row.name,
        description=project_row.description,
        status=project_row.status,
        created_at=project_row.created_at,
        tasks=tasks_out,
    )

@app.put("/projects/{project_id}", response_model=schemas.ProjectResponse)
async def update_project(
    project_id: int,
    project_update: schemas.ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить проект"""
    result = await db.execute(
        select(models.Project).where(models.Project.id == project_id)
    )
    db_project = result.scalar_one_or_none()
    
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    await db.commit()
    await db.refresh(db_project)

    # Аналогично `create_project`: возвращаем DTO, а не ORM-объект.
    project_result = await db.execute(
        select(models.Project).where(models.Project.id == db_project.id)
    )
    project_row = project_result.scalar_one()

    tasks_result = await db.execute(
        select(models.Task).where(models.Task.project_id == db_project.id)
    )
    tasks_rows = tasks_result.scalars().all()
    tasks_out = [
        schemas.TaskResponse.model_validate(t, from_attributes=True)
        for t in tasks_rows
    ]

    return schemas.ProjectResponse(
        id=project_row.id,
        name=project_row.name,
        description=project_row.description,
        status=project_row.status,
        created_at=project_row.created_at,
        tasks=tasks_out,
    )

@app.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Удалить проект"""
    result = await db.execute(
        select(models.Project).where(models.Project.id == project_id)
    )
    db_project = result.scalar_one_or_none()
    
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.delete(db_project)
    await db.commit()
    
    background_tasks.add_task(log_action, "DELETE_PROJECT", project_id)
    
    return {"message": "Project deleted successfully"}

# ----- Tasks -----
@app.get("/projects/{project_id}/tasks", response_model=List[schemas.TaskResponse])
async def get_tasks(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить задачи проекта"""
    # Проверяем существование проекта
    project_result = await db.execute(
        select(models.Project).where(models.Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Получаем задачи
    tasks_result = await db.execute(
        select(models.Task).where(models.Task.project_id == project_id)
    )
    tasks = tasks_result.scalars().all()
    
    return tasks

@app.post("/projects/{project_id}/tasks", response_model=schemas.TaskResponse, status_code=201)
async def create_task(
    project_id: int,
    task: schemas.TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Создать задачу в проекте"""
    # Проверяем проект
    project_result = await db.execute(
        select(models.Project).where(models.Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_task = models.Task(**task.dict(), project_id=project_id)
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    
    # Отправляем уведомление о создании задачи
    background_tasks.add_task(
        publish_notification,
        user_id=1,  # TODO: брать из JWT
        title="Создана задача",
        content=f'Задача "{task.name}" добавлена в проект'
    )
    
    return db_task

@app.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить задачу по ID"""
    result = await db.execute(
        select(models.Task).where(models.Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task

@app.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
async def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Обновить задачу"""
    result = await db.execute(
        select(models.Task).where(models.Task.id == task_id)
    )
    db_task = result.scalar_one_or_none()
    
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Сохраняем старый статус для проверки
    old_status = db_task.status
    
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    await db.commit()
    await db.refresh(db_task)
    
    # Если задача завершена - отправляем уведомление
    if old_status != "done" and db_task.status == "done":
        background_tasks.add_task(update_user_skills, db_task.name)
        background_tasks.add_task(
            publish_notification,
            user_id=1,  # TODO: брать из JWT
            title="Задача завершена",
            content=f'Задача "{db_task.name}" выполнена! + навыки'
    )
    
    return db_task

@app.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Удалить задачу"""
    result = await db.execute(
        select(models.Task).where(models.Task.id == task_id)
    )
    db_task = result.scalar_one_or_none()
    
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete(db_task)
    await db.commit()
    
    background_tasks.add_task(log_action, "DELETE_TASK", task_id)
    
    return {"message": "Task deleted successfully"}

# ----- Дополнительный асинхронный эндпоинт -----
@app.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Получить статистику по проектам и задачам (асинхронно)"""
    # Выполняем несколько запросов параллельно
    projects_query = select(models.Project)
    tasks_query = select(models.Task)
    
    projects_result, tasks_result = await asyncio.gather(
        db.execute(projects_query),
        db.execute(tasks_query)
    )
    
    projects = projects_result.scalars().all()
    tasks = tasks_result.scalars().all()
    
    # Считаем статистику
    total_projects = len(projects)
    total_tasks = len(tasks)
    tasks_by_status = {
        "todo": sum(1 for t in tasks if t.status == "todo"),
        "in_progress": sum(1 for t in tasks if t.status == "in_progress"),
        "review": sum(1 for t in tasks if t.status == "review"),
        "done": sum(1 for t in tasks if t.status == "done")
    }
    
    return {
        "total_projects": total_projects,
        "total_tasks": total_tasks,
        "tasks_by_status": tasks_by_status
    }