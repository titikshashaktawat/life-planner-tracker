from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# ===== DATABASE =====
def get_db():
    return sqlite3.connect("database.db")

def init_db():
    db = get_db()
    db.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT,
        priority TEXT,
        category TEXT,
        recurring TEXT,
        status TEXT,
        last_done TEXT
    )
    ''')
    db.commit()
    db.close()

init_db()

# ===== HOME PAGE =====
@app.route('/')
def home():
    db = get_db()
    tasks = db.execute("SELECT * FROM tasks").fetchall()

    today = datetime.today().strftime("%Y-%m-%d")

    # Handle recurring tasks
    for t in tasks:
        if len(t) < 7:
            continue

        task_id = t[0]
        recurring = t[4]
        last_done = t[6] or ""

        if recurring == "Daily":
            if last_done != today:
                db.execute("UPDATE tasks SET status='Pending' WHERE id=?", (task_id,))

        elif recurring == "Weekly":
            if last_done:
                try:
                    last_date = datetime.strptime(last_done, "%Y-%m-%d")
                    if (datetime.today() - last_date).days >= 7:
                        db.execute("UPDATE tasks SET status='Pending' WHERE id=?", (task_id,))
                except:
                    db.execute("UPDATE tasks SET status='Pending' WHERE id=?", (task_id,))
            else:
                db.execute("UPDATE tasks SET status='Pending' WHERE id=?", (task_id,))

    db.commit()

    tasks = db.execute("SELECT * FROM tasks").fetchall()
    db.close()

    done = len([t for t in tasks if t[5] == "Done"])
    total = len(tasks)
    progress = int((done / total) * 100) if total else 0

    return render_template("index.html", tasks=tasks, progress=progress)

# ===== ADD TASK =====
@app.route('/add', methods=['POST'])
def add():
    task = request.form.get('task')
    priority = request.form.get('priority')
    category = request.form.get('category')
    recurring = request.form.get('recurring')

    if not task:
        return redirect('/')

    db = get_db()
    db.execute(
        "INSERT INTO tasks VALUES (NULL, ?, ?, ?, ?, ?, ?)",
        (task, priority, category, recurring, "Pending", "")
    )
    db.commit()
    db.close()

    return redirect('/')

# ===== COMPLETE TASK =====
@app.route('/complete/<int:id>')
def complete(id):
    today = datetime.today().strftime("%Y-%m-%d")

    db = get_db()
    db.execute(
        "UPDATE tasks SET status='Done', last_done=? WHERE id=?",
        (today, id)
    )
    db.commit()
    db.close()

    return redirect('/')

# ===== DELETE TASK =====
@app.route('/delete/<int:id>')
def delete(id):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id=?", (id,))
    db.commit()
    db.close()

    return redirect('/')

# ===== WORKOUT PAGE =====
@app.route('/workout')
def workout():
    return render_template("workout.html")

# ===== STUDY PAGE =====
@app.route('/study', methods=['GET', 'POST'])
def study():
    db = get_db()

    if request.method == 'POST':
        task = request.form.get('task')

        if task:
            db.execute(
                "INSERT INTO tasks VALUES (NULL, ?, ?, ?, ?, ?, ?)",
                (task, "Medium", "Study", "None", "Pending", "")
            )
            db.commit()

        return redirect('/study')

    tasks = db.execute(
        "SELECT * FROM tasks WHERE category='Study'"
    ).fetchall()

    db.close()

    return render_template("study.html", tasks=tasks)

# ===== PERIOD PAGE =====
@app.route('/period')
def period():
    return render_template("period.html")

# ===== RUN APP =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
