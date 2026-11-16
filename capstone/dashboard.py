from flask import Blueprint, current_app, g, render_template

from .security import login_required

bp = Blueprint("dashboard", __name__)
NAV = [("Dashboard", "dashboard.index", None)]


@bp.route("/dashboard")
@login_required
def index():
    # Each feature module may contribute a widget: a dict with a "template" key.
    widgets = [widget(g.user) for widget in current_app.extensions["dashboard_widgets"]]
    return render_template("dashboard.html", widgets=[w for w in widgets if w])
