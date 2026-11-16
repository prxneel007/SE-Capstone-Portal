"""FR-12 / FR-13: in-app notifications and automated progress reminders.

Reminders run once per day automatically (on the first request of the day)
and can also be triggered from cron with `flask --app capstone send-reminders`.
"""
from datetime import timedelta

import click
from flask.cli import with_appcontext
from flask import Blueprint, abort, current_app, g, redirect, render_template, url_for

from .db import get_db, today
from .events import subscribe
from .security import login_required, safe_next

bp = Blueprint("notifications", __name__, url_prefix="/notifications")


def notify(user_id, message, link="", dedupe_key=None):
    """Store a notification; a repeated dedupe_key is ignored (no duplicate reminders)."""
    cur = get_db().execute(
        "INSERT OR IGNORE INTO notifications (user_id, message, link, dedupe_key) VALUES (?, ?, ?, ?)",
        (user_id, message, link, dedupe_key),
    )
    return cur.rowcount


def team_member_ids(team_id):
    return [r["user_id"] for r in get_db().execute(
        "SELECT user_id FROM team_members WHERE team_id = ?", (team_id,))]


def generate_reminders(on_date=None):
    """Create due-soon and overdue reminders for unfinished milestones. Returns how many were new."""
    db = get_db()
    on_date = on_date or today()
    soon = (on_date + timedelta(days=current_app.config["REMINDER_DAYS"])).isoformat()
    now = on_date.isoformat()
    rows = db.execute(
        "SELECT m.id, m.title, m.due_date, m.team_id, t.mentor_id FROM milestones m"
        " JOIN teams t ON t.id = m.team_id WHERE m.status != 'done' AND m.due_date <= ?", (soon,)
    ).fetchall()
    created = 0
    for m in rows:
        link = f"/teams/{m['team_id']}"
        if m["due_date"] < now:
            recipients = team_member_ids(m["team_id"]) + ([m["mentor_id"]] if m["mentor_id"] else [])
            for uid in recipients:
                created += notify(uid, f"Overdue: milestone '{m['title']}' was due on {m['due_date']}.",
                                  link, f"overdue:{m['id']}:{m['due_date']}:{uid}")
        else:
            for uid in team_member_ids(m["team_id"]):
                created += notify(uid, f"Reminder: milestone '{m['title']}' is due on {m['due_date']}.",
                                  link, f"due:{m['id']}:{m['due_date']}:{uid}")
    db.commit()
    return created


def run_daily_reminders():
    db = get_db()
    stamp = today().isoformat()
    row = db.execute("SELECT value FROM meta WHERE key = 'reminders_last_run'").fetchone()
    if row and row["value"] == stamp:
        return 0
    db.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('reminders_last_run', ?)", (stamp,))
    return generate_reminders()


def unread_count():
    if not g.get("user"):
        return 0
    return get_db().execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
                            (g.user["id"],)).fetchone()[0]


@bp.route("/")
@login_required
def index():
    items = get_db().execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY id DESC LIMIT 100",
                             (g.user["id"],)).fetchall()
    return render_template("notifications/index.html", items=items)


@bp.route("/<int:notification_id>/open", methods=("POST",))
@login_required
def open_one(notification_id):
    db = get_db()
    n = db.execute("SELECT * FROM notifications WHERE id = ? AND user_id = ?",
                   (notification_id, g.user["id"])).fetchone()
    if n is None:
        abort(404)
    db.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
    db.commit()
    return redirect(safe_next(n["link"], url_for("notifications.index")))


@bp.route("/read-all", methods=("POST",))
@login_required
def read_all():
    db = get_db()
    db.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (g.user["id"],))
    db.commit()
    return redirect(url_for("notifications.index"))


@click.command("send-reminders")
@with_appcontext
def send_reminders_command():
    """Generate milestone reminders now (for cron / scheduled jobs)."""
    click.echo(f"Created {generate_reminders()} reminder(s).")


# --- event subscribers -------------------------------------------------------

def _on_submission(submission_id):
    s = get_db().execute("SELECT s.filename, s.team_id, t.name, t.mentor_id FROM submissions s"
                         " JOIN teams t ON t.id = s.team_id WHERE s.id = ?", (submission_id,)).fetchone()
    if s["mentor_id"]:
        notify(s["mentor_id"], f"Team {s['name']} submitted '{s['filename']}'.", f"/submissions/{submission_id}")
        get_db().commit()


def _on_feedback(submission_id, team_id):
    for uid in team_member_ids(team_id):
        notify(uid, "New faculty feedback on your report.", f"/submissions/{submission_id}")
    get_db().commit()


def _on_plagiarism(submission_id, score):
    db = get_db()
    s = db.execute("SELECT t.name, t.mentor_id FROM submissions s JOIN teams t ON t.id = s.team_id"
                   " WHERE s.id = ?", (submission_id,)).fetchone()
    staff = [r["id"] for r in db.execute("SELECT id FROM users WHERE role = 'admin'")]
    if s["mentor_id"]:
        staff.append(s["mentor_id"])
    for uid in set(staff):
        notify(uid, f"Plagiarism check flagged a report from team {s['name']} ({round(score * 100)}% similar).",
               f"/submissions/{submission_id}")
    db.commit()


def init_module(app):
    app.cli.add_command(send_reminders_command)
    app.jinja_env.globals["unread_count"] = unread_count
    subscribe(app, "submission_created", _on_submission)
    subscribe(app, "feedback_added", _on_feedback)
    subscribe(app, "plagiarism_flagged", _on_plagiarism)

    @app.before_request
    def daily_reminders():
        if g.get("user") is not None:
            run_daily_reminders()
