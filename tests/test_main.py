import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db
from database import Base
import json

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def client():
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    # Drop test database tables
    Base.metadata.drop_all(bind=engine)

def test_add_doctor_valid(client):
    """Test adding a valid doctor"""
    doctor_data = {
        "name": "Dr. John Smith",
        "specialty": "Cardiology",
        "slots_per_day": 10
    }
    
    response = client.post("/doctors/", json=doctor_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == doctor_data["name"]
    assert data["specialty"] == doctor_data["specialty"]
    assert data["slots_per_day"] == doctor_data["slots_per_day"]
    assert data["available_slots"] == doctor_data["slots_per_day"]
    assert "id" in data
    assert "created_at" in data

def test_add_doctor_invalid_slots(client):
    """Test adding doctor with invalid slots"""
    doctor_data = {
        "name": "Dr. Jane Doe",
        "specialty": "Neurology",
        "slots_per_day": -5
    }
    
    response = client.post("/doctors/", json=doctor_data)
    assert response.status_code == 422

def test_add_duplicate_doctor(client):
    """Test adding duplicate doctor"""
    doctor_data = {
        "name": "Dr. John Smith",
        "specialty": "Cardiology",
        "slots_per_day": 10
    }
    
    # Add doctor first time
    response1 = client.post("/doctors/", json=doctor_data)
    assert response1.status_code == 201
    
    # Try to add same doctor again
    response2 = client.post("/doctors/", json=doctor_data)
    assert response2.status_code == 400

def test_get_doctors_empty(client):
    """Test getting doctors when none exist"""
    response = client.get("/doctors/")
    assert response.status_code == 200
    assert response.json() == []

def test_get_doctors_with_data(client):
    """Test getting doctors when they exist"""
    # Add a doctor first
    doctor_data = {
        "name": "Dr. John Smith",
        "specialty": "Cardiology",
        "slots_per_day": 10
    }
    client.post("/doctors/", json=doctor_data)
    
    response = client.get("/doctors/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == doctor_data["name"]

def test_get_doctor_by_id(client):
    """Test getting specific doctor by ID"""
    # Add a doctor first
    doctor_data = {
        "name": "Dr. John Smith",
        "specialty": "Cardiology",
        "slots_per_day": 10
    }
    add_response = client.post("/doctors/", json=doctor_data)
    doctor_id = add_response.json()["id"]
    
    response = client.get(f"/doctors/{doctor_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == doctor_id
    assert data["name"] == doctor_data["name"]

def test_get_doctor_not_found(client):
    """Test getting non-existent doctor"""
    response = client.get("/doctors/999")
    assert response.status_code == 404

def test_book_appointment_valid(client):
    """Test booking a valid appointment"""
    # Add a doctor first
    doctor_data = {
        "name": "Dr. John Smith",
        "specialty": "Cardiology",
        "slots_per_day": 10
    }
    doctor_response = client.post("/doctors/", json=doctor_data)
    doctor_id = doctor_response.json()["id"]
    
    # Book appointment
    appointment_data = {
        "patient_name": "Alice Johnson",
        "appointment_date": "2024-12-25",
        "time_slot": "10:00"
    }
    
    response = client.post(f"/doctors/{doctor_id}/appointments/", json=appointment_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["patient_name"] == appointment_data["patient_name"]
    assert data["appointment_date"] == appointment_data["appointment_date"]
    assert data["time_slot"] == appointment_data["time_slot"]
    assert data["doctor_id"] == doctor_id
    assert data["is_cancelled"] == False

def test_book_appointment_invalid_time(client):
    """Test booking appointment with invalid time"""
    # Add a doctor first
    doctor_data = {
        "name": "Dr. John Smith",
        "specialty": "Cardiology",
        "slots_per_day": 10
    }
    doctor_response = client.post("/doctors/", json=doctor_data)
    doctor_id = doctor_response.json()["id"]
    
    # Try to book appointment outside working hours
    appointment_data = {
        "patient_name": "Alice Johnson",
        "appointment_date": "2024-12-25",
        "time_slot": "20:00"  # 8 PM - outside working hours
    }
    
    response = client.post(f"/doctors/{doctor_id}/appointments/", json=appointment_data)
    assert response.status_code == 422

def test_book_appointment_doctor_not_found(client):
    """Test booking appointment with non-existent doctor"""
    appointment_data = {
        "patient_name": "Alice Johnson",
        "appointment_date": "2024-12-25",
        "time_slot": "10:00"
    }
    
    response = client.post("/doctors/999/appointments/", json=appointment_data)
    assert response.status_code == 404

def test_book_appointment_no_slots(client):
    """Test booking appointment when no slots available"""
    # Add a doctor with only 1 slot
    doctor_data = {
        "name": "Dr. John Smith",
        "specialty": "Cardiology",
        "slots_per_day": 1
    }
    doctor_response = client.post("/doctors/", json=doctor_data)
    doctor_id = doctor_response.json()["id"]
    
    # Book first appointment
    appointment_data1 = {
        "patient_name": "Alice Johnson",
        "appointment_date": "2024-12-25",
        "time_slot": "10:00"
    }
    client.post(f"/doctors/{doctor_id}/appointments/", json=appointment_data1)
    
    # Try to book second appointment (should fail)
    appointment_data2 = {
        "patient_name": "Bob Smith",
        "appointment_date": "2024-12-25",
        "time_slot": "11:00"
    }
    
    response = client.post(f"/doctors/{doctor_id}/appointments/", json=appointment_data2)
    assert response.status_code == 400

def test_cancel_appointment(client):
    """Test canceling an appointment"""
    # Add doctor and book appointment
    doctor_data = {
        "name": "Dr. John Smith",
        "specialty": "Cardiology",
        "slots_per_day": 10
    }
    doctor_response = client.post("/doctors/", json=doctor_data)
    doctor_id = doctor_response.json()["id"]
    
    appointment_data = {
        "patient_name": "Alice Johnson",
        "appointment_date": "2024-12-25",
        "time_slot": "10:00"
    }
    
    appointment_response = client.post(f"/doctors/{doctor_id}/appointments/", json=appointment_data)
    appointment_id = appointment_response.json()["id"]
    
    # Cancel appointment
    response = client.delete(f"/appointments/{appointment_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "successfully cancelled" in data["message"]

def test_cancel_nonexistent_appointment(client):
    """Test canceling non-existent appointment"""
    response = client.delete("/appointments/999")
    assert response.status_code == 404

def test_cancel_already_cancelled_appointment(client):
    """Test canceling already cancelled appointment"""
    # Add doctor and book appointment
    doctor_data = {
        "name": "Dr. John Smith",
        "specialty": "Cardiology",
        "slots_per_day": 10
    }
    doctor_response = client.post("/doctors/", json=doctor_data)
    doctor_id = doctor_response.json()["id"]
    
    appointment_data = {
        "patient_name": "Alice Johnson",
        "appointment_date": "2024-12-25",
        "time_slot": "10:00"
    }
    
    appointment_response = client.post(f"/doctors/{doctor_id}/appointments/", json=appointment_data)
    appointment_id = appointment_response.json()["id"]
    
    # Cancel appointment first time
    client.delete(f"/appointments/{appointment_id}")
    
    # Try to cancel again
    response = client.delete(f"/appointments/{appointment_id}")
    assert response.status_code == 400

def test_slots_freed_after_cancellation(client):
    """Test that slots are freed after cancellation"""
    # Add doctor with 1 slot
    doctor_data = {
        "name": "Dr. John Smith",
        "specialty": "Cardiology",
        "slots_per_day": 1
    }
    doctor_response = client.post("/doctors/", json=doctor_data)
    doctor_id = doctor_response.json()["id"]
    
    # Book appointment (uses up the slot)
    appointment_data = {
        "patient_name": "Alice Johnson",
        "appointment_date": "2024-12-25",
        "time_slot": "10:00"
    }
    
    appointment_response = client.post(f"/doctors/{doctor_id}/appointments/", json=appointment_data)
    appointment_id = appointment_response.json()["id"]
    
    # Verify no slots available
    doctor_response = client.get(f"/doctors/{doctor_id}")
    assert doctor_response.json()["available_slots"] == 0
    
    # Cancel appointment
    client.delete(f"/appointments/{appointment_id}")
    
    # Verify slot is available again
    doctor_response = client.get(f"/doctors/{doctor_id}")
    assert doctor_response.json()["available_slots"] == 1

def test_get_all_appointments(client):
    """Test getting all appointments"""
    # Add doctor and book appointment
    doctor_data = {
        "name": "Dr. John Smith",
        "specialty": "Cardiology",
        "slots_per_day": 10
    }
    doctor_response = client.post("/doctors/", json=doctor_data)
    doctor_id = doctor_response.json()["id"]
    
    appointment_data = {
        "patient_name": "Alice Johnson",
        "appointment_date": "2024-12-25",
        "time_slot": "10:00"
    }
    
    client.post(f"/doctors/{doctor_id}/appointments/", json=appointment_data)
    
    # Get all appointments
    response = client.get("/appointments/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["patient_name"] == appointment_data["patient_name"]