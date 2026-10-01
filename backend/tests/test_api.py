import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.session import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in the shared in-memory DB
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "service" in data

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "DATAEXPIRY API"

def test_get_empty_data_records():
    response = client.get("/api/data")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_and_read_data_record():
    payload = {
        "record_id": "TST-9999",
        "data_type": "Test Customer Audit",
        "category": "Customer",
        "sensitivity": "High",
        "collection_purpose": "Test Collection",
        "current_usage": "Test Usage",
        "owner": "QA Engineering",
        "created_date": "2025-01-01",
        "retention_period": "2 years",
        "expiry_date": "2027-01-01",
        "status": "Active",
        "source": "Automated Unit Test"
    }

    # POST create
    create_resp = client.post("/api/data", json=payload)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["record_id"] == "TST-9999"
    assert created_data["id"] is not None

    # GET single record
    get_resp = client.get(f"/api/data/{created_data['record_id']}")
    assert get_resp.status_code == 200
    single_data = get_resp.json()
    assert single_data["record_id"] == "TST-9999"
    assert single_data["owner"] == "QA Engineering"

def test_invalid_data_validation():
    # Missing required fields like data_type, category
    invalid_payload = {
        "record_id": "INVALID-01"
    }
    response = client.post("/api/data", json=invalid_payload)
    assert response.status_code == 422  # Unprocessable Entity (Pydantic validation error)

def test_get_nonexistent_record():
    response = client.get("/api/data/NONEXISTENT-999")
    assert response.status_code == 404
