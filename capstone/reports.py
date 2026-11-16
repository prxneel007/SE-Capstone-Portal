"""FR-14: progress report across teams for faculty/admin, with CSV export."""
import csv
import io

from flask import Blueprint, Response, g, render_template, request

from .db import get_db, today
from .security import role_required

bp = Blueprint("reports", __name__, url_prefix="/reports")
NAV = [("Reports", "reports.index", ("faculty", "admin"))]

COLUMNS = ["Team", "Members", "Idea", "Mentor", "Milestones done", "Milestones total",
           "Progress %", "Overdue", "Reports", "Max similarity %", "Last submission"]


def team_rows(mentor_id=None):
    sql = (
        "SELECT t.id, t.name, i.title AS idea, m.name AS mentor,"
        " (SELECT COUNT(*) FROM team_members tm WHERE tm.team_id = t.id) AS members,"
        " (SELECT COUNT(*) FROM milestones ms WHERE ms.team_id = t.id) AS total,"
        " (SELECT COUNT(*) FROM milestones ms WHERE ms.team_id = t.id AND ms.status = 'done') AS done,"
        " (SELECT COUNT(*) FROM milestones ms WHERE ms.team_id = t.id AND ms.status != 'done'"
        "   AND ms.due_date < ?) AS overdue,"
        " (SELECT COUNT(*) FROM submissions s WHERE s.team_id = t.id) AS reports,"
        " (SELECT MAX(similarity) FROM submissions s WHERE s.team_id = t.id) AS max_sim,"
        " (SELECT MAX(created_at) FROM submissions s WHERE s.team_id = t.id) AS last_sub"
        " FROM teams t LEFT JOIN ideas i ON i.id = t.idea_id LEFT JOIN users m ON m.id = t.mentor_id"
    )
    params = [today().isoformat()]
    if mentor_id:
        sql += " WHERE t.mentor_id = ?"
        params.append(mentor_id)
    rows = []
    for r in get_db().execute(sql + " ORDER BY t.name", params):
        rows.append({
            "id": r["id"], "name": r["name"], "members": r["members"], "idea": r["idea"] or "",
            "mentor": r["mentor"] or "", "done": r["done"], "total": r["total"],
            "percent": round(100 * r["done"] / r["total"]) if r["total"] else 0,
            "overdue": r["overdue"], "reports": r["reports"],
            "max_sim": round(100 * (r["max_sim"] or 0)), "last_sub": (r["last_sub"] or "")[:16],
        })
    return rows


def _mentor_filter():
    return g.user["id"] if g.user["role"] == "faculty" and request.args.get("mine") == "1" else None


@bp.route("/")
@role_required("faculty", "admin")
def index():
    return render_template("reports/index.html", rows=team_rows(_mentor_filter()),
                           mine=request.args.get("mine") == "1")


@bp.route("/export.csv")
@role_required("faculty", "admin")
def export_csv():
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(COLUMNS)
    for r in team_rows(_mentor_filter()):
        writer.writerow([r["name"], r["members"], r["idea"], r["mentor"], r["done"], r["total"],
                         r["percent"], r["overdue"], r["reports"], r["max_sim"], r["last_sub"]])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=capstone_progress_report.csv"})
