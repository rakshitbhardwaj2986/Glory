import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest  # type: ignore[import]

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Mock ALL unavailable packages BEFORE any imports ──
sys.modules["psycopg2"] = MagicMock()
sys.modules["psycopg2.extras"] = MagicMock()
sys.modules["psycopg2.extensions"] = MagicMock()

mock_st = MagicMock()
mock_model = MagicMock()
mock_model.encode.return_value = MagicMock()
mock_st.SentenceTransformer.return_value = mock_model
mock_st.util.cos_sim.return_value = [[0.75]]
sys.modules["sentence_transformers"] = mock_st

# ── Now set up SQLite test engine ──
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite:///./test_glory.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# ── Patch Database module to use SQLite ──
import app.Database as db_module
db_module.engine = test_engine
db_module.SessionLocal = TestingSessionLocal

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

db_module.get_db = override_get_db

# ── Now safely import app ──
from fastapi.testclient import TestClient
from app.models import Base
from app.main import app
from app.Database import get_db

app.dependency_overrides[get_db] = override_get_db

# Create all tables in SQLite test DB
Base.metadata.create_all(bind=test_engine)

# ── Fixtures ──
@pytest.fixture(scope="function")
def client():
    # Clean tables between tests so each test starts fresh
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    return TestClient(app)

@pytest.fixture(scope="function")
def registered_jobseeker(client):
    payload = {
        "full_name": "Test Jobseeker",
        "email": "jobseeker@glory.com",
        "password": "testpass123",
        "role": "jobseeker"
    }
    client.post("/users", json=payload)
    return payload

@pytest.fixture(scope="function")
def jobseeker_headers(client, registered_jobseeker):
    res = client.post("/login", data={
        "username": registered_jobseeker["email"],
        "password": registered_jobseeker["password"]
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def employer_headers(client):
    payload = {
        "full_name": "Test Employer",
        "email": "employer@glory.com",
        "password": "employerpass123",
        "role": "employer"
    }
    client.post("/users", json=payload)
    res = client.post("/login", data={
        "username": payload["email"],
        "password": payload["password"]
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
