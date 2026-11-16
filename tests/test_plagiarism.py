from helpers import make_team
from test_submissions import upload

from capstone.plagiarism import best_match, shingles, similarity

ORIGINAL = ("Our capstone builds a smart parking system using ultrasonic sensors on each slot and a mobile "
            "application that shows free slots in real time to students and staff across the whole campus.")


def test_shingles_and_similarity():
    assert shingles("") == set()
    assert shingles("Two words") == {"two words"}
    assert len(shingles("a b c d e f")) == 2
    assert similarity(ORIGINAL, ORIGINAL) == 1.0
    assert similarity(ORIGINAL, "Completely different text about canteen demand forecasting models.") == 0.0
    assert similarity("", ORIGINAL) == 0.0
    assert 0 < similarity(ORIGINAL, ORIGINAL + " We also add payments and analytics.") < 1


def test_best_match():
    assert best_match("", [(1, ORIGINAL)]) == (0.0, None)
    score, match = best_match(ORIGINAL, [(1, "unrelated words here entirely"), (2, ORIGINAL), (3, "")])
    assert (score, match) == (1.0, 2)


def test_copied_report_is_flagged(client, login, query):
    a = make_team(client, login, query)
    upload(client, a, ORIGINAL.encode())
    b = make_team(client, login, query, owner="s2", name="Beta")
    upload(client, b, (ORIGINAL + " Small change at the end.").encode())
    first, second = query("SELECT * FROM submissions ORDER BY id")
    assert first["similarity"] == 0  # nothing to compare against yet
    assert second["similarity"] >= 0.4 and second["similar_to"] == first["id"]
    login("f1")
    page = client.get("/plagiarism/").data
    assert b"Beta" in page
    detail = client.get(f"/submissions/{second['id']}").data
    assert b"Flagged for review" in detail and b"closest match" in detail


def test_same_team_versions_not_compared(client, login, query):
    a = make_team(client, login, query)
    upload(client, a, ORIGINAL.encode())
    upload(client, a, ORIGINAL.encode())
    assert query("SELECT MAX(similarity) FROM submissions")[0][0] == 0


def test_plagiarism_page_staff_only(client, login):
    login("s1")
    assert client.get("/plagiarism/").status_code == 403
    login("admin")
    assert b"Nothing flagged" in client.get("/plagiarism/").data
