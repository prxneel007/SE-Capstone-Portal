"""Tiny in-process event bus so feature modules stay decoupled.

Example: submissions emit "submission_created"; the plagiarism and
notifications modules subscribe to it without submissions knowing about them.
"""
from flask import current_app


def subscribe(app, event, handler):
    app.extensions.setdefault("capstone_events", {}).setdefault(event, []).append(handler)


def emit(event, **data):
    for handler in current_app.extensions.get("capstone_events", {}).get(event, []):
        handler(**data)
