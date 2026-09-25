# Hi Thoshi

A small personal dashboard built with FastAPI and plain HTML/CSS/JS. It greets you by the time of day and keeps a to-do list that survives restarts.

- **Greeting that follows the clock:** "Good morning, Thoshi ☀️" becomes "Good evening, Thoshi 🌆", and the colours of the sky band at the top change with it.
- **To-do list:** add tasks, tick them off and delete them. Tasks are saved in SQLite on your laptop and in Firestore on Google Cloud.
- **One server, one URL:** FastAPI serves both the API and the page.
- **Optional password:** set `APP_PASSWORD` and the browser asks for it before showing anything.

## Run it (Windows)

```powershell
# 1. (optional) create a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. install dependencies (includes the test tools)
pip install -r requirements-dev.txt

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
│   ├── main.py          # FastAPI app: routes, models, password check, serves the page
│   ├── db.py            # SQLite storage (used on your laptop)
│   ├── firestore_db.py  # Firestore storage (used on Cloud Run) - same functions as db.py
│   └── greeting.py      # Time-of-day logic (pure functions, easy to test)
├── static/
│   ├── index.html       # The page
│   ├── style.css        # Styles, including the per-time-of-day sky colours
│   └── app.js           # Calls the API and renders the list
├── tests/
│   └── test_api.py      # pytest tests for every endpoint
├── Dockerfile           # How Cloud Run builds and starts the app
├── data/tasks.db        # Created automatically on first local run
├── requirements.txt     # What the app needs to run
└── requirements-dev.txt # Plus the test tools
```

## Settings (environment variables)

| Variable | Default | What it does |
|---|---|---|
| `STORAGE` | *(unset)* = SQLite | Set to `firestore` to store tasks in Firestore |
| `APP_PASSWORD` | *(unset)* = no password | When set, every page and API call needs this password. The browser shows a login box; any username works. `/health` stays open. |

## Deploy to Google Cloud (Cloud Run)

Cloud Run builds the app straight from this GitHub repo and redeploys on every push to `main`. You don't need Docker or `gcloud` on your laptop.

Why Firestore: Cloud Run wipes local files whenever the app restarts or goes idle, so a SQLite file there would lose your tasks.

**1. Create a project**
[console.cloud.google.com](https://console.cloud.google.com) → project picker (top left) → **New project** → name it `hi-thoshi` → **Create**. Then link a billing account (**Billing** → **Link a billing account**). Personal use should stay within the free tier, but Cloud Run requires billing to be on.

**2. Create the Firestore database**
Search **Firestore** → **Create database** → **Native mode**, database ID `(default)` → pick a location near you (e.g. `asia-south1` Mumbai) → **Create**.

**3. Create the Cloud Run service**
Search **Cloud Run** → **Deploy container** (or **Create service**) → **Continuously deploy from a repository** → **Set up with Cloud Build**:
- Enable any APIs it asks for (Cloud Build, Artifact Registry).
- Repository provider: **GitHub** → sign in → install the Google Cloud Build app on the `hi-thoshi` repo → select it.
- Branch: `^main$` · Build type: **Dockerfile** · Source location: `/Dockerfile` → **Save**.

Then on the same page:
- Service name `hi-thoshi`, region **the same as Firestore** (e.g. `asia-south1`).
- Authentication: **Allow public access** (unauthenticated). Your `APP_PASSWORD` protects the app.
- Minimum instances `0` (free when nobody's using it), maximum `2`.
- **Containers → Variables & Secrets** → add:
  - `STORAGE` = `firestore`
  - `APP_PASSWORD` = a password of your choice
- **Create**.

**4. Open it**
When the build finishes, the URL (`https://hi-thoshi-….run.app`) appears at the top. Open it, enter any username and your password, then add a task and refresh the page. If the task is still there, Firestore is working. You'll also see it under Firestore → **tasks**.

**Updating:** push to `main` on GitHub and Cloud Run rebuilds and redeploys automatically.

**If tasks fail to save (errors mentioning 403 or permissions):** go to **IAM**, find the service account Cloud Run uses (shown on the service's **Security** tab, usually `…-compute@developer.gserviceaccount.com`) and grant it the **Cloud Datastore User** role.

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
