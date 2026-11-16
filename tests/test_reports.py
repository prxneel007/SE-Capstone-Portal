import csv
import io

from helpers import make_team, mentor
from test_submissions import upload


def test_report_and_csv(client, login, query):
    a = make_team(client, login, query, members=("s2",))
    mentor(client, login, a)
    client.post(f"/teams/{a}/milestones", data={"title": "Done one", "due_date": "2026-10-01"})
    client.post(f"/teams/{a}/milestones", data={"title": "Late one", "due_date": "2026-10-02"})
    m_id = query("SELECT id FROM milestones WHERE title = 'Done one'")[0][0]
    client.post(f"/milestones/{m_id}/status", data={"status": "done"})
    login("s1")
    upload(client, a)
    make_team(client, login, query, owner="s3", name="Beta")
    login("f1")
    page = client.get("/reports/").data
    assert b"Alpha" in page and b"Beta" in page and b"50%" in page
    assert b"Beta" not in client.get("/reports/?mine=1").data
    r = client.get("/reports/export.csv")
    assert r.mimetype == "text/csv"
    rows = list(csv.DictReader(io.StringIO(r.data.decode())))
    alpha = next(row for row in rows if row["Team"] == "Alpha")
    assert alpha["Members"] == "2" and alpha["Progress %"] == "50" and alpha["Overdue"] == "1"
    assert alpha["Reports"] == "1" and alpha["Mentor"] == "Faculty One"


def test_reports_staff_only(client, login):
    login("s1")
    assert client.get("/reports/").status_code == 403
    assert client.get("/reports/export.csv").status_code == 403
    login("admin")
    assert b"No teams yet" in client.get("/reports/").data
