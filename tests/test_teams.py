def team(query):
    return query("SELECT * FROM teams")[0]


def size(query):
    return query("SELECT COUNT(*) FROM team_members")[0][0]


def test_create_team_and_join(client, login, query):
    login("s1")
    r = client.post("/teams/create", data={"name": "Alpha"})
    t = team(query)
    assert r.headers["Location"].endswith(f"/teams/{t['id']}")
    assert len(t["invite_code"]) == 8
    login("s2")
    client.post("/teams/join", data={"code": t["invite_code"].lower()})
    assert size(query) == 2
    assert client.get("/teams/").headers["Location"].endswith(f"/teams/{t['id']}")


def test_team_rules(client, login, query):
    login("s1")
    assert b"3-50 characters" in client.post("/teams/create", data={"name": "ab"}, follow_redirects=True).data
    client.post("/teams/create", data={"name": "Alpha"})
    r = client.post("/teams/create", data={"name": "Beta"}, follow_redirects=True)
    assert b"already in a team" in r.data
    login("s2")
    r = client.post("/teams/create", data={"name": "Alpha"}, follow_redirects=True)
    assert b"name is taken" in r.data
    r = client.post("/teams/join", data={"code": "ZZZ"}, follow_redirects=True)
    assert b"No team has that invite code" in r.data


def test_team_is_full_at_four(client, login, query):
    login("s1")
    client.post("/teams/create", data={"name": "Alpha"})
    code = team(query)["invite_code"]
    for s in ("s2", "s3", "s4"):
        login(s)
        client.post("/teams/join", data={"code": code})
    login("s5")
    r = client.post("/teams/join", data={"code": code}, follow_redirects=True)
    assert b"team is full" in r.data
    assert size(query) == 4
    login("s1")
    r = client.post("/teams/join", data={"code": code}, follow_redirects=True)
    assert b"already in a team" in r.data


def test_team_page_access(client, login, query):
    login("s1")
    client.post("/teams/create", data={"name": "Alpha"})
    t = team(query)
    assert t["invite_code"].encode() in client.get(f"/teams/{t['id']}").data
    login("s2")
    assert client.get(f"/teams/{t['id']}").status_code == 403
    assert client.get("/teams/").status_code == 200  # join/create page
    login("f1")
    page = client.get(f"/teams/{t['id']}")
    assert page.status_code == 200 and t["invite_code"].encode() not in page.data
    assert b"Alpha" in client.get("/teams/").data
    assert client.get("/teams/999").status_code == 404


def test_faculty_cannot_create_team(client, login):
    login("f1")
    assert client.post("/teams/create", data={"name": "Profs"}).status_code == 403


def test_leave_team(client, login, query):
    login("s1")
    client.post("/teams/create", data={"name": "Alpha"})
    t = team(query)
    login("s2")
    client.post("/teams/join", data={"code": t["invite_code"]})
    client.post(f"/teams/{t['id']}/leave")
    assert size(query) == 1
    assert client.post(f"/teams/{t['id']}/leave").status_code == 403
    login("s1")
    client.post(f"/teams/{t['id']}/leave")
    assert query("SELECT COUNT(*) FROM teams")[0][0] == 0


def test_last_member_cannot_leave_with_submissions(client, login, query, app):
    login("s1")
    client.post("/teams/create", data={"name": "Alpha"})
    t = team(query)
    with app.app_context():
        from capstone.db import get_db
        db = get_db()
        db.execute("INSERT INTO submissions (team_id, filename, stored_name, version, submitted_by)"
                   " VALUES (?, 'r.txt', 'x.txt', 1, (SELECT id FROM users WHERE email = 's1@test.edu'))",
                   (t["id"],))
        db.commit()
    r = client.post(f"/teams/{t['id']}/leave", follow_redirects=True)
    assert b"can&#39;t leave" in r.data
    assert size(query) == 1


def test_dashboard_team_widget(client, login):
    login("s1")
    assert b"not in a team yet" in client.get("/dashboard").data
    client.post("/teams/create", data={"name": "Alpha"})
    assert b"Alpha" in client.get("/dashboard").data
