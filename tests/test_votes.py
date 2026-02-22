def test_vote_on_post(authorized_client, test_posts):
    res = authorized_client.post(
        "/vote", json={"post_id": test_posts[2].id, "dir": 1})
    assert res.status_code == 201


def test_vote_post_twice(authorized_client, test_posts):
    post_id = test_posts[2].id
    authorized_client.post(
        "/vote", json={"post_id": post_id, "dir": 1})
    res = authorized_client.post(
        "/vote", json={"post_id": post_id, "dir": 1})
    assert res.status_code == 409


def test_delete_vote(authorized_client, test_posts):
    post_id = test_posts[2].id
    res1 = authorized_client.post(
        "/vote", json={"post_id": post_id, "dir": 1})
    res2 = authorized_client.post(
        "/vote", json={"post_id": post_id, "dir": 0})
    assert res1.status_code == 201
    assert res2.status_code == 201


def test_delete_vote_not_exist(authorized_client, test_posts):
    res = authorized_client.post(
        "/vote", json={"post_id": test_posts[2].id, "dir": 0})
    assert res.status_code == 404


def test_vote_post_not_exist(authorized_client, test_posts):
    res = authorized_client.post(
        "/vote", json={"post_id": 888888, "dir": 1})
    assert res.status_code == 404


def test_vote_unauthorized_user(client, test_posts):
    res = client.post("/vote", json={"post_id": test_posts[2].id, "dir": 1})
    assert res.status_code == 401
