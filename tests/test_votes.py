def make_idea(client, login, query):
    login("s1")
    client.post("/ideas/new", data={"title": "Vote target", "domain": "Web",
                                    "description": "An idea that people will vote for."})
    return query("SELECT id FROM ideas")[0][0]


def votes(query):
    return query("SELECT COUNT(*) FROM votes")[0][0]


def test_vote_toggle(client, login, query):
    idea_id = make_idea(client, login, query)
    login("s2")
    client.post(f"/ideas/{idea_id}/vote")
    assert votes(query) == 1
    client.post(f"/ideas/{idea_id}/vote")
    assert votes(query) == 0


def test_one_vote_per_user_and_sorting(client, login, query):
    first = make_idea(client, login, query)
    client.post("/ideas/new", data={"title": "Second idea", "domain": "Web",
                                    "description": "Another idea that should win the vote."})
    second = query("SELECT MAX(id) FROM ideas")[0][0]
    for user in ("s2", "s3"):
        login(user)
        client.post(f"/ideas/{second}/vote")
    login("s4")
    client.post(f"/ideas/{first}/vote")
    page = client.get("/ideas/?sort=votes").data.decode()
    assert page.index("Second idea") < page.index("Vote target")


def test_cannot_vote_own_idea(client, login, query):
    idea_id = make_idea(client, login, query)
    r = client.post(f"/ideas/{idea_id}/vote", follow_redirects=True)
    assert b"can&#39;t vote for your own idea" in r.data
    assert votes(query) == 0


def test_vote_missing_idea(client, login):
    login("s1")
    assert client.post("/ideas/42/vote").status_code == 404


def test_vote_redirect_is_safe(client, login, query):
    idea_id = make_idea(client, login, query)
    login("s2")
    r = client.post(f"/ideas/{idea_id}/vote", data={"next": "https://evil.com"})
    assert r.headers["Location"].endswith(f"/ideas/{idea_id}")
