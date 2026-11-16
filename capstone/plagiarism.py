"""FR-10: plagiarism check. Every new report is compared with all other teams'
reports using 5-word shingles and Jaccard similarity; scores at or above
PLAGIARISM_THRESHOLD are flagged for faculty review."""
import re

from flask import Blueprint, current_app, render_template

from .db import get_db
from .events import emit, subscribe
from .security import role_required

bp = Blueprint("plagiarism", __name__, url_prefix="/plagiarism")
NAV = [("Plagiarism", "plagiarism.index", ("faculty", "admin"))]

WORD_RE = re.compile(r"[a-z0-9]+")
SHINGLE_SIZE = 5


def shingles(text, k=SHINGLE_SIZE):
    words = WORD_RE.findall(text.lower())
    if len(words) < k:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i:i + k]) for i in range(len(words) - k + 1)}


def similarity(a, b):
    """Jaccard similarity of two texts' shingle sets, 0.0 to 1.0."""
    sa, sb = shingles(a), shingles(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def best_match(text, candidates):
    """(score, id) of the most similar candidate; candidates are (id, text) pairs."""
    best = (0.0, None)
    target = shingles(text)
    if not target:
        return best
    for cid, other in candidates:
        theirs = shingles(other)
        if theirs:
            score = len(target & theirs) / len(target | theirs)
            if score > best[0]:
                best = (score, cid)
    return best


def check_submission(submission_id):
    db = get_db()
    sub = db.execute("SELECT id, team_id, text_content FROM submissions WHERE id = ?",
                     (submission_id,)).fetchone()
    # shortcut: compares against every other team's report (O(n)); fine for one
    # cohort, switch to MinHash/LSH if the archive grows past a few thousand.
    others = db.execute("SELECT id, text_content FROM submissions WHERE team_id != ?",
                        (sub["team_id"],)).fetchall()
    score, match_id = best_match(sub["text_content"], [(o["id"], o["text_content"]) for o in others])
    db.execute("UPDATE submissions SET similarity = ?, similar_to = ? WHERE id = ?",
               (round(score, 4), match_id, submission_id))
    db.commit()
    if score >= current_app.config["PLAGIARISM_THRESHOLD"]:
        emit("plagiarism_flagged", submission_id=submission_id, score=score)
    return score, match_id


@bp.route("/")
@role_required("faculty", "admin")
def index():
    flagged = get_db().execute(
        "SELECT s.*, t.name AS team_name, o.filename AS match_filename, ot.name AS match_team"
        " FROM submissions s JOIN teams t ON t.id = s.team_id"
        " LEFT JOIN submissions o ON o.id = s.similar_to LEFT JOIN teams ot ON ot.id = o.team_id"
        " WHERE s.similarity >= ? ORDER BY s.similarity DESC",
        (current_app.config["PLAGIARISM_THRESHOLD"],)
    ).fetchall()
    return render_template("plagiarism/index.html", flagged=flagged)


def match_info(submission_id):
    return get_db().execute(
        "SELECT s.id, s.filename, t.name AS team_name FROM submissions s"
        " JOIN teams t ON t.id = s.team_id WHERE s.id = ?", (submission_id,)
    ).fetchone()


def init_module(app):
    subscribe(app, "submission_created", lambda submission_id: check_submission(submission_id))
    app.jinja_env.globals["plagiarism_match"] = match_info
