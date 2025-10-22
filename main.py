from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid

from database import get_db, Doctor, Appointment
from schemas import (
    DoctorCreate, DoctorResponse, AppointmentCreate, AppointmentResponse,
    ChatbotMessage, ChatbotResponse, ConversationSummary, DoctorSuggestion
)
from email_service import email_service
from chatbot_service import healthcare_chatbot

app = FastAPI(
    title="Healthcare Appointment Booking System",
    description="A comprehensive system for managing doctor appointments",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_doctor_available_slots(doctor: Doctor, db: Session) -> int:
    booked_appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor.id,
        Appointment.is_cancelled == False
    ).count()
    return max(0, doctor.slots_per_day - booked_appointments)

@app.post("/doctors/", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
async def add_doctor(doctor: DoctorCreate, db: Session = Depends(get_db)):
    """Add a new doctor to the system"""
    
    # Check if doctor with same name and specialty already exists
    existing_doctor_name = db.query(Doctor).filter(
        Doctor.name == doctor.name,
        Doctor.specialty == doctor.specialty
    ).first()
    
    if existing_doctor_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor with this name and specialty already exists"
        )
    
    # Check if email already exists
    existing_doctor_email = db.query(Doctor).filter(
        Doctor.email == doctor.email
    ).first()
    
    if existing_doctor_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor with this email already exists"
        )
    
    db_doctor = Doctor(
        name=doctor.name,
        specialty=doctor.specialty,
        email=doctor.email,
        slots_per_day=doctor.slots_per_day
    )
    
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    
    # Calculate available slots
    available_slots = get_doctor_available_slots(db_doctor, db)
    
    # Send welcome email to doctor (non-blocking)
    try:
        email_service.send_welcome_doctor_email(
            doctor_email=db_doctor.email,
            doctor_name=db_doctor.name,
            doctor_id=db_doctor.id
        )
    except Exception as e:
        print(f"Failed to send welcome email: {e}")
        # Don't fail the registration if email fails
    
    return DoctorResponse(
        id=db_doctor.id,
        name=db_doctor.name,
        specialty=db_doctor.specialty,
        email=db_doctor.email,
        slots_per_day=db_doctor.slots_per_day,
        available_slots=available_slots,
        created_at=db_doctor.created_at
    )

@app.get("/doctors/", response_model=List[DoctorResponse])
async def get_doctors(db: Session = Depends(get_db)):
    """Retrieve all doctors and their availability"""
    doctors = db.query(Doctor).all()
    
    doctor_responses = []
    for doctor in doctors:
        available_slots = get_doctor_available_slots(doctor, db)
        doctor_responses.append(DoctorResponse(
            id=doctor.id,
            name=doctor.name,
            specialty=doctor.specialty,
            email=doctor.email,
            slots_per_day=doctor.slots_per_day,
            available_slots=available_slots,
            created_at=doctor.created_at
        ))
    
    return doctor_responses

@app.get("/doctors/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a specific doctor"""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    available_slots = get_doctor_available_slots(doctor, db)
    
    return DoctorResponse(
        id=doctor.id,
        name=doctor.name,
        specialty=doctor.specialty,
        email=doctor.email,
        slots_per_day=doctor.slots_per_day,
        available_slots=available_slots,
        created_at=doctor.created_at
    )

@app.post("/doctors/{doctor_id}/appointments/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    doctor_id: int, 
    appointment: AppointmentCreate, 
    db: Session = Depends(get_db)
):
    """Book an appointment with a doctor"""
    
    # Check if doctor exists
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    # Check if slot is available
    available_slots = get_doctor_available_slots(doctor, db)
    if available_slots <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No available slots for this doctor"
        )
    
    # Check if same patient already has an appointment on the same date and time
    existing_appointment = db.query(Appointment).filter(
        Appointment.patient_name == appointment.patient_name,
        Appointment.appointment_date == appointment.appointment_date,
        Appointment.time_slot == appointment.time_slot,
        Appointment.is_cancelled == False
    ).first()
    
    if existing_appointment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient already has an appointment at this time slot"
        )
    
    # Check if doctor already has an appointment at this time slot
    doctor_appointment = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == appointment.appointment_date,
        Appointment.time_slot == appointment.time_slot,
        Appointment.is_cancelled == False
    ).first()
    
    if doctor_appointment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor already has an appointment at this time slot"
        )
    
    # Create appointment
    db_appointment = Appointment(
        patient_name=appointment.patient_name,
        appointment_date=appointment.appointment_date,
        time_slot=appointment.time_slot,
        doctor_id=doctor_id
    )
    
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    
    # Send email notification to doctor (non-blocking)
    try:
        email_service.send_appointment_notification(
            doctor_email=doctor.email,
            doctor_name=doctor.name,
            patient_name=db_appointment.patient_name,
            appointment_date=db_appointment.appointment_date,
            time_slot=db_appointment.time_slot,
            appointment_id=db_appointment.id
        )
    except Exception as e:
        print(f"Failed to send appointment notification email: {e}")
        # Don't fail the booking if email fails
    
    return AppointmentResponse(
        id=db_appointment.id,
        patient_name=db_appointment.patient_name,
        appointment_date=db_appointment.appointment_date,
        time_slot=db_appointment.time_slot,
        doctor_id=doctor.id,
        doctor_name=doctor.name,
        doctor_specialty=doctor.specialty,
        is_cancelled=db_appointment.is_cancelled,
        created_at=db_appointment.created_at
    )

