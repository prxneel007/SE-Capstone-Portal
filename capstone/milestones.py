"""FR-07 / FR-08: mentors set milestones with due dates; teams update status;
progress and overdue milestones are computed for dashboards."""
from datetime import date

from flask import Blueprint, abort, flash, redirect, request, url_for

from .db import get_db, today
from .security import login_required
from .teams import get_team, is_member, is_staff_for, team_of

bp = Blueprint("milestones", __name__)

STATUSES = ("pending", "in_progress", "done")


def team_milestones(team_id):
    rows = get_db().execute(
        "SELECT * FROM milestones WHERE team_id = ? ORDER BY due_date, id", (team_id,)
    ).fetchall()
    now = today().isoformat()
    return [dict(m, overdue=m["status"] != "done" and m["due_date"] < now) for m in rows]


def progress(team_id):
    items = team_milestones(team_id)
    done = sum(m["status"] == "done" for m in items)
    return {
        "total": len(items),
        "done": done,
        "percent": round(100 * done / len(items)) if items else 0,
        "overdue": sum(m["overdue"] for m in items),
    }


def parse_due(value):
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError):
        return None


def get_milestone(milestone_id):
    m = get_db().execute("SELECT * FROM milestones WHERE id = ?", (milestone_id,)).fetchone()
    if m is None:
        abort(404)
    return m


@bp.route("/teams/<int:team_id>/milestones", methods=("POST",))
@login_required
def create(team_id):
    if not is_staff_for(get_team(team_id)):
        abort(403)
    title = request.form.get("title", "").strip()
    due = parse_due(request.form.get("due_date"))
    if not title or len(title) > 120:
        flash("Milestone title is required (max 120 characters).", "error")
    elif due is None:
        flash("Enter a valid due date.", "error")
    else:
        db = get_db()
        db.execute("INSERT INTO milestones (team_id, title, description, due_date) VALUES (?, ?, ?, ?)",
                   (team_id, title, request.form.get("description", "").strip(), due))
        db.commit()
        flash("Milestone added.", "success")
    return redirect(url_for("teams.detail", team_id=team_id))


@bp.route("/milestones/<int:milestone_id>/status", methods=("POST",))
@login_required
def update_status(milestone_id):
    m = get_milestone(milestone_id)
    if not (is_member(m["team_id"]) or is_staff_for(get_team(m["team_id"]))):
        abort(403)
    status = request.form.get("status")
    if status not in STATUSES:
        abort(400)
    db = get_db()
    db.execute("UPDATE milestones SET status = ? WHERE id = ?", (status, milestone_id))
    db.commit()
    flash("Milestone updated.", "success")
    return redirect(url_for("teams.detail", team_id=m["team_id"]))


@bp.route("/milestones/<int:milestone_id>/delete", methods=("POST",))
@login_required
def delete(milestone_id):
    m = get_milestone(milestone_id)
    if not is_staff_for(get_team(m["team_id"])):
        abort(403)
    db = get_db()
    db.execute("DELETE FROM milestones WHERE id = ?", (milestone_id,))
    db.commit()
    flash("Milestone deleted.", "info")
    return redirect(url_for("teams.detail", team_id=m["team_id"]))


def init_module(app):
    app.jinja_env.globals.update(team_milestones=team_milestones, milestone_progress=progress,
                                 milestone_statuses=STATUSES)


def dashboard_widget(user):
    if user["role"] != "student":
        return None
    team_id = team_of(user["id"])
    if team_id is None:
        return None
    upcoming = [m for m in team_milestones(team_id) if m["status"] != "done"][:4]
    return {"template": "widgets/milestones.html", "team_id": team_id,
            "progress": progress(team_id), "upcoming": upcoming}
