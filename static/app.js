const NAME_KEY = "hi-dashboard:name";
const DEFAULT_NAME = "Thoshi";

const $ = (id) => document.getElementById(id);

let tasks = [];
let tasksLoaded = false;

// ---------- API ----------

class ApiError extends Error {
    constructor(status, message) {
        super(message);
        this.status = status;
    }
}

async function api(path, options = {}) {
    let res;
    try {
        res = await fetch(path, {
            headers: { "Content-Type": "application/json" },
            ...options,
        });
    } catch {
        throw new ApiError(0, "Can't reach the server. Check that it's running, then refresh the page.");
    }
    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const message = typeof body.detail === "string"
            ? body.detail
            : "The server didn't accept that. Check the text and try again.";
        throw new ApiError(res.status, message);
    }
    return res.status === 204 ? null : res.json();
}

// ---------- Name (kept in this browser only) ----------

function loadName() {
    try {
        return localStorage.getItem(NAME_KEY) || DEFAULT_NAME;
    } catch {
        return DEFAULT_NAME;
    }
}

function saveName(name) {
    try {
        localStorage.setItem(NAME_KEY, name);
    } catch {
        // Storage blocked: the name still applies until the page reloads.
    }
}

// ---------- Greeting ----------

let currentName = loadName();

async function loadGreeting() {
    const params = new URLSearchParams({ name: currentName, hour: new Date().getHours() });
    const greeting = await api(`/api/greeting?${params}`);
    $("greeting").textContent = greeting.message;
    document.body.dataset.part = greeting.part_of_day;
    if (!document.body.classList.contains("ready")) {
        void document.body.offsetWidth; // apply the first sky colours instantly, then enable transitions
        document.body.classList.add("ready");
    }
}

function showToday() {
    $("today").textContent = new Date().toLocaleDateString(undefined, {
        weekday: "long", day: "numeric", month: "long",
    });
}

// ---------- Rendering ----------

function taskItem(task) {
    const li = document.createElement("li");
    li.className = task.done ? "task is-done" : "task";

    const box = document.createElement("input");
    box.type = "checkbox";
    box.id = `task-${task.id}`;
    box.checked = task.done;
    box.addEventListener("change", () => run(() => setDone(task, box.checked)));

    const label = document.createElement("label");
    label.htmlFor = box.id;
    label.textContent = task.title;

    const del = document.createElement("button");
    del.type = "button";
    del.className = "delete";
    del.textContent = "✕";
    del.setAttribute("aria-label", `Delete “${task.title}”`);
    del.addEventListener("click", () => run(() => deleteTask(task)));

    li.append(box, label, del);
    return li;
}

function render() {
    $("tasks").replaceChildren(...tasks.map(taskItem));
    const done = tasks.filter((t) => t.done).length;
    $("empty").hidden = !tasksLoaded || tasks.length > 0;
    $("progress").textContent = tasks.length ? `${done} of ${tasks.length} done` : "";
}

function showError(message) {
    $("error").textContent = message;
    $("error").hidden = false;
}

function clearError() {
    $("error").hidden = true;
}

// Runs an action, shows any failure, and re-syncs the list so the UI never lies.
async function run(action) {
    clearError();
    try {
        await action();
    } catch (err) {
        showError(err.message);
        render();
        if (err.status === 404) refreshTasks().catch(() => {});
    }
}

// ---------- Actions ----------

async function refreshTasks() {
    tasks = await api("/api/tasks");
    tasksLoaded = true;
    render();
}

async function addTask(title) {
    const task = await api("/api/tasks", { method: "POST", body: JSON.stringify({ title }) });
    tasks.push(task);
    render();
}

async function setDone(task, done) {
    const updated = await api(`/api/tasks/${task.id}`, {
        method: "PATCH",
        body: JSON.stringify({ done }),
    });
    tasks = tasks.map((t) => (t.id === updated.id ? updated : t));
    render();
}

async function deleteTask(task) {
    await api(`/api/tasks/${task.id}`, { method: "DELETE" });
    tasks = tasks.filter((t) => t.id !== task.id);
    render();
}

// ---------- Wiring ----------

$("task-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const input = $("task-input");
    const title = input.value.trim();
    if (!title) return;
    run(async () => {
        await addTask(title);
        input.value = "";
        input.focus();
    });
});

$("rename-btn").addEventListener("click", () => {
    const form = $("name-form");
    form.hidden = !form.hidden;
    if (!form.hidden) {
        $("name-input").value = currentName;
        $("name-input").focus();
    }
});

$("name-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const name = $("name-input").value.trim();
    if (!name) return;
    currentName = name;
    saveName(name);
    $("name-form").hidden = true;
    $("rename-btn").focus();
    run(loadGreeting);
});

showToday();
run(loadGreeting);
run(refreshTasks);

// Keep the greeting and sky in step as the day moves on.
setInterval(() => {
    showToday();
    loadGreeting().catch(() => {});
}, 60_000);
