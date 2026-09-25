from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, StringConstraints

from . import db
from .greeting import greeting_for, part_of_day

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
DEFAULT_NAME = "Thoshi"


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(
    title="Hi Thoshi",
    description="A time-of-day greeting and a small to-do list",
    version="2.0.0",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --- Models ----------------------------------------------------------------

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class TaskCreate(BaseModel):
    title: Title


class TaskUpdate(BaseModel):
    title: Title | None = None
    done: bool | None = None


class Task(BaseModel):
    id: int
    title: str
    done: bool
    created_at: str


class Greeting(BaseModel):
    message: str
    part_of_day: str


# --- Page + health ---------------------------------------------------------

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat(timespec="seconds")}


# --- Greeting --------------------------------------------------------------

@app.get("/api/greeting")
def get_greeting(
    name: Annotated[str, Query(max_length=40)] = DEFAULT_NAME,
    hour: Annotated[int | None, Query(ge=0, le=23, description="Caller's local hour; defaults to server time")] = None,
) -> Greeting:
    name = name.strip() or DEFAULT_NAME
    if hour is None:
        hour = datetime.now().hour
    return Greeting(message=greeting_for(name, hour), part_of_day=part_of_day(hour))


# --- Tasks -----------------------------------------------------------------

@app.get("/api/tasks")
def list_tasks() -> list[Task]:
    return db.list_tasks()


@app.post("/api/tasks", status_code=status.HTTP_201_CREATED)
def create_task(body: TaskCreate) -> Task:
    return db.create_task(body.title)


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, body: TaskUpdate) -> Task:
    task = db.update_task(task_id, title=body.title, done=body.done)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int) -> Response:
    if not db.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
