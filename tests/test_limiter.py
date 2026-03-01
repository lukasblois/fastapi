import pytest
from app.main import app
from app.limiter import limiter
from app.config import settings
from app.utils import get_limit_count


@pytest.fixture
def api_limiter():
    original_state = app.state.limiter.enabled
    app.state.limiter.enabled = True
    limiter.reset()
    yield
    app.state.limiter.enabled = original_state
    limiter.reset()


def test_password_reset_rate_limit(authorized_client, test_user, api_limiter):
    limit = get_limit_count(settings.limit_password_reset)
    current_pw = "ComplexPass1492!"

    for i in range(limit):
        new_pw = f"AlternativePass{i*7}!"
        payload = {
            "old_password": current_pw,
            "new_password": new_pw
        }
        res = authorized_client.put("/users/password-reset", json=payload)
        assert res.status_code == 200
        current_pw = new_pw

    res = authorized_client.put("/users/password-reset", json={
                                "old_password": "ComplexPass1492!", "new_password": "AlternativePass999!"})
    assert res.status_code == 429


def test_global_rate_limit(client, api_limiter):
    limit = get_limit_count(settings.limit_global)

    for _ in range(limit):
        assert client.get("/").status_code == 200

    assert client.get("/").status_code == 429


def test_create_user_rate_limit(client, api_limiter):
    limit = get_limit_count(settings.limit_users_create)

    for i in range(limit):
        user_data = {'email': f'limit{i}@gmail.com',
                     'password': 'ComplexPass1492!'}
        assert client.post("/users", json=user_data).status_code == 201

    user_data = {'email': 'limit_fail@gmail.com',
                 'password': 'ComplexPass1492!'}
    assert client.post("/users", json=user_data).status_code == 429


def test_create_post_rate_limit(authorized_client, api_limiter):
    limit = get_limit_count(settings.limit_posts_create)

    for i in range(limit):
        res = authorized_client.post(
            "/posts", json={"title": f"title {i}", "content": "content"})
        assert res.status_code == 201

    res = authorized_client.post(
        "/posts", json={"title": "fail", "content": "fail"})
    assert res.status_code == 429


def test_delete_post_rate_limit(authorized_client, test_posts, api_limiter):
    limit = get_limit_count(settings.limit_posts_delete)
    post_id = test_posts[0].id

    for _ in range(limit):
        res = authorized_client.delete(f"/posts/{post_id}")
        assert res.status_code != 429

    res = authorized_client.delete(f"/posts/{post_id}")
    assert res.status_code == 429


def test_vote_rate_limit(authorized_client, test_posts, api_limiter):
    limit = get_limit_count(settings.limit_vote)
    post_id = test_posts[0].id

    for i in range(limit):
        direction = 1 if i % 2 == 0 else 0
        res = authorized_client.post(
            "/vote", json={"post_id": post_id, "dir": direction})

        assert res.status_code in [201, 204]

    res = authorized_client.post("/vote", json={"post_id": post_id, "dir": 1})
    assert res.status_code == 429


def test_limiter_reset_manually(client, api_limiter):
    limit = get_limit_count(settings.limit_global)

    for _ in range(limit):
        client.get("/")

    assert client.get("/").status_code == 429

    limiter.reset()
    assert client.get("/").status_code == 200
