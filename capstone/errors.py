"""Friendly error pages (NFR-03 usability)."""
from flask import Blueprint, render_template

bp = Blueprint("errors", __name__)

MESSAGES = {
    400: ("Bad request", "The form was invalid or expired. Go back, refresh the page and try again."),
    403: ("Not allowed", "You don't have permission to view this page."),
    404: ("Not found", "We couldn't find that page."),
    413: ("File too large", "Uploads are limited to 10 MB."),
}


def render_error(error):
    code = getattr(error, "code", 500)
    title, text = MESSAGES.get(code, ("Something went wrong", "Please try again."))
    return render_template("errors/error.html", code=code, title=title, text=text), code


@bp.app_errorhandler(400)
@bp.app_errorhandler(403)
@bp.app_errorhandler(404)
@bp.app_errorhandler(413)
def handle(error):
    return render_error(error)
