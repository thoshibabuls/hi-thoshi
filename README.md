# Hi Thoshi

A small personal dashboard built with FastAPI and plain HTML/CSS/JS. It greets you by the time of day and keeps a to-do list that survives restarts.

- **Greeting that follows the clock:** "Good morning, Thoshi ☀️" becomes "Good evening, Thoshi 🌆", and the colours of the sky band at the top change with it.
- **To-do list:** add tasks, tick them off and delete them. Tasks are saved in a SQLite file.
- **One server, one URL:** FastAPI serves both the API and the page.

## Run it (Windows)

```powershell
# 1. (optional) create a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. start the app from the project folder
python -m uvicorn src.main:app --reload
```

Then open **http://localhost:8000**.

Interactive API docs are at **http://localhost:8000/docs**, where you can try every endpoint from the browser.

## Run the tests

```powershell
python -m pytest
```

## Project structure

```
trail/
├── src/
│   ├── main.py        # FastAPI app: routes, request/response models, serves the page
│   ├── db.py          # All SQLite code (create, list, update, delete tasks)
│   └── greeting.py    # Time-of-day logic (pure functions, easy to test)
├── static/
│   ├── index.html     # The page
│   ├── style.css      # Styles, including the per-time-of-day sky colours
│   └── app.js         # Calls the API and renders the list
├── tests/
│   └── test_api.py    # pytest tests for every endpoint
├── data/tasks.db      # Created automatically on first run
└── requirements.txt
```

## API

| Method | Path | What it does |
|---|---|---|
| GET | `/` | The dashboard page |
| GET | `/health` | `{"status": "ok", "time": "..."}` |
| GET | `/api/greeting?name=Thoshi&hour=21` | Greeting for that hour. `hour` is optional (0–23) and defaults to the server clock. |
| GET | `/api/tasks` | All tasks, oldest first |
| POST | `/api/tasks` | Add a task: `{"title": "Buy milk"}` → `201` |
| PATCH | `/api/tasks/{id}` | Update a task: `{"done": true}` and/or `{"title": "New title"}` |
| DELETE | `/api/tasks/{id}` | Delete a task → `204` |

A task looks like this:

```json
{ "id": 1, "title": "Buy milk", "done": false, "created_at": "2026-09-25T16:30:00+00:00" }
```

Titles are trimmed and must be 1–200 characters; anything else returns `422`. A task id that doesn't exist returns `404`.

### Greeting times

| Hours | Greeting |
|---|---|
| 05:00–11:59 | Good morning, Thoshi ☀️ |
| 12:00–16:59 | Good afternoon, Thoshi 👋 |
| 17:00–21:59 | Good evening, Thoshi 🌆 |
| 22:00–04:59 | Still up, Thoshi? 🌙 |

## Ideas for next steps

- Due dates, or a "today" filter
- Double-click a task to rename it (the PATCH endpoint already supports it)
- A "clear completed" button
