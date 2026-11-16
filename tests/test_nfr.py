"""Non-functional checks: error pages, demo seed, performance, responsive layout."""
import time

from capstone.db import get_db


def test_error_pages(client, login):
    login("s1")
    r = client.get("/no-such-page")
    assert r.status_code == 404 and b"Not found" in r.data
    assert b"Not allowed" in client.get("/reports/").data


def test_csrf_error_page(app):
    app.config["CSRF_DISABLED"] = False
    r = app.test_client().post("/auth/login", data={})
    assert r.status_code == 400 and b"Bad request" in r.data


def test_seed_demo(app, query):
    result = app.test_cli_runner().invoke(args=["seed-demo"])
    assert "Demo data loaded" in result.output
    assert query("SELECT COUNT(*) FROM users")[0][0] == 8
    assert query("SELECT COUNT(*) FROM team_members")[0][0] == 4
    assert query("SELECT COUNT(*) FROM milestones")[0][0] == 4


def test_idea_list_fast_with_500_ideas(app, client, login):
    """NFR-02: the idea bank lists 500 ideas with votes in under a second."""
    with app.app_context():
        db = get_db()
        db.executemany("INSERT INTO ideas (title, description, domain, author_id) VALUES (?, ?, 'Web', 1)",
                       [(f"Idea {i}", "x" * 50) for i in range(500)])
        db.executemany("INSERT INTO votes (user_id, idea_id) VALUES (?, ?)",
                       [(u, i) for u in range(1, 6) for i in range(1, 501, 3)])
        db.commit()
    login("s1")
    start = time.perf_counter()
    r = client.get("/ideas/?sort=votes")
    assert r.status_code == 200
    assert time.perf_counter() - start < 1.0
    assert r.data.count(b'class="vote"') == 500


def test_viewport_meta_present(client):
    """NFR-03: pages declare a mobile viewport so the responsive CSS applies."""
    assert b'name="viewport"' in client.get("/").data
