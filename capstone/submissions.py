"""FR-09: teams upload versioned reports (.txt, .md, .pdf) against a milestone."""
import io
import os
import uuid

from flask import (Blueprint, abort, current_app, flash, g, redirect, render_template, request,
                   send_from_directory, url_for)

from .db import get_db
from .events import emit
from .security import login_required
from .teams import get_team, is_member, is_staff_for

bp = Blueprint("submissions", __name__)

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}


class UnreadableFile(ValueError):
    pass


def extract_text(data, ext):
    """Plain text of an uploaded report, used for the plagiarism check."""
    if ext == ".pdf":
        from pypdf import PdfReader
        try:
            reader = PdfReader(io.BytesIO(data))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:  # pypdf raises many types for malformed files
            raise UnreadableFile("Could not read that PDF.") from exc
    return data.decode("utf-8", errors="replace")


def get_submission(submission_id):
    s = get_db().execute(
        "SELECT s.*, u.name AS submitter, m.title AS milestone_title, t.name AS team_name"
        " FROM submissions s JOIN users u ON u.id = s.submitted_by"
        " JOIN teams t ON t.id = s.team_id"
        " LEFT JOIN milestones m ON m.id = s.milestone_id WHERE s.id = ?", (submission_id,)
    ).fetchone()
    if s is None:
        abort(404)
    return s


def can_view(submission):
    return g.user["role"] in ("faculty", "admin") or is_member(submission["team_id"])


def team_submissions(team_id):
    return get_db().execute(
        "SELECT s.*, u.name AS submitter, m.title AS milestone_title"
        " FROM submissions s JOIN users u ON u.id = s.submitted_by"
        " LEFT JOIN milestones m ON m.id = s.milestone_id"
        " WHERE s.team_id = ? ORDER BY s.created_at DESC, s.id DESC", (team_id,)
    ).fetchall()


@bp.route("/teams/<int:team_id>/submissions", methods=("POST",))
@login_required
def upload(team_id):
    get_team(team_id)
    if not is_member(team_id):
        abort(403)
    back = redirect(url_for("teams.detail", team_id=team_id))
    file = request.files.get("report")
    if file is None or not file.filename:
        flash("Choose a file to upload.", "error")
        return back
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        flash("Only .txt, .md and .pdf reports are accepted.", "error")
        return back
    db = get_db()
    milestone_id = request.form.get("milestone_id", type=int)
    if milestone_id and not db.execute("SELECT 1 FROM milestones WHERE id = ? AND team_id = ?",
                                       (milestone_id, team_id)).fetchone():
        abort(400)
    data = file.read()
    if not data:
        flash("That file is empty.", "error")
        return back
    try:
        text = extract_text(data, ext)
    except UnreadableFile as exc:
        flash(str(exc), "error")
        return back
    stored = uuid.uuid4().hex + ext
    with open(os.path.join(current_app.config["UPLOAD_FOLDER"], stored), "wb") as fh:
        fh.write(data)
    version = db.execute("SELECT COUNT(*) FROM submissions WHERE team_id = ? AND milestone_id IS ?",
                         (team_id, milestone_id)).fetchone()[0] + 1
    cur = db.execute(
        "INSERT INTO submissions (team_id, milestone_id, filename, stored_name, text_content, version,"
        " submitted_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (team_id, milestone_id, os.path.basename(file.filename)[:200], stored, text, version, g.user["id"]),
    )
    db.commit()
    emit("submission_created", submission_id=cur.lastrowid)
    flash(f"Report uploaded (version {version}).", "success")
    return redirect(url_for("submissions.detail", submission_id=cur.lastrowid))


@bp.route("/submissions/<int:submission_id>")
@login_required
def detail(submission_id):
    s = get_submission(submission_id)
    if not can_view(s):
        abort(403)
    return render_template("submissions/detail.html", s=s, team=get_team(s["team_id"]),
                           is_staff=is_staff_for(get_team(s["team_id"])))


@bp.route("/submissions/<int:submission_id>/download")
@login_required
def download(submission_id):
    s = get_submission(submission_id)
    if not can_view(s):
        abort(403)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], s["stored_name"],
                               as_attachment=True, download_name=s["filename"])


def init_module(app):
    app.jinja_env.globals["team_submissions"] = team_submissions
