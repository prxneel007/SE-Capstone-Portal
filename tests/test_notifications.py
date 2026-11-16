from datetime import date

from helpers import make_team, mentor
from test_plagiarism import ORIGINAL
from test_submissions import upload

from capstone.notifications import generate_reminders, notify


def notes(query, user_id):
    return [r["message"] for r in query("SELECT message FROM notifications WHERE user_id = ? ORDER BY id",
                                        (user_id,))]


def test_reminders_due_soon_and_overdue(client, login, query, app, uid):
    team = make_team(client, login, query, members=("s2",))
    mentor(client, login, team)
    client.post(f"/teams/{team}/milestones", data={"title": "Soon", "due_date": "2026-10-22"})
    client.post(f"/teams/{team}/milestones", data={"title": "Late", "due_date": "2026-10-10"})
    client.post(f"/teams/{team}/milestones", data={"title": "Far", "due_date": "2026-12-01"})
    with app.app_context():
        created = generate_reminders(date(2026, 10, 20))
        assert created == 5  # 2 students x (soon + late) + mentor x late
        assert generate_reminders(date(2026, 10, 20)) == 0  # no duplicates
    s1 = notes(query, uid("s1"))
    assert any("Reminder" in m and "Soon" in m for m in s1)
    assert any("Overdue" in m and "Late" in m for m in s1)
    assert not any("Far" in m for m in s1)
    assert notes(query, uid("f1")) == ["Overdue: milestone 'Late' was due on 2026-10-10."]


def test_daily_run_on_first_request(client, login, query, uid):
    team = make_team(client, login, query)
    mentor(client, login, team)
    client.post(f"/teams/{team}/milestones", data={"title": "Soon", "due_date": "2026-10-21"})
    query("DELETE FROM meta")  # pretend today's run hasn't happened yet
    login("s1")
    client.get("/dashboard")
    assert any("Soon" in m for m in notes(query, uid("s1")))


def test_cli_send_reminders(app):
    result = app.test_cli_runner().invoke(args=["send-reminders"])
    assert "Created 0 reminder(s)." in result.output


def test_inbox_open_and_read_all(client, login, query, app, uid):
    with app.app_context():
        from capstone.db import get_db
        notify(uid("s1"), "Hello", "/ideas/")
        notify(uid("s1"), "Bad link", "https://evil.com")
        notify(uid("s2"), "Not yours")
        get_db().commit()
    login("s1")
    page = client.get("/notifications/").data
    assert b"Hello" in page and b"Not yours" not in page
    assert b'class="badge">2<' in client.get("/dashboard").data
    hello, bad = query("SELECT id FROM notifications WHERE user_id = ? ORDER BY id", (uid("s1"),))
    assert client.post(f"/notifications/{hello[0]}/open").headers["Location"].endswith("/ideas/")
    assert client.post(f"/notifications/{bad[0]}/open").headers["Location"].endswith("/notifications/")
    other = query("SELECT id FROM notifications WHERE user_id = ?", (uid("s2"),))[0][0]
    assert client.post(f"/notifications/{other}/open").status_code == 404
    client.post("/notifications/read-all")
    assert query("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0", (uid("s1"),))[0][0] == 0
    assert b"all caught up" not in client.get("/notifications/").data


def test_event_notifications(client, login, query, uid):
    a = make_team(client, login, query)
    mentor(client, login, a)
    login("s1")
    upload(client, a, ORIGINAL.encode())
    assert any("submitted" in m for m in notes(query, uid("f1")))
    sub = query("SELECT id FROM submissions")[0][0]
    login("f1")
    client.post(f"/submissions/{sub}/feedback", data={"comment": "Nice work"})
    assert "New faculty feedback on your report." in notes(query, uid("s1"))
    b = make_team(client, login, query, owner="s2", name="Beta")
    mentor(client, login, b, faculty="f2")
    login("s2")
    upload(client, b, ORIGINAL.encode())
    assert any("flagged" in m for m in notes(query, uid("admin")))
    assert any("flagged" in m for m in notes(query, uid("f2")))


def test_empty_inbox(client, login):
    login("s3")
    assert b"all caught up" in client.get("/notifications/").data
