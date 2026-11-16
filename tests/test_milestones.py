from helpers import make_team, mentor

from capstone.milestones import parse_due, progress


def add(client, team, title="Proposal", due="2026-10-25"):
    return client.post(f"/teams/{team}/milestones", data={"title": title, "due_date": due})


def test_mentor_adds_and_team_updates(client, login, query, app):
    team = make_team(client, login, query)
    mentor(client, login, team)
    add(client, team)
    add(client, team, "Old one", "2026-10-01")
    ms = query("SELECT * FROM milestones ORDER BY id")
    assert len(ms) == 2
    login("s1")
    page = client.get(f"/teams/{team}").data
    assert b"Proposal" in page and b"overdue" in page
    client.post(f"/milestones/{ms[1]['id']}/status", data={"status": "done"})
    with app.app_context():
        assert progress(team) == {"total": 2, "done": 1, "percent": 50, "overdue": 0}
    assert b"50%" in client.get("/dashboard").data


def test_milestone_validation_and_permissions(client, login, query):
    team = make_team(client, login, query)
    login("s1")
    assert add(client, team).status_code == 403  # students can't create
    mentor(client, login, team)
    r = client.post(f"/teams/{team}/milestones", data={"title": "", "due_date": "2026-10-25"},
                    follow_redirects=True)
    assert b"title is required" in r.data
    r = client.post(f"/teams/{team}/milestones", data={"title": "X", "due_date": "not-a-date"},
                    follow_redirects=True)
    assert b"valid due date" in r.data
    add(client, team)
    m_id = query("SELECT id FROM milestones")[0][0]
    assert client.post(f"/milestones/{m_id}/status", data={"status": "bogus"}).status_code == 400
    login("s2")  # not a member
    assert client.post(f"/milestones/{m_id}/status", data={"status": "done"}).status_code == 403
    assert client.post(f"/milestones/{m_id}/delete").status_code == 403
    assert client.post("/milestones/999/delete").status_code == 404


def test_mentor_deletes_milestone(client, login, query):
    team = make_team(client, login, query)
    mentor(client, login, team)
    add(client, team)
    client.post(f"/milestones/{query('SELECT id FROM milestones')[0][0]}/delete")
    assert query("SELECT COUNT(*) FROM milestones")[0][0] == 0


def test_progress_empty(app):
    with app.app_context():
        assert progress(123)["percent"] == 0


def test_parse_due():
    assert parse_due("2026-10-25") == "2026-10-25"
    assert parse_due("25/10/2026") is None
    assert parse_due(None) is None
