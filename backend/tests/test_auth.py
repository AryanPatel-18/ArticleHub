def valid_user_payload(email="test@example.com"):
    return {
        "user_email": email,
        "user_name": "tester",
        "password": "password123",
        "confirm_password": "password123",
        "birth_date": "2000-01-01",
    }


def test_user_registration_and_login(client):
    register = client.post("/auth/register", json=valid_user_payload())
    assert register.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "user_email": "test@example.com",
            "password": "password123",
        },
    )

    assert login.status_code == 200
    assert "access_token" in login.json()
