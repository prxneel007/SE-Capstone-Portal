from helpers import make_team
from test_submissions import upload


def setup_submission(client, login, query):
    team = make_team(client, login, query)
    upload(client, team)
    return query("SELECT id FROM submissions")[0][0]


def test_faculty_feedback_visible_to_team(client, login, query):
    sub = setup_submission(client, login, query)
    login("f1")
    r = client.post(f"/submissions/{sub}/feedback", data={"comment": "Good structure, add test results.",
                                                          "grade": "B"})
    assert r.headers["Location"].endswith(f"/submissions/{sub}")
    login("s1")
    page = client.get(f"/submissions/{sub}").data
    assert b"Good structure" in page and b"Grade B" in page
    assert b"Good structure" in client.get("/dashboard").data


def test_feedback_validation_and_permissions(client, login, query):
    sub = setup_submission(client, login, query)
    assert client.post(f"/submissions/{sub}/feedback", data={"comment": "hi"}).status_code == 403
    login("f1")
    r = client.post(f"/submissions/{sub}/feedback", data={"comment": "  "}, follow_redirects=True)
    assert b"1-2000 characters" in r.data
    r = client.post(f"/submissions/{sub}/feedback", data={"comment": "ok", "grade": "Z"}, follow_redirects=True)
    assert b"valid grade" in r.data
    assert client.post("/submissions/999/feedback", data={"comment": "x"}).status_code == 404
    assert query("SELECT COUNT(*) FROM feedback")[0][0] == 0


def test_dashboard_without_feedback(client, login, query):
    setup_submission(client, login, query)
    assert b"No feedback on your reports yet" in client.get("/dashboard").data
