"""FR-05: create a team, join with an invite code, leave; one team per student."""
import secrets
import sqlite3

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for

from .db import get_db
from .security import login_required, role_required

bp = Blueprint("teams", __name__, url_prefix="/teams")
NAV = [("My Team", "teams.index", ("student",)), ("Teams", "teams.index", ("faculty", "admin"))]


def get_team(team_id):
    team = get_db().execute(
        "SELECT t.*, i.title AS idea_title, m.name AS mentor_name"
        " FROM teams t LEFT JOIN ideas i ON i.id = t.idea_id"
        " LEFT JOIN users m ON m.id = t.mentor_id WHERE t.id = ?", (team_id,)
    ).fetchone()
    if team is None:
        abort(404)
    return team


def team_of(user_id):
    """The team id a student belongs to, or None."""
    row = get_db().execute("SELECT team_id FROM team_members WHERE user_id = ?", (user_id,)).fetchone()
    return row["team_id"] if row else None


def members(team_id):
    return get_db().execute(
        "SELECT u.id, u.name, u.email, u.srn FROM team_members tm JOIN users u ON u.id = tm.user_id"
        " WHERE tm.team_id = ? ORDER BY tm.joined_at, u.name", (team_id,)
    ).fetchall()


def is_member(team_id, user=None):
    user = user or g.user
    return team_of(user["id"]) == team_id


def is_staff_for(team, user=None):
    """Admins, and the team's mentor, can manage it; any faculty can view it."""
    user = user or g.user
    return user["role"] == "admin" or (user["role"] == "faculty" and team["mentor_id"] == user["id"])


@bp.route("/")
@login_required
def index():
    if g.user["role"] == "student":
        team_id = team_of(g.user["id"])
        if team_id:
            return redirect(url_for("teams.detail", team_id=team_id))
        return render_template("teams/join.html")
    teams = get_db().execute(
        "SELECT t.*, i.title AS idea_title, m.name AS mentor_name,"
        " (SELECT COUNT(*) FROM team_members tm WHERE tm.team_id = t.id) AS size"
        " FROM teams t LEFT JOIN ideas i ON i.id = t.idea_id"
        " LEFT JOIN users m ON m.id = t.mentor_id ORDER BY t.name"
    ).fetchall()
    return render_template("teams/list.html", teams=teams)


@bp.route("/create", methods=("POST",))
@role_required("student")
def create():
    name = request.form.get("name", "").strip()
    if team_of(g.user["id"]):
        flash("You are already in a team.", "error")
    elif not 3 <= len(name) <= 50:
        flash("Team name must be 3-50 characters.", "error")
    else:
        db = get_db()
        try:
            cur = db.execute("INSERT INTO teams (name, invite_code, created_by) VALUES (?, ?, ?)",
                             (name, secrets.token_hex(4).upper(), g.user["id"]))
        except sqlite3.IntegrityError:
            flash("That team name is taken.", "error")
            return redirect(url_for("teams.index"))
        db.execute("INSERT INTO team_members (team_id, user_id) VALUES (?, ?)", (cur.lastrowid, g.user["id"]))
        db.commit()
        flash("Team created. Share the invite code with your teammates.", "success")
        return redirect(url_for("teams.detail", team_id=cur.lastrowid))
    return redirect(url_for("teams.index"))


@bp.route("/join", methods=("POST",))
@role_required("student")
def join():
    code = request.form.get("code", "").strip().upper()
    db = get_db()
    team = db.execute("SELECT id FROM teams WHERE invite_code = ?", (code,)).fetchone()
    if team_of(g.user["id"]):
        flash("You are already in a team.", "error")
    elif team is None:
        flash("No team has that invite code.", "error")
    elif len(members(team["id"])) >= current_app.config["MAX_TEAM_SIZE"]:
        flash("That team is full.", "error")
    else:
        db.execute("INSERT INTO team_members (team_id, user_id) VALUES (?, ?)", (team["id"], g.user["id"]))
        db.commit()
        flash("You joined the team.", "success")
        return redirect(url_for("teams.detail", team_id=team["id"]))
    return redirect(url_for("teams.index"))


@bp.route("/<int:team_id>")
@login_required
def detail(team_id):
    team = get_team(team_id)
    if g.user["role"] == "student" and not is_member(team_id):
        abort(403)
    return render_template("teams/detail.html", team=team, members=members(team_id),
                           is_member=is_member(team_id), is_staff=is_staff_for(team))


@bp.route("/<int:team_id>/leave", methods=("POST",))
@role_required("student")
def leave(team_id):
    if not is_member(team_id):
        abort(403)
    db = get_db()
    last = len(members(team_id)) == 1
    if last and db.execute("SELECT 1 FROM submissions WHERE team_id = ?", (team_id,)).fetchone():
        # Leaving would delete the team and its submitted reports.
        flash("You are the last member and the team has submissions, so you can't leave.", "error")
        return redirect(url_for("teams.detail", team_id=team_id))
    db.execute("DELETE FROM team_members WHERE team_id = ? AND user_id = ?", (team_id, g.user["id"]))
    if last:
        db.execute("DELETE FROM teams WHERE id = ?", (team_id,))
    db.commit()
    flash("You left the team.", "info")
    return redirect(url_for("teams.index"))


def dashboard_widget(user):
    if user["role"] != "student":
        return None
    team_id = team_of(user["id"])
    return {"template": "widgets/team.html", "team": get_team(team_id) if team_id else None,
            "members": members(team_id) if team_id else []}
