"""FR-02 / FR-03: propose, browse, search and filter capstone ideas."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .db import get_db
from .security import login_required

bp = Blueprint("ideas", __name__, url_prefix="/ideas")
NAV = [("Idea Bank", "ideas.index", None)]

DOMAINS = ["AI/ML", "Web", "Mobile", "IoT", "Security", "Data Science", "Cloud", "Other"]


def get_idea(idea_id):
    idea = get_db().execute(
        "SELECT i.*, u.name AS author_name,"
        " (SELECT COUNT(*) FROM votes v WHERE v.idea_id = i.id) AS votes,"
        " (SELECT COUNT(*) FROM votes v WHERE v.idea_id = i.id AND v.user_id = ?) AS voted,"
        " t.id AS team_id, t.name AS team_name"
        " FROM ideas i JOIN users u ON u.id = i.author_id"
        " LEFT JOIN teams t ON t.idea_id = i.id WHERE i.id = ?",
        (g.user["id"], idea_id),
    ).fetchone()
    if idea is None:
        abort(404)
    return idea


def validate_idea(form):
    errors = []
    title = form.get("title", "").strip()
    if not 5 <= len(title) <= 120:
        errors.append("Title must be 5-120 characters.")
    if len(form.get("description", "").strip()) < 20:
        errors.append("Description must be at least 20 characters.")
    if form.get("domain") not in DOMAINS:
        errors.append("Choose a domain.")
    return errors


def clean_tags(raw):
    tags = [t.strip().lower() for t in raw.split(",") if t.strip()]
    return ", ".join(dict.fromkeys(tags))  # de-duplicate, keep order


def can_edit(idea):
    return g.user["id"] == idea["author_id"] or g.user["role"] == "admin"


@bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    domain = request.args.get("domain", "")
    sort = request.args.get("sort", "new")
    sql = ("SELECT i.*, u.name AS author_name, COUNT(v.user_id) AS votes,"
           " SUM(v.user_id = ?) AS voted, t.name AS team_name"
           " FROM ideas i JOIN users u ON u.id = i.author_id"
           " LEFT JOIN votes v ON v.idea_id = i.id"
           " LEFT JOIN teams t ON t.idea_id = i.id")
    params, where = [g.user["id"]], []
    if q:
        where.append("(i.title LIKE ? OR i.description LIKE ? OR i.tags LIKE ?)")
        params += [f"%{q}%"] * 3
    if domain in DOMAINS:
        where.append("i.domain = ?")
        params.append(domain)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " GROUP BY i.id"
    sql += " ORDER BY votes DESC, i.id DESC" if sort == "votes" else " ORDER BY i.id DESC"
    ideas = get_db().execute(sql, params).fetchall()
    return render_template("ideas/index.html", ideas=ideas, q=q, domain=domain,
                           sort=sort, domains=DOMAINS)


@bp.route("/new", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        errors = validate_idea(request.form)
        if not errors:
            db = get_db()
            cur = db.execute(
                "INSERT INTO ideas (title, description, domain, tags, author_id) VALUES (?, ?, ?, ?, ?)",
                (request.form["title"].strip(), request.form["description"].strip(),
                 request.form["domain"], clean_tags(request.form.get("tags", "")), g.user["id"]),
            )
            db.commit()
            flash("Idea published to the idea bank.", "success")
            return redirect(url_for("ideas.detail", idea_id=cur.lastrowid))
        for error in errors:
            flash(error, "error")
    return render_template("ideas/form.html", idea=None, domains=DOMAINS)


@bp.route("/<int:idea_id>")
@login_required
def detail(idea_id):
    return render_template("ideas/detail.html", idea=get_idea(idea_id), can_edit=can_edit)


@bp.route("/<int:idea_id>/edit", methods=("GET", "POST"))
@login_required
def edit(idea_id):
    idea = get_idea(idea_id)
    if not can_edit(idea):
        abort(403)
    if request.method == "POST":
        errors = validate_idea(request.form)
        if not errors:
            db = get_db()
            db.execute(
                "UPDATE ideas SET title = ?, description = ?, domain = ?, tags = ? WHERE id = ?",
                (request.form["title"].strip(), request.form["description"].strip(),
                 request.form["domain"], clean_tags(request.form.get("tags", "")), idea_id),
            )
            db.commit()
            flash("Idea updated.", "success")
            return redirect(url_for("ideas.detail", idea_id=idea_id))
        for error in errors:
            flash(error, "error")
    return render_template("ideas/form.html", idea=idea, domains=DOMAINS)


@bp.route("/<int:idea_id>/delete", methods=("POST",))
@login_required
def delete(idea_id):
    idea = get_idea(idea_id)
    if not can_edit(idea):
        abort(403)
    if idea["team_id"]:
        flash("This idea has been claimed by a team and cannot be deleted.", "error")
        return redirect(url_for("ideas.detail", idea_id=idea_id))
    db = get_db()
    db.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
    db.commit()
    flash("Idea deleted.", "info")
    return redirect(url_for("ideas.index"))
