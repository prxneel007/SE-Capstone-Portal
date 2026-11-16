from helpers import make_idea, make_team, mentor


def team_row(query, team_id):
    return query("SELECT * FROM teams WHERE id = ?", (team_id,))[0]


def test_claim_and_release_idea(client, login, query):
    idea = make_idea(client, login, query)
    team = make_team(client, login, query)
    assert b"Claim for my team" in client.get(f"/ideas/{idea}").data
    r = client.post(f"/ideas/{idea}/claim")
    assert r.headers["Location"].endswith(f"/teams/{team}")
    assert team_row(query, team)["idea_id"] == idea
    assert b"Claimed by Alpha" in client.get("/ideas/").data
    client.post(f"/teams/{team}/release")
    assert team_row(query, team)["idea_id"] is None


def test_claim_rules(client, login, query):
    idea = make_idea(client, login, query)
    other = make_idea(client, login, query, title="Other idea")
    login("s5")
    assert b"Join or create a team" in client.post(f"/ideas/{idea}/claim", follow_redirects=True).data
    make_team(client, login, query)
    client.post(f"/ideas/{idea}/claim")
    assert b"already claimed an idea" in client.post(f"/ideas/{other}/claim", follow_redirects=True).data
    make_team(client, login, query, owner="s2", name="Beta")
    assert b"Another team has already claimed" in client.post(f"/ideas/{idea}/claim",
                                                              follow_redirects=True).data
    assert client.post("/ideas/999/claim").status_code == 404
    login("f1")
    assert client.post(f"/ideas/{idea}/claim").status_code == 403


def test_claimed_idea_cannot_be_deleted(client, login, query):
    idea = make_idea(client, login, query)
    make_team(client, login, query)
    client.post(f"/ideas/{idea}/claim")
    login("f1")
    assert b"cannot be deleted" in client.post(f"/ideas/{idea}/delete", follow_redirects=True).data


def test_faculty_mentor_flow(client, login, query):
    team = make_team(client, login, query)
    mentor(client, login, team)
    assert team_row(query, team)["mentor_id"] is not None
    assert b"Alpha" in client.get("/dashboard").data  # "Teams I mentor" widget
    login("f2")
    assert b"already has a mentor" in client.post(f"/teams/{team}/mentor", follow_redirects=True).data
    assert client.post(f"/teams/{team}/unmentor").status_code == 403
    login("f1")
    client.post(f"/teams/{team}/unmentor")
    assert team_row(query, team)["mentor_id"] is None
    login("s1")
    assert client.post(f"/teams/{team}/mentor").status_code == 403


def test_admin_assigns_mentor(client, login, query, uid):
    team = make_team(client, login, query)
    login("admin")
    assert b"Assign faculty" in client.get(f"/teams/{team}").data
    client.post(f"/teams/{team}/mentor", data={"faculty_id": uid("f2")})
    assert team_row(query, team)["mentor_id"] == uid("f2")
    assert b"Choose a faculty member" in client.post(f"/teams/{team}/mentor", data={"faculty_id": uid("s1")},
                                                     follow_redirects=True).data


def test_release_permissions(client, login, query):
    idea = make_idea(client, login, query)
    team = make_team(client, login, query)
    client.post(f"/ideas/{idea}/claim")
    login("s2")
    assert client.post(f"/teams/{team}/release").status_code == 403
    login("f2")
    assert client.post(f"/teams/{team}/release").status_code == 403
