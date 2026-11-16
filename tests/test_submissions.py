import io

import pytest
from helpers import make_team, mentor

from capstone.submissions import UnreadableFile, extract_text


def upload(client, team, content=b"Our report text.", name="report.txt", **extra):
    return client.post(f"/teams/{team}/submissions",
                       data={"report": (io.BytesIO(content), name), **extra},
                       content_type="multipart/form-data")


def minimal_pdf(text):
    """A tiny valid one-page PDF containing `text`."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R"
            b" /Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offsets = b"%PDF-1.4\n", []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return out


def test_upload_versions_and_download(client, login, query):
    team = make_team(client, login, query, members=("s2",))
    r = upload(client, team)
    sub = query("SELECT * FROM submissions")[0]
    assert r.headers["Location"].endswith(f"/submissions/{sub['id']}")
    assert sub["version"] == 1 and sub["text_content"] == "Our report text."
    upload(client, team, b"Second draft")
    assert query("SELECT MAX(version) FROM submissions")[0][0] == 2
    page = client.get(f"/teams/{team}").data
    assert b"report.txt" in page and b"v2" in page
    d = client.get(f"/submissions/{sub['id']}/download")
    assert d.data == b"Our report text." and "report.txt" in d.headers["Content-Disposition"]


def test_upload_per_milestone_versioning(client, login, query):
    team = make_team(client, login, query)
    mentor(client, login, team)
    client.post(f"/teams/{team}/milestones", data={"title": "SRS", "due_date": "2026-10-25"})
    m_id = query("SELECT id FROM milestones")[0][0]
    login("s1")
    upload(client, team)
    upload(client, team, milestone_id=m_id)
    rows = query("SELECT milestone_id, version FROM submissions ORDER BY id")
    assert [tuple(r) for r in rows] == [(None, 1), (m_id, 1)]


def test_upload_validation(client, login, query):
    team = make_team(client, login, query)
    assert b"Choose a file" in client.post(f"/teams/{team}/submissions", data={},
                                           follow_redirects=True).data
    r = client.post(f"/teams/{team}/submissions", data={"report": (io.BytesIO(b"x"), "a.exe")},
                    content_type="multipart/form-data", follow_redirects=True)
    assert b"Only .txt, .md and .pdf" in r.data
    r = client.post(f"/teams/{team}/submissions", data={"report": (io.BytesIO(b""), "a.txt")},
                    content_type="multipart/form-data", follow_redirects=True)
    assert b"empty" in r.data
    r = client.post(f"/teams/{team}/submissions", data={"report": (io.BytesIO(b"%PDF-broken"), "a.pdf")},
                    content_type="multipart/form-data", follow_redirects=True)
    assert b"Could not read that PDF" in r.data
    assert upload(client, team, milestone_id=999).status_code == 400
    assert query("SELECT COUNT(*) FROM submissions")[0][0] == 0


def test_pdf_text_extracted(client, login, query):
    team = make_team(client, login, query)
    upload(client, team, minimal_pdf("Capstone PDF report"), "final.pdf")
    assert "Capstone PDF report" in query("SELECT text_content FROM submissions")[0][0]


def test_access_control(client, login, query):
    team = make_team(client, login, query)
    upload(client, team)
    sub_id = query("SELECT id FROM submissions")[0][0]
    login("s2")
    assert upload(client, team).status_code == 403
    assert client.get(f"/submissions/{sub_id}").status_code == 403
    assert client.get(f"/submissions/{sub_id}/download").status_code == 403
    login("f2")
    assert client.get(f"/submissions/{sub_id}").status_code == 200
    assert client.get("/submissions/999").status_code == 404


def test_upload_size_limit(client, login, query, app):
    app.config["MAX_CONTENT_LENGTH"] = 1024
    team = make_team(client, login, query)
    assert upload(client, team, b"x" * 5000).status_code == 413


def test_extract_text_helpers():
    assert extract_text("héllo".encode(), ".txt") == "héllo"
    assert extract_text(b"\xff\xfeok", ".md").endswith("ok")
    with pytest.raises(UnreadableFile):
        extract_text(b"not a pdf", ".pdf")
