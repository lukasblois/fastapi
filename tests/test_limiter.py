import pytest
from app.main import app
from app.limiter import limiter
from app.config import settings
from app.utils import get_limit_count
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import get_db, Base
from app import models
from app.oauth2 import create_access_token

SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}_test"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def rate_limit_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def rate_limit_client(rate_limit_session):
    def override_get_db():
        try:
            yield rate_limit_session
        finally:
            rate_limit_session.close()

    app.dependency_overrides[get_db] = override_get_db
    # Don't disable the limiter for rate limiting tests
    yield TestClient(app)


@pytest.fixture
def rate_limit_test_user(rate_limit_client):
    user_data = {'email': 'example@gmail.com', 'password': 'ComplexPass1492!'}
    res = rate_limit_client.post("/users", json=user_data)
    assert res.status_code == 201
    new_user = res.json()
    new_user['password'] = user_data['password']
    return new_user


@pytest.fixture
def rate_limit_token(rate_limit_test_user):
    return create_access_token({"user_id": rate_limit_test_user['id']})


@pytest.fixture
def rate_limit_authorized_client(rate_limit_client, rate_limit_token):
    rate_limit_client.headers = {
        ** rate_limit_client.headers,
        "Authorization": f"Bearer {rate_limit_token}"
    }
    return rate_limit_client


@pytest.fixture
def rate_limit_test_posts(rate_limit_test_user, rate_limit_session):
    post_data = [{
        "title": "1st title",
        "content": "1st content",
        "owner_id": rate_limit_test_user['id']
    },
        {
        "title": "2nd title",
        "content": "2nd content",
        "owner_id": rate_limit_test_user['id']
    },
        {
        "title": "3rd title",
        "content": "3rd content",
        "owner_id": rate_limit_test_user['id']
    }]

    def create_post_model(post):
        return models.Post(**post)

    post_map = map(create_post_model, post_data)
    posts = list(post_map)

    rate_limit_session.add_all(posts)
    rate_limit_session.commit()

    posts = rate_limit_session.query(models.Post).all()
    return posts


@pytest.fixture
def api_limiter():
    original_state = app.state.limiter.enabled
    # Ensure limiter is enabled for rate limiting tests
    app.state.limiter.enabled = True
    limiter.reset()
    yield
    # Restore original state
    app.state.limiter.enabled = original_state
    limiter.reset()


def test_password_reset_rate_limit(rate_limit_authorized_client, rate_limit_test_user, api_limiter):
    limit = get_limit_count(settings.limit_password_reset)
    current_pw = "ComplexPass1492!"

    for i in range(limit):
        new_pw = f"AlternativePass{i*7}!"
        payload = {
            "old_password": current_pw,
            "new_password": new_pw
        }
        res = rate_limit_authorized_client.put(
            "/users/password-reset", json=payload)
        assert res.status_code == 200
        current_pw = new_pw

    res = rate_limit_authorized_client.put("/users/password-reset", json={
        "old_password": "ComplexPass1492!", "new_password": "AlternativePass999!"})
    assert res.status_code == 429


def test_global_rate_limit(rate_limit_client, api_limiter):
    limit = get_limit_count(settings.limit_global)

    for _ in range(limit):
        assert rate_limit_client.get("/").status_code == 200

    assert rate_limit_client.get("/").status_code == 429


def test_create_user_rate_limit(rate_limit_client, api_limiter):
    limit = get_limit_count(settings.limit_users_create)

    for i in range(limit):
        user_data = {'email': f'limit{i}@gmail.com',
                     'password': 'ComplexPass1492!'}
        assert rate_limit_client.post(
            "/users", json=user_data).status_code == 201

    user_data = {'email': 'limit_fail@gmail.com',
                 'password': 'ComplexPass1492!'}
    assert rate_limit_client.post("/users", json=user_data).status_code == 429


def test_create_post_rate_limit(rate_limit_authorized_client, api_limiter):
    limit = get_limit_count(settings.limit_posts_create)

    for i in range(limit):
        res = rate_limit_authorized_client.post(
            "/posts", json={"title": f"title {i}", "content": "content"})
        assert res.status_code == 201

    res = rate_limit_authorized_client.post(
        "/posts", json={"title": "fail", "content": "fail"})
    assert res.status_code == 429


def test_delete_post_rate_limit(rate_limit_authorized_client, rate_limit_test_posts, api_limiter):
    limit = get_limit_count(settings.limit_posts_delete)
    post_id = rate_limit_test_posts[0].id

    for _ in range(limit):
        res = rate_limit_authorized_client.delete(f"/posts/{post_id}")
        assert res.status_code != 429

    res = rate_limit_authorized_client.delete(f"/posts/{post_id}")
    assert res.status_code == 429


def test_vote_rate_limit(rate_limit_authorized_client, rate_limit_test_posts, api_limiter):
    limit = get_limit_count(settings.limit_vote)
    post_id = rate_limit_test_posts[0].id

    for i in range(limit):
        direction = 1 if i % 2 == 0 else 0
        res = rate_limit_authorized_client.post(
            "/vote", json={"post_id": post_id, "dir": direction})

        assert res.status_code in [201, 204]

    res = rate_limit_authorized_client.post(
        "/vote", json={"post_id": post_id, "dir": 1})
    assert res.status_code == 429


def test_limiter_reset_manually(rate_limit_client, api_limiter):
    limit = get_limit_count(settings.limit_global)

    for _ in range(limit):
        rate_limit_client.get("/")

    assert rate_limit_client.get("/").status_code == 429

    limiter.reset()
    assert rate_limit_client.get("/").status_code == 200
