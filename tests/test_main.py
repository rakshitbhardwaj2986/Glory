"""
Glory - API Tests
Tests cover: user registration, authentication, protected routes,
             job CRUD, and ML match endpoint.
"""

# ─────────────────────────────────────────
# TEST 1: USER REGISTRATION
# ─────────────────────────────────────────

def test_register_user_success(client):
    """Registering a new user should return 200 with correct fields."""
    response = client.post("/users", json={
        "full_name": "Rakshit Sharma",
        "email": "rakshit@glory.com",
        "password": "securepass123",
        "role": "jobseeker"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "rakshit@glory.com"
    assert data["full_name"] == "Rakshit Sharma"
    assert data["role"] == "jobseeker"
    assert "id" in data
    # Password should never be returned
    assert "password" not in data
    assert "hashed_password" not in data

# ─────────────────────────────────────────
# TEST 2: USER REGISTRATION DUPLICATE CHECK
# ─────────────────────────────────────────
def test_register_duplicate_email(client):
    """Registering the same email twice should return 400."""
    payload = {
        "full_name": "Duplicate User",
        "email": "duplicate@glory.com",
        "password": "pass123",
        "role": "jobseeker"
    }
    client.post("/users", json=payload)  # first registration
    response = client.post("/users", json=payload)  # duplicate
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()

# ─────────────────────────────────────────
# TEST 3: USER EMPTY LOGIN FLAG
# ─────────────────────────────────────────
def test_empty_login(client):
    login_cred= {
        "username":"",
        "password":""
    }
    response= client.post("/login", json= login_cred)
    data= response.json()
    assert response.status_code in [400,422]
    # Check that there's an error in the response (either 'detail' or 'error')
    assert "detail" in data or "error" in data

# ─────────────────────────────────────────
# TEST 4: USER WRONG LOGIN CREDENTIALS FLAG
# ─────────────────────────────────────────
def test_wrong_credentials(client):
    login_cred= {
        "username":"wrong_username",
        "password":"wrong_password"
    }
    response= client.post("/login", json= login_cred)
    data= response.json()
    assert response.status_code in [400,422]
    # Check that there's an error response
    assert "detail" in data or "error" in data

# ─────────────────────────────────────────
# TEST 5: USER REGISTRATION
# ─────────────────────────────────────────
def test_protected_route_requires_valid_token(client):
    response = client.get("/users")

    assert response.status_code == 401
    assert response.json()["detail"] in ["Not authenticated", "Could not validate credentials"]