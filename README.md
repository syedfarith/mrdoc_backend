# Healthcare Booking System - Backend

A FastAPI-based backend service for managing healthcare appointments and doctor information.

## 🚀 Features

### Core Functionality
- **Doctor Management**: Add, view, and manage doctor profiles with specialties and availability
- **Appointment Booking**: Schedule appointments with automatic validation and conflict prevention
- **Appointment Cancellation**: Cancel appointments and automatically free up slots
- **Slot Management**: Real-time tracking of available appointment slots per doctor
- **Business Hours Validation**: Automatic enforcement of 9 AM - 5 PM booking hours

### AI-Powered Chatbot
- **Intelligent Assistant**: AI-powered chatbot using Groq/LLaMA for medical assistance
- **Doctor Suggestions**: Smart doctor recommendations based on patient symptoms/conditions
- **Conversation History**: Persistent chat sessions with conversation memory
- **Medical Knowledge**: Comprehensive healthcare information and guidance
- **Session Management**: Unique session tracking for personalized experiences

### Email Notification System
- **Appointment Confirmations**: Automated email confirmations for new bookings
- **Cancellation Notifications**: Email alerts for appointment cancellations
- **Welcome Messages**: Personalized welcome emails for new patients
- **Reminder System**: Appointment reminder emails (configurable)
- **Professional Templates**: Beautifully formatted HTML email templates

### API & Documentation
- **RESTful API**: Well-structured REST endpoints with proper HTTP status codes
- **OpenAPI/Swagger**: Auto-generated interactive API documentation
- **Data Validation**: Comprehensive input validation using Pydantic schemas
- **Error Handling**: Detailed error responses with helpful messages
- **CORS Support**: Cross-origin resource sharing for frontend integration

### Database & Security
- **SQLite Integration**: Lightweight database with SQLAlchemy ORM
- **Data Integrity**: Foreign key constraints and data validation
- **Automated Migrations**: Database schema management and initialization
- **Backup Support**: Easy database backup and restore functionality

### Development & Deployment
- **Hot Reload**: Development server with automatic code reloading
- **Testing Suite**: Comprehensive test coverage with pytest
- **Environment Configuration**: Flexible configuration via environment variables
- **Production Ready**: Optimized for deployment on Vercel, Heroku, and other platforms
- **Monitoring**: Built-in logging and error tracking

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd healthcare-booking-system/backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Initialize Database
```bash
python reset_db.py
```

## 🚀 Running the Server

### Development Mode
```bash
uvicorn main:app --host localhost --port 8000 --reload
```

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The server will start at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

## 📊 Database

The application uses SQLite database with the following tables:

### Doctors Table
- `id`: Primary key
- `name`: Doctor's full name
- `specialty`: Medical specialty
- `available_slots`: Number of available appointment slots
- `rating`: Doctor's rating (1-5)
- `location`: Practice location

### Appointments Table
- `id`: Primary key
- `patient_name`: Patient's name
- `patient_email`: Patient's email
- `appointment_date`: Date and time of appointment
- `doctor_id`: Foreign key to doctors table
- `is_cancelled`: Cancellation status
- `notes`: Additional notes

## 🔧 API Endpoints

### Doctors
- `GET /doctors/` - Get all doctors
- `GET /doctors/{doctor_id}` - Get doctor by ID
- `POST /doctors/` - Add new doctor
- `POST /doctors/{doctor_id}/appointments/` - Book appointment with doctor

### Appointments
- `GET /appointments/` - Get all appointments
- `DELETE /appointments/{appointment_id}` - Cancel appointment

### Chatbot
- `POST /chatbot/message` - Send message to chatbot
- `GET /chatbot/conversation/{session_id}` - Get conversation history
- `DELETE /chatbot/conversation/{session_id}` - Clear conversation history
- `POST /chatbot/suggest-doctors` - Get doctor suggestions based on condition

## 📝 Example Usage

### Add a Doctor
```bash
curl -X POST "http://localhost:8000/doctors/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. John Smith",
    "specialty": "Cardiology",
    "available_slots": 10,
    "rating": 4.5,
    "location": "New York"
  }'
```

### Book an Appointment
```bash
curl -X POST "http://localhost:8000/doctors/1/appointments/" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_name": "Jane Doe",
    "patient_email": "jane@example.com",
    "appointment_date": "2024-12-01T10:00:00",
    "notes": "Regular checkup"
  }'
```

### Chat with Bot
```bash
curl -X POST "http://localhost:8000/chatbot/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need to book an appointment for chest pain",
    "session_id": "user123"
  }'
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/ -v
```

Run tests with coverage:
```bash
python -m pytest tests/ --cov=. --cov-report=html
```

## 📁 Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── database.py          # Database models and configuration
├── schemas.py           # Pydantic models for request/response
├── auth.py             # Authentication utilities
├── email_service.py    # Email notification service
├── chatbot_service.py  # AI chatbot implementation
├── requirements.txt    # Python dependencies
├── reset_db.py        # Database initialization script
├── tests/             # Test files
│   ├── __init__.py
│   └── test_main.py
└── __pycache__/       # Python bytecode cache
```

## 🔐 Environment Variables

Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=sqlite:///./healthcare.db

# Email Configuration (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# API Configuration
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 🚀 Deployment

### Deploy to Vercel

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Create `vercel.json` in backend directory:
```json
{
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ]
}
```

3. Deploy:
```bash
vercel --prod
```

### Deploy to Heroku

1. Create `Procfile`:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

2. Deploy:
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

## 🔧 Configuration

### CORS Settings
Update `main.py` to configure CORS for your frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://your-frontend-domain.com"  # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📚 Dependencies

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation using Python type hints
- **Uvicorn**: Lightning-fast ASGI server
- **Pytest**: Testing framework
- **Requests**: HTTP library for testing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   # Kill process on port 8000
   lsof -ti:8000 | xargs kill -9
   ```

2. **Database locked**:
   ```bash
   # Reset database
   python reset_db.py
   ```

3. **Import errors**:
   ```bash
   # Ensure virtual environment is activated
   pip install -r requirements.txt
   ```

### Support

For support and questions, please open an issue on GitHub or contact the development team.