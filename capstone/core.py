from flask import Blueprint, current_app, g, redirect, render_template, url_for

from .db import get_db

bp = Blueprint("core", __name__)


@bp.route("/")
def home():
    if g.user and "dashboard" in current_app.blueprints:
        return redirect(url_for("dashboard.index"))
    return render_template("home.html")


@bp.route("/health")
def health():
    get_db().execute("SELECT 1")
    return {"status": "ok"}
