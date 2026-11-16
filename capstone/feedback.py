"""FR-11: faculty leave comments and an optional grade on a submitted report."""
from flask import Blueprint, abort, flash, g, redirect, request, url_for

from .db import get_db
from .events import emit
from .security import role_required
from .teams import team_of

bp = Blueprint("feedback", __name__)

GRADES = ("", "A", "B", "C", "D", "F")


def submission_feedback(submission_id):
    return get_db().execute(
        "SELECT f.*, u.name AS faculty_name FROM feedback f JOIN users u ON u.id = f.faculty_id"
        " WHERE f.submission_id = ? ORDER BY f.created_at, f.id", (submission_id,)
    ).fetchall()


@bp.route("/submissions/<int:submission_id>/feedback", methods=("POST",))
@role_required("faculty", "admin")
def create(submission_id):
    db = get_db()
    sub = db.execute("SELECT id, team_id FROM submissions WHERE id = ?", (submission_id,)).fetchone()
    if sub is None:
        abort(404)
    comment = request.form.get("comment", "").strip()
    grade = request.form.get("grade", "")
    if not comment or len(comment) > 2000:
        flash("Feedback must be 1-2000 characters.", "error")
    elif grade not in GRADES:
        flash("Choose a valid grade.", "error")
    else:
        db.execute("INSERT INTO feedback (submission_id, faculty_id, comment, grade) VALUES (?, ?, ?, ?)",
                   (submission_id, g.user["id"], comment, grade))
        db.commit()
        emit("feedback_added", submission_id=submission_id, team_id=sub["team_id"])
        flash("Feedback posted.", "success")
    return redirect(url_for("submissions.detail", submission_id=submission_id))


def init_module(app):
    app.jinja_env.globals.update(submission_feedback=submission_feedback, feedback_grades=GRADES)


def dashboard_widget(user):
    if user["role"] != "student" or team_of(user["id"]) is None:
        return None
    latest = get_db().execute(
        "SELECT f.comment, f.grade, f.created_at, u.name AS faculty_name, s.id AS submission_id, s.filename"
        " FROM feedback f JOIN submissions s ON s.id = f.submission_id JOIN users u ON u.id = f.faculty_id"
        " WHERE s.team_id = ? ORDER BY f.created_at DESC, f.id DESC LIMIT 3", (team_of(user["id"]),)
    ).fetchall()
    return {"template": "widgets/feedback.html", "items": latest}
