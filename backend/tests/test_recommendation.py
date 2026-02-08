def test_recommendations_return_results(client):
    user = {
        "user_email": "rec@test.com",
        "user_name": "rec",
        "password": "password123",
        "confirm_password": "password123",
        "birth_date": "2000-01-01",
    }

    client.post("/auth/register", json=user)

    login = client.post(
        "/auth/login",
        json={"user_email": "rec@test.com", "password": "password123"},
    )

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    for i in range(3):
        client.post(
            "/articles/",
            json={
                "title": f"Article {i}",
                "content": "Recommendation testing article content is long enough.",
                "tag_names": ["ml"],
            },
            headers=headers,
        )

    response = client.get("/recommendations?page=1&page_size=5", headers=headers)

    assert response.status_code == 200
    assert "articles" in response.json()
