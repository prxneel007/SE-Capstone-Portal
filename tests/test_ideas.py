from capstone.ideas import clean_tags

IDEA = {"title": "Smart parking", "description": "Find free parking slots on campus in real time.",
        "domain": "IoT", "tags": "IoT, Sensors, iot"}


def new_idea(client, **overrides):
    return client.post("/ideas/new", data={**IDEA, **overrides})


def test_ideas_require_login(client):
    assert client.get("/ideas/").status_code == 302


def test_create_and_view_idea(client, login, query):
    login("s1")
    r = new_idea(client)
    assert r.status_code == 302
    idea = query("SELECT * FROM ideas")[0]
    assert idea["tags"] == "iot, sensors"
    page = client.get(f"/ideas/{idea['id']}")
    assert b"Smart parking" in page.data


def test_create_idea_validation(client, login, query):
    login("s1")
    r = new_idea(client, title="abc", description="short", domain="Nope")
    assert b"Title must be 5-120 characters." in r.data
    assert b"Description must be at least 20 characters." in r.data
    assert b"Choose a domain." in r.data
    assert query("SELECT COUNT(*) FROM ideas")[0][0] == 0


def test_search_filter_and_sort(client, login):
    login("s1")
    new_idea(client, title="Parking finder app")
    new_idea(client, title="Resume ranking with NLP", domain="AI/ML", tags="nlp")
    assert b"Resume ranking" in client.get("/ideas/?q=nlp").data
    assert b"Parking finder" not in client.get("/ideas/?q=nlp").data
    assert b"Parking finder" not in client.get("/ideas/?domain=AI/ML").data
    assert client.get("/ideas/?sort=votes").status_code == 200


def test_edit_and_delete_by_author_only(client, login, query):
    login("s1")
    new_idea(client)
    idea_id = query("SELECT id FROM ideas")[0][0]
    login("s2")
    assert client.get(f"/ideas/{idea_id}/edit").status_code == 403
    assert client.post(f"/ideas/{idea_id}/delete").status_code == 403
    login("s1")
    client.post(f"/ideas/{idea_id}/edit", data={**IDEA, "title": "Smarter parking"})
    assert query("SELECT title FROM ideas")[0][0] == "Smarter parking"
    r = client.post(f"/ideas/{idea_id}/edit", data={**IDEA, "title": "x"})
    assert b"Title must be" in r.data
    client.post(f"/ideas/{idea_id}/delete")
    assert query("SELECT COUNT(*) FROM ideas")[0][0] == 0


def test_admin_can_edit_any_idea(client, login, query):
    login("s1")
    new_idea(client)
    idea_id = query("SELECT id FROM ideas")[0][0]
    login("admin")
    assert client.get(f"/ideas/{idea_id}/edit").status_code == 200


def test_missing_idea_404(client, login):
    login("s1")
    assert client.get("/ideas/999").status_code == 404


def test_clean_tags():
    assert clean_tags(" A, b ,, a ") == "a, b"
