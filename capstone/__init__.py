"""Capstone Hub: idea bank, team formation, milestone tracking and reporting."""
import importlib
import os

from flask import Flask

# Feature modules, in load order. Each sprint story adds its module here.
MODULES = [
    "core",
    "auth",
    "dashboard",
    "ideas",
    "votes",
    "teams",
    "allocation",
]


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-me"),
        DATABASE=os.path.join(app.instance_path, "capstone.sqlite"),
        UPLOAD_FOLDER=os.path.join(app.instance_path, "uploads"),
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,  # NFR-04: 10 MB upload limit
        FACULTY_SIGNUP_CODE=os.environ.get("FACULTY_SIGNUP_CODE", "faculty-2026"),
        PLAGIARISM_THRESHOLD=0.4,
        REMINDER_DAYS=3,
        MAX_TEAM_SIZE=4,
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    from . import db, security
    db.init_app(app)
    security.init_app(app)

    nav, widgets = [], []
    for name in MODULES:
        module = importlib.import_module(f"{__name__}.{name}")
        if hasattr(module, "bp"):
            app.register_blueprint(module.bp)
        if hasattr(module, "init_module"):
            module.init_module(app)
        nav += getattr(module, "NAV", [])
        if hasattr(module, "dashboard_widget"):
            widgets.append(module.dashboard_widget)
    app.config["NAV"] = nav
    app.extensions["dashboard_widgets"] = widgets
    return app
