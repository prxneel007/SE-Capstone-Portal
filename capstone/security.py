"""Session user loading, CSRF protection and access-control decorators (NFR-01)."""
import functools
import secrets

from flask import abort, current_app, g, redirect, request, session, url_for
from markupsafe import Markup

from .db import get_db


def login_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login", next=request.path))
        return view(**kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @login_required
        @functools.wraps(view)
        def wrapped(**kwargs):
            if g.user["role"] not in roles:
                abort(403)
            return view(**kwargs)
        return wrapped
    return decorator


def safe_next(target, default):
    """Only allow same-site relative redirects (blocks open redirects)."""
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return default


def init_app(app):
    @app.before_request
    def load_user_and_check_csrf():
        user_id = session.get("user_id")
        g.user = None
        if user_id is not None:
            g.user = get_db().execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        if request.method == "POST" and not app.config.get("CSRF_DISABLED"):
            expected = session.get("csrf_token", "")
            sent = request.form.get("csrf_token", "")
            if not expected or not secrets.compare_digest(expected, sent):
                abort(400, "Invalid or missing CSRF token.")

    @app.context_processor
    def template_helpers():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(16)
        token = session["csrf_token"]
        role = g.user["role"] if g.get("user") else None
        nav = [(label, endpoint) for label, endpoint, roles in current_app.config["NAV"]
               if role and (roles is None or role in roles)]
        return {
            "csrf_token": token,
            "csrf_field": Markup(f'<input type="hidden" name="csrf_token" value="{token}">'),
            "has": lambda name: name in current_app.blueprints,
            "nav_items": nav,
        }
