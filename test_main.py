import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db
from database import Base, Account

client = TestClient(app)
HEADERS = {"X-API-Key": "super-secret-key"}

# Setup an isolated SQLite database for testing
TEST_DATABASE_URL = "sqlite:///./test_api.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    """Overrides the main database dependency to use the test database."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

def setup_module(module):
    """Pytest hook: Runs once before any tests execute to build the test schema."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    
    if not db.query(Account).filter(Account.id == 1).first():
        db.add(Account(id=1, customer_name="Test User", balance=100000.0, status="active"))
        db.commit()
    db.close()

# --- Unit Tests ---
def test_unauthorized_access():
    response = client.post(
        "/transactions/", 
        json={"account_id": 1, "amount": 100},
        headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 401

def test_fraud_alert_logic():
    response = client.post(
        "/transactions/", 
        json={"account_id": 1, "amount": 15000}, 
        headers=HEADERS
    )
    assert response.status_code == 200
    assert response.json()["status"] == "flagged_for_fraud"

def test_insufficient_funds():
    response = client.post(
        "/transactions/", 
        json={"account_id": 1, "amount": 200000}, 
        headers=HEADERS
    )
    assert response.status_code == 200
    assert response.json()["status"] == "declined"

def test_successful_transaction():
    response = client.post(
        "/transactions/", 
        json={"account_id": 1, "amount": 500}, 
        headers=HEADERS
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert "new_balance" in response.json()