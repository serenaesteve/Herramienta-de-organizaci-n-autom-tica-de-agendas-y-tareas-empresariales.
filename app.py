from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "agendaai-secret-2025")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///agendaai.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")


# ──────────────────────────────────────────
# MODELOS
# ──────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    company = db.Column(db.String(100), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tasks = db.relationship("Task", backref="user", lazy=True, cascade="all, delete-orphan")
    events = db.relationship("Event", backref="user", lazy=True, cascade="all, delete-orphan")


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    priority = db.Column(db.String(10), default="media")  # alta / media / baja
    category = db.Column(db.String(50), default="General")
    due_date = db.Column(db.Date, nullable=True)
    due_time = db.Column(db.String(5), default="")
    done = db.Column(db.Boolean, default=False)
    ai_suggestion = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    event_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(5), default="09:00")
    end_time = db.Column(db.String(5), default="10:00")
    color = db.Column(db.String(20), default="meet")  # meet / dead / task / block
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ──────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def current_user():
    if "user_id" in session:
        return User.query.get(session["user_id"])
    return None


def ask_ollama(prompt):
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": "llama3", "prompt": prompt, "stream": False},
            timeout=30
        )
        if r.ok:
            return r.json().get("response", "").strip()
    except Exception:
        pass
    return None


# ──────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            return redirect(url_for("dashboard"))
        error = "Email o contraseña incorrectos"
    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        company = request.form.get("company", "").strip()
        if not name or not email or not password:
            error = "Todos los campos son obligatorios"
        elif User.query.filter_by(email=email).first():
            error = "Ya existe una cuenta con ese email"
        else:
            user = User(
                name=name,
                email=email,
                password=generate_password_hash(password),
                company=company
            )
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            session["user_name"] = user.name
            return redirect(url_for("dashboard"))
    return render_template("register.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ──────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    today = date.today()
    tasks = Task.query.filter_by(user_id=user.id).order_by(Task.due_date, Task.priority).all()
    events_today = Event.query.filter_by(user_id=user.id, event_date=today).order_by(Event.start_time).all()
    total = len(tasks)
    done = sum(1 for t in tasks if t.done)
    high = sum(1 for t in tasks if t.priority == "alta" and not t.done)
    return render_template("dashboard.html", user=user, tasks=tasks,
                           events_today=events_today, today=today,
                           total=total, done=done, high=high)


# ──────────────────────────────────────────
# TAREAS
# ──────────────────────────────────────────

@app.route("/tasks")
@login_required
def tasks():
    user = current_user()
    filter_pri = request.args.get("pri", "")
    filter_cat = request.args.get("cat", "")
    filter_done = request.args.get("done", "")
    q = Task.query.filter_by(user_id=user.id)
    if filter_pri:
        q = q.filter_by(priority=filter_pri)
    if filter_cat:
        q = q.filter_by(category=filter_cat)
    if filter_done == "0":
        q = q.filter_by(done=False)
    elif filter_done == "1":
        q = q.filter_by(done=True)
    tasks_list = q.order_by(Task.done, Task.due_date, Task.priority).all()
    cats = db.session.query(Task.category).filter_by(user_id=user.id).distinct().all()
    categories = [c[0] for c in cats]
    return render_template("tasks.html", user=user, tasks=tasks_list,
                           categories=categories, filter_pri=filter_pri,
                           filter_cat=filter_cat, filter_done=filter_done)


@app.route("/tasks/add", methods=["POST"])
@login_required
def add_task():
    user = current_user()
    title = request.form.get("title", "").strip()
    if not title:
        return redirect(url_for("tasks"))
    due_str = request.form.get("due_date", "")
    due_date = datetime.strptime(due_str, "%Y-%m-%d").date() if due_str else None
    task = Task(
        user_id=user.id,
        title=title,
        description=request.form.get("description", ""),
        priority=request.form.get("priority", "media"),
        category=request.form.get("category", "General"),
        due_date=due_date,
        due_time=request.form.get("due_time", ""),
    )
    db.session.add(task)
    db.session.commit()
    return redirect(url_for("tasks"))


@app.route("/tasks/toggle/<int:task_id>", methods=["POST"])
@login_required
def toggle_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=session["user_id"]).first_or_404()
    task.done = not task.done
    db.session.commit()
    return jsonify({"done": task.done})


@app.route("/tasks/delete/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=session["user_id"]).first_or_404()
    db.session.delete(task)
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/tasks/edit/<int:task_id>", methods=["POST"])
@login_required
def edit_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=session["user_id"]).first_or_404()
    task.title = request.form.get("title", task.title)
    task.description = request.form.get("description", task.description)
    task.priority = request.form.get("priority", task.priority)
    task.category = request.form.get("category", task.category)
    due_str = request.form.get("due_date", "")
    task.due_date = datetime.strptime(due_str, "%Y-%m-%d").date() if due_str else task.due_date
    task.due_time = request.form.get("due_time", task.due_time)
    db.session.commit()
    return redirect(url_for("tasks"))


