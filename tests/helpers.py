"""Shared setup steps for feature tests."""


def make_team(client, login, query, owner="s1", name="Alpha", members=()):
    login(owner)
    client.post("/teams/create", data={"name": name})
    team = query("SELECT * FROM teams WHERE name = ?", (name,))[0]
    for m in members:
        login(m)
        client.post("/teams/join", data={"code": team["invite_code"]})
    return team["id"]


def make_idea(client, login, query, author="f1", title="Shared idea"):
    login(author)
    client.post("/ideas/new", data={"title": title, "domain": "Web",
                                    "description": "A capstone idea description that is long enough."})
    return query("SELECT id FROM ideas WHERE title = ?", (title,))[0][0]


def mentor(client, login, team_id, faculty="f1"):
    login(faculty)
    client.post(f"/teams/{team_id}/mentor")
