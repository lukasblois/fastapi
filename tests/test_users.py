import pytest
from jose import jwt
from app import schemas
from app.config import settings


def test_create_user(client):
    res = client.post(
        "/users", json={'email': 'example@gmail.com', 'password': 'ComplexPass1492'})
    new_user = schemas.UserOut(**res.json())
    assert new_user.email == 'example@gmail.com'
    assert res.status_code == 201


def test_login_user(client, test_user):
    res = client.post(
        "/login", data={'username': test_user['email'], 'password': test_user['password']})
    login_res = schemas.Token(**res.json())
    payload = jwt.decode(login_res.access_token,
                         settings.secret_key, algorithms=[settings.algorithm])
    id = payload.get("user_id")
    assert id == test_user['id']
    assert login_res.token_type == 'bearer'
    assert res.status_code == 200


def test_create_user_with_email_spaces(client):
    res = client.post(
        "/users", json={'email': '  spaces@gmail.com  ', 'password': 'ComplexPass1492!'})
    new_user = schemas.UserOut(**res.json())
    assert new_user.email == 'spaces@gmail.com'
    assert res.status_code == 201


def test_create_user_with_password_spaces(client):
    res = client.post(
        "/users", json={'email': 'passspaces@gmail.com', 'password': '  ComplexPass1492!  '})
    assert res.status_code == 201

    login_res = client.post(
        "/login", data={'username': 'passspaces@gmail.com', 'password': 'ComplexPass1492!'})
    assert login_res.status_code == 200


def test_login_with_email_spaces(client, test_user):
    res = client.post(
        "/login", data={'username': f'  {test_user["email"]}  ', 'password': test_user['password']})
    assert res.status_code == 200


def test_login_with_password_spaces(client, test_user):
    res = client.post(
        "/login", data={'username': test_user['email'], 'password': f'  {test_user["password"]}  '})
    assert res.status_code == 200


def test_create_user_weak_password(client):
    res = client.post(
        "/users", json={'email': 'weakpass@gmail.com', 'password': 'password123'})
    assert res.status_code == 422
    assert 'Password is too weak' in res.json()['detail'][0]['msg']


def test_create_user_very_weak_password(client):
    res = client.post(
        "/users", json={'email': 'veryweak@gmail.com', 'password': '12345678'})
    assert res.status_code == 422
    assert 'Password is too weak' in res.json()['detail'][0]['msg']


@pytest.mark.parametrize("email, password, status_code", [
    ('wrongemail@gmail.com', 'ComplexPass1492!', 404),
    ('example@gmail.com', 'wrongpasswordComplex1492!', 401),
    ('wrongemail@gmail.com', 'wrongpasswordComplex1492', 404),
    (None, 'ComplexPass1492!', 422),
    ('example@gmail.com', None, 422),
    (None, None, 422)
])
def test_incorrect_login(test_user, client, email, password, status_code):
    res = client.post(
        "/login", data={'username': email, 'password': password})
    assert res.status_code == status_code
