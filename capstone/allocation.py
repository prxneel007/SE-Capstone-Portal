"""FR-06: a team claims an idea (one idea per team, one team per idea);
faculty take on teams as mentor, admins can assign any faculty member."""
import sqlite3

from flask import Blueprint, abort, flash, g, redirect, request, url_for

from .db import get_db
from .security import login_required, role_required
from .teams import get_team, is_member, is_staff_for, team_of

bp = Blueprint("allocation", __name__)


@bp.route("/ideas/<int:idea_id>/claim", methods=("POST",))
@role_required("student")
def claim(idea_id):
    db = get_db()
    if db.execute("SELECT 1 FROM ideas WHERE id = ?", (idea_id,)).fetchone() is None:
        abort(404)
    team_id = team_of(g.user["id"])
    back = url_for("ideas.detail", idea_id=idea_id)
    if team_id is None:
        flash("Join or create a team before claiming an idea.", "error")
        return redirect(back)
    if get_team(team_id)["idea_id"]:
        flash("Your team has already claimed an idea. Release it first.", "error")
        return redirect(back)
    try:
        db.execute("UPDATE teams SET idea_id = ? WHERE id = ?", (idea_id, team_id))
        db.commit()
    except sqlite3.IntegrityError:  # UNIQUE(idea_id): another team got there first
        flash("Another team has already claimed this idea.", "error")
        return redirect(back)
    flash("Idea claimed for your team.", "success")
    return redirect(url_for("teams.detail", team_id=team_id))


@bp.route("/teams/<int:team_id>/release", methods=("POST",))
@login_required
def release(team_id):
    team = get_team(team_id)
    if not (is_member(team_id) or is_staff_for(team)):
        abort(403)
    db = get_db()
    db.execute("UPDATE teams SET idea_id = NULL WHERE id = ?", (team_id,))
    db.commit()
    flash("Idea released back to the idea bank.", "info")
    return redirect(url_for("teams.detail", team_id=team_id))


@bp.route("/teams/<int:team_id>/mentor", methods=("POST",))
@role_required("faculty", "admin")
def set_mentor(team_id):
    team = get_team(team_id)
    db = get_db()
    if g.user["role"] == "admin":
        mentor_id = request.form.get("faculty_id", type=int)
        faculty = db.execute("SELECT 1 FROM users WHERE id = ? AND role = 'faculty'", (mentor_id,)).fetchone()
        if faculty is None:
            flash("Choose a faculty member.", "error")
            return redirect(url_for("teams.detail", team_id=team_id))
    else:
        if team["mentor_id"] and team["mentor_id"] != g.user["id"]:
            flash("This team already has a mentor.", "error")
            return redirect(url_for("teams.detail", team_id=team_id))
        mentor_id = g.user["id"]
    db.execute("UPDATE teams SET mentor_id = ? WHERE id = ?", (mentor_id, team_id))
    db.commit()
    flash("Mentor assigned.", "success")
    return redirect(url_for("teams.detail", team_id=team_id))


@bp.route("/teams/<int:team_id>/unmentor", methods=("POST",))
@role_required("faculty", "admin")
def remove_mentor(team_id):
    if not is_staff_for(get_team(team_id)):
        abort(403)
    db = get_db()
    db.execute("UPDATE teams SET mentor_id = NULL WHERE id = ?", (team_id,))
    db.commit()
    flash("Mentor removed.", "info")
    return redirect(url_for("teams.detail", team_id=team_id))


def faculty_list():
    return get_db().execute("SELECT id, name FROM users WHERE role = 'faculty' ORDER BY name").fetchall()


def init_module(app):
    app.jinja_env.globals["faculty_list"] = faculty_list
    app.jinja_env.globals["team_of"] = team_of


def dashboard_widget(user):
    if user["role"] != "faculty":
        return None
    teams = get_db().execute(
        "SELECT t.id, t.name, i.title AS idea_title FROM teams t LEFT JOIN ideas i ON i.id = t.idea_id"
        " WHERE t.mentor_id = ? ORDER BY t.name", (user["id"],)
    ).fetchall()
    return {"template": "widgets/mentored.html", "teams": teams}
