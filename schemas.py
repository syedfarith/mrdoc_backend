from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime, time

class DoctorCreate(BaseModel):
    name: str
    specialty: str
    email: str
    slots_per_day: int
    
    @validator('slots_per_day')
    def validate_slots(cls, v):
        if v <= 0:
            raise ValueError('Slots per day must be positive')
        return v
    
    @validator('name', 'specialty')
    def validate_strings(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('email')
    def validate_email(cls, v):
        import re
        if not v or not v.strip():
            raise ValueError('Email cannot be empty')
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v.strip()):
            raise ValueError('Invalid email format')
        return v.strip().lower()

class DoctorResponse(BaseModel):
    id: int
    name: str
    specialty: str
    email: str
    slots_per_day: int
    available_slots: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class AppointmentCreate(BaseModel):
    patient_name: str
    appointment_date: str  # Format: YYYY-MM-DD
    time_slot: str  # Format: HH:MM
    
    @validator('patient_name')
    def validate_patient_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Patient name cannot be empty')
        return v.strip()
    
    @validator('appointment_date')
    def validate_date(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v
    
    @validator('time_slot')
    def validate_time_slot(cls, v):
        try:
            parsed_time = datetime.strptime(v, '%H:%M').time()
            # Check if time is within working hours (9 AM - 5 PM)
            start_time = time(9, 0)  # 9:00 AM
            end_time = time(17, 0)   # 5:00 PM
            
            if not (start_time <= parsed_time <= end_time):
                raise ValueError('Time slot must be between 9:00 AM and 5:00 PM')
        except ValueError as e:
            if "does not match format" in str(e):
                raise ValueError('Time must be in HH:MM format')
            raise e
        return v

class AppointmentResponse(BaseModel):
    id: int
    patient_name: str
    appointment_date: str
    time_slot: str
    doctor_id: int
    doctor_name: str
    doctor_specialty: str
    is_cancelled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class AppointmentCancel(BaseModel):
    appointment_id: int

# Chatbot schemas
class ChatbotMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v.strip()) > 1000:
            raise ValueError('Message is too long (max 1000 characters)')
        return v.strip()

class ChatbotResponse(BaseModel):
    success: bool
    response: str
    session_id: str
    timestamp: str
    conversation_length: Optional[int] = None
    error: Optional[str] = None

class ConversationSummary(BaseModel):
    exists: bool
    session_id: Optional[str] = None
    created_at: Optional[str] = None
    last_activity: Optional[str] = None
    message_count: Optional[int] = None
    recent_messages: Optional[List[dict]] = None
    message: Optional[str] = None

class DoctorSuggestion(BaseModel):
    id: int
    name: str
    specialty: str
    available_slots: int
    relevance_score: int