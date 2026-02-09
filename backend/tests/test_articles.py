def create_user_and_login(client):
    payload = {
        "user_email": "author@test.com",
        "user_name": "author",
        "password": "password123",
        "confirm_password": "password123",
        "birth_date": "2000-01-01",
    }

    client.post("/auth/register", json=payload)

    login = client.post(
        "/auth/login",
        json={"user_email": "author@test.com", "password": "password123"},
    )

    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_article_lifecycle(client):
    headers = create_user_and_login(client)

    article_data = {
        "title": "Test Article Title",
        "content": "This is a long article content used for testing purposes only.",
        "tag_names": ["python"],
    }

    create = client.post("/articles/", json=article_data, headers=headers)
    assert create.status_code == 201

    article_id = create.json()["article_id"]

    update = client.put(
        f"/articles/{article_id}",
        json={
            "title": "Updated Title",
            "content": "This is updated content for testing article updates.",
            "tag_names": ["backend"],
        },
        headers=headers,
    )

    assert update.status_code == 200

    delete = client.delete(f"/articles/{article_id}", headers=headers)
    assert delete.status_code == 200