# ──────────────────────────────────────────
# CALENDARIO
# ──────────────────────────────────────────

@app.route("/calendar")
@login_required
def calendar():
    user = current_user()
    return render_template("calendar.html", user=user)


@app.route("/api/events")
@login_required
def api_events():
    user = current_user()
    year = int(request.args.get("year", date.today().year))
    month = int(request.args.get("month", date.today().month))
    events = Event.query.filter(
        Event.user_id == user.id,
        db.extract("year", Event.event_date) == year,
        db.extract("month", Event.event_date) == month
    ).all()
    tasks = Task.query.filter(
        Task.user_id == user.id,
        db.extract("year", Task.due_date) == year,
        db.extract("month", Task.due_date) == month,
        Task.due_date != None
    ).all()
    result = []
    for e in events:
        result.append({
            "id": e.id, "type": "event",
            "title": e.title, "date": e.event_date.isoformat(),
            "start": e.start_time, "end": e.end_time,
            "color": e.color, "description": e.description
        })
    for t in tasks:
        result.append({
            "id": t.id, "type": "task",
            "title": t.title, "date": t.due_date.isoformat(),
            "priority": t.priority, "done": t.done
        })
    return jsonify(result)


@app.route("/events/add", methods=["POST"])
@login_required
def add_event():
    user = current_user()
    title = request.form.get("title", "").strip()
    if not title:
        return redirect(url_for("calendar"))
    event_date_str = request.form.get("event_date", "")
    event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date() if event_date_str else date.today()
    ev = Event(
        user_id=user.id,
        title=title,
        description=request.form.get("description", ""),
        event_date=event_date,
        start_time=request.form.get("start_time", "09:00"),
        end_time=request.form.get("end_time", "10:00"),
        color=request.form.get("color", "meet"),
    )
    db.session.add(ev)
    db.session.commit()
    return redirect(url_for("calendar"))


@app.route("/events/delete/<int:event_id>", methods=["POST"])
@login_required
def delete_event(event_id):
    ev = Event.query.filter_by(id=event_id, user_id=session["user_id"]).first_or_404()
    db.session.delete(ev)
    db.session.commit()
    return jsonify({"ok": True})


# ──────────────────────────────────────────
# ASISTENTE IA
# ──────────────────────────────────────────

@app.route("/ai", methods=["GET", "POST"])
@login_required
def ai_assistant():
    user = current_user()
    return render_template("ai.html", user=user)


@app.route("/api/ai/chat", methods=["POST"])
@login_required
def ai_chat():
    user = current_user()
    data = request.get_json()
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Mensaje vacío"}), 400

    tasks = Task.query.filter_by(user_id=user.id, done=False).order_by(Task.priority).all()
    tasks_ctx = "\n".join([f"- {t.title} (prioridad: {t.priority}, vence: {t.due_date or 'sin fecha'})" for t in tasks[:10]])

    prompt = f"""Eres un asistente de productividad empresarial para {user.name} que trabaja en {user.company or 'su empresa'}.
Tareas actuales pendientes:
{tasks_ctx or 'Sin tareas registradas.'}

El usuario dice: {message}

Responde en español con consejos concretos de organización, priorización y gestión del tiempo. Sé directo y práctico. Máximo 4 oraciones."""

    reply = ask_ollama(prompt)
    if not reply:
        reply = "No se pudo conectar con el asistente de IA. Asegúrate de que Ollama esté corriendo con el modelo llama3."
    return jsonify({"reply": reply})


@app.route("/api/ai/organize", methods=["POST"])
@login_required
def ai_organize():
    user = current_user()
    tasks = Task.query.filter_by(user_id=user.id, done=False).all()
    if not tasks:
        return jsonify({"reply": "No tienes tareas pendientes. ¡Añade algunas para que pueda organizarlas!"})

    task_list = "\n".join([f"- ID:{t.id} | {t.title} | prioridad: {t.priority} | vence: {t.due_date or 'sin fecha'}" for t in tasks])
    prompt = f"""Analiza estas tareas empresariales de {user.name} y crea un plan de trabajo óptimo para hoy.
Tareas:
{task_list}

Devuelve: 1) orden recomendado con justificación breve, 2) estimación de tiempo total, 3) un consejo de productividad. En español, máximo 150 palabras."""

    reply = ask_ollama(prompt)
    if not reply:
        reply = "No se pudo conectar con Ollama. Verifica que esté activo con: ollama run llama3"
    return jsonify({"reply": reply})


# ──────────────────────────────────────────
# PERFIL
# ──────────────────────────────────────────

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user()
    message = None
    if request.method == "POST":
        user.name = request.form.get("name", user.name).strip()
        user.company = request.form.get("company", user.company).strip()
        new_pass = request.form.get("new_password", "").strip()
        if new_pass:
            user.password = generate_password_hash(new_pass)
        db.session.commit()
        session["user_name"] = user.name
        message = "Perfil actualizado correctamente"
    return render_template("profile.html", user=user, message=message)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
