"""FR-04: one vote per user per idea (toggle); authors cannot vote for their own idea."""
from flask import Blueprint, abort, flash, g, redirect, request, url_for

from .db import get_db
from .security import login_required, safe_next

bp = Blueprint("votes", __name__, url_prefix="/ideas")


@bp.route("/<int:idea_id>/vote", methods=("POST",))
@login_required
def toggle(idea_id):
    db = get_db()
    idea = db.execute("SELECT author_id FROM ideas WHERE id = ?", (idea_id,)).fetchone()
    if idea is None:
        abort(404)
    back = safe_next(request.form.get("next"), url_for("ideas.detail", idea_id=idea_id))
    if idea["author_id"] == g.user["id"]:
        flash("You can't vote for your own idea.", "error")
        return redirect(back)
    removed = db.execute("DELETE FROM votes WHERE user_id = ? AND idea_id = ?",
                         (g.user["id"], idea_id)).rowcount
    if not removed:
        db.execute("INSERT INTO votes (user_id, idea_id) VALUES (?, ?)", (g.user["id"], idea_id))
    db.commit()
    flash("Vote removed." if removed else "Thanks for voting!", "info")
    return redirect(back)
