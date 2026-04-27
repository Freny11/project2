from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_gists_success():
    response = client.get("/octocat")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["gists"], list)
    if body["gists"]:
        gist = body["gists"][0]
        assert "id" in gist
        assert "url" in gist
        assert "description" in gist


def test_user_not_found():
    response = client.get("/invaliduser123456789xyz")
    assert response.status_code == 404