@app.delete("/appointments/{appointment_id}")
async def cancel_appointment(appointment_id: int, db: Session = Depends(get_db)):
    """Cancel an appointment"""
    
    # Find the appointment with doctor information
    appointment = db.query(Appointment).join(Doctor).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    if appointment.is_cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment is already cancelled"
        )
    
    # Store appointment details before cancellation for email
    doctor_email = appointment.doctor.email
    doctor_name = appointment.doctor.name
    patient_name = appointment.patient_name
    appointment_date = appointment.appointment_date
    time_slot = appointment.time_slot
    
    # Cancel the appointment
    appointment.is_cancelled = True
    db.commit()
    
    # Send cancellation email notification to doctor (non-blocking)
    try:
        email_service.send_cancellation_notification(
            doctor_email=doctor_email,
            doctor_name=doctor_name,
            patient_name=patient_name,
            appointment_date=appointment_date,
            time_slot=time_slot,
            appointment_id=appointment_id,
            cancellation_reason="Patient request"
        )
        print(f"✅ Cancellation email sent to Dr. {doctor_name} ({doctor_email})")
    except Exception as e:
        print(f"❌ Failed to send cancellation email to Dr. {doctor_name}: {str(e)}")
        # Don't fail the cancellation if email fails
    
    return {"message": f"Appointment {appointment_id} has been successfully cancelled"}

@app.get("/appointments/", response_model=List[AppointmentResponse])
async def get_appointments(db: Session = Depends(get_db)):
    """Get all appointments"""
    appointments = db.query(Appointment).join(Doctor).all()
    
    appointment_responses = []
    for appointment in appointments:
        appointment_responses.append(AppointmentResponse(
            id=appointment.id,
            patient_name=appointment.patient_name,
            appointment_date=appointment.appointment_date,
            time_slot=appointment.time_slot,
            doctor_id=appointment.doctor.id,
            doctor_name=appointment.doctor.name,
            doctor_specialty=appointment.doctor.specialty,
            is_cancelled=appointment.is_cancelled,
            created_at=appointment.created_at
        ))
    
    return appointment_responses

# === CHATBOT ENDPOINTS ===

@app.post("/chatbot/message", response_model=ChatbotResponse)
async def chat_with_bot(
    message_data: ChatbotMessage,
    db: Session = Depends(get_db)
):
    """Send a message to the medical chatbot"""
    try:
        # Generate session ID if not provided
        session_id = message_data.session_id or str(uuid.uuid4())
        
        # Get response from chatbot
        response = await healthcare_chatbot.get_response(
            user_message=message_data.message,
            session_id=session_id,
            db=db
        )
        
        return ChatbotResponse(**response)
        
    except Exception as e:
        return ChatbotResponse(
            success=False,
            response="I'm sorry, I'm experiencing technical difficulties. Please try again later.",
            session_id=message_data.session_id or str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )

@app.get("/chatbot/conversation/{session_id}", response_model=ConversationSummary)
async def get_conversation_summary(session_id: str):
    """Get conversation summary for a session"""
    try:
        summary = healthcare_chatbot.get_conversation_summary(session_id)
        return ConversationSummary(**summary)
    except Exception as e:
        return ConversationSummary(
            exists=False,
            message=f"Error retrieving conversation: {str(e)}"
        )

@app.post("/chatbot/suggest-doctors", response_model=List[DoctorSuggestion])
async def suggest_doctors_for_condition(
    condition: str,
    db: Session = Depends(get_db)
):
    """Get doctor suggestions based on medical condition"""
    try:
        suggestions = healthcare_chatbot.suggest_doctors_for_condition(condition, db)
        return [DoctorSuggestion(**suggestion) for suggestion in suggestions]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting doctor suggestions: {str(e)}"
        )

@app.delete("/chatbot/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """Clear conversation history for a session"""
    try:
        if session_id in healthcare_chatbot.conversations:
            del healthcare_chatbot.conversations[session_id]
            return {"message": f"Conversation {session_id} cleared successfully"}
        else:
            return {"message": "Conversation not found"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing conversation: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Healthcare Appointment Booking System API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)