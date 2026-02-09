def test_like_interaction(client):
    user = {
        "user_email": "user@test.com",
        "user_name": "user",
        "password": "password123",
        "confirm_password": "password123",
        "birth_date": "2000-01-01",
    }

    client.post("/auth/register", json=user)

    login = client.post(
        "/auth/login",
        json={"user_email": "user@test.com", "password": "password123"},
    )

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    article = client.post(
        "/articles/",
        json={
            "title": "Interaction Article",
            "content": "This article exists only for interaction testing purposes.",
            "tag_names": ["ai"],
        },
        headers=headers,
    )

    article_id = article.json()["article_id"]

    interaction = client.post(
        "/interactions/toggle",
        json={
            "article_id": article_id,
            "interaction_type": "like",
        },
        headers=headers,
    )

    assert interaction.status_code == 200
