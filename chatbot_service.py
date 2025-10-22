import json
from typing import List, Dict, Optional
from datetime import datetime
from groq import Groq
from sqlalchemy.orm import Session
from database import get_db, Doctor
import asyncio

class HealthcareChatbot:
    def __init__(self):
        self.api_key = "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"
        self.client = Groq(api_key=self.api_key)
        self.conversations = {}
        self.model = "llama-3.1-8b-instant"
        
    def get_doctors_list(self, db: Session) -> str:
        """Get current list of doctors from database"""
        try:
            doctors = db.query(Doctor).all()
            if not doctors:
                return "Currently no doctors are available in our system."
            
            doctors_info = []
            for doctor in doctors:
                available_slots = max(0, doctor.slots_per_day - len([
                    apt for apt in doctor.appointments if not apt.is_cancelled
                ]))
                
                doctors_info.append(
                    f"Dr. {doctor.name} - {doctor.specialty} "
                    f"({available_slots}/{doctor.slots_per_day} slots available)"
                )
            
            return "Available doctors in our system:\n" + "\n".join(doctors_info)
        except Exception as e:
            return "Unable to fetch current doctor list."
    
    def get_system_prompt(self, doctors_list: str) -> str:
        """Generate system prompt with current doctor information"""
        return f"""You are MedBot, a helpful medical assistant for the Healthcare Appointment Booking System. 

Your responsibilities:
1. Answer medical questions in a simple, polite, and informative way
2. Recommend appropriate doctors from our available specialists based on user symptoms/conditions
3. Provide general health advice and information
4. Help users understand when they should seek medical attention
5. Assist with appointment-related questions

IMPORTANT GUIDELINES:
- Always be empathetic and supportive
- Provide clear, easy-to-understand explanations
- Never diagnose or provide specific medical advice that requires professional examination
- Always recommend consulting with a healthcare professional for serious concerns
- When suggesting doctors, use ONLY doctors from our current list
- If a user's condition requires a specialist we don't have, recommend they contact our administration
- Remember conversation context to provide personalized responses

CURRENT AVAILABLE DOCTORS:
{doctors_list}

CONVERSATION STYLE:
- Use a warm, professional tone
- Include relevant emojis to make responses friendly
- Keep responses concise but informative
- Ask follow-up questions when appropriate
- Show genuine care for the user's health concerns

Remember: You are representing our Healthcare Booking System, so always maintain professionalism while being approachable and helpful."""

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        if session_id not in self.conversations:
            self.conversations[session_id] = {
                "messages": [],
                "created_at": datetime.now(),
                "last_activity": datetime.now()
            }
        return self.conversations[session_id]["messages"]
    
    def add_message_to_history(self, session_id: str, role: str, content: str):
        """Add a message to conversation history"""
        if session_id not in self.conversations:
            self.conversations[session_id] = {
                "messages": [],
                "created_at": datetime.now(),
                "last_activity": datetime.now()
            }
        
        self.conversations[session_id]["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 20 messages to manage memory
        if len(self.conversations[session_id]["messages"]) > 20:
            self.conversations[session_id]["messages"] = \
                self.conversations[session_id]["messages"][-20:]
        
        self.conversations[session_id]["last_activity"] = datetime.now()
    
    def clean_old_conversations(self, hours: int = 24):
        """Clean conversations older than specified hours"""
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        sessions_to_remove = []
        for session_id, conversation in self.conversations.items():
            if conversation["last_activity"] < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.conversations[session_id]
    
    async def get_response(self, user_message: str, session_id: str, db: Session) -> Dict:
        """Get chatbot response with conversation context"""
        try:
            # Clean old conversations periodically
            self.clean_old_conversations()
            
            # Get current doctors list
            doctors_list = self.get_doctors_list(db)
            
            # Get conversation history
            conversation_history = self.get_conversation_history(session_id)
            
            # Build messages for API call
            messages = [
                {
                    "role": "system",
                    "content": self.get_system_prompt(doctors_list)
                }
            ]
            
            # Add conversation history (last 10 messages for context)
            recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
            for msg in recent_history:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Get response from Groq
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1024,
                temperature=0.7
            )
            
            bot_response = completion.choices[0].message.content
            
            # Add messages to conversation history
            self.add_message_to_history(session_id, "user", user_message)
            self.add_message_to_history(session_id, "assistant", bot_response)
            
            return {
                "success": True,
                "response": bot_response,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "conversation_length": len(self.conversations[session_id]["messages"])
            }
            
        except Exception as e:
            error_msg = "I'm sorry, I'm experiencing some technical difficulties. Please try again in a moment or contact our support team for assistance."
            
            # Still add user message to history even if response fails
            self.add_message_to_history(session_id, "user", user_message)
            self.add_message_to_history(session_id, "assistant", error_msg)
            
            return {
                "success": False,
                "response": error_msg,
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_conversation_summary(self, session_id: str) -> Dict:
        """Get summary of conversation for a session"""
        if session_id not in self.conversations:
            return {
                "exists": False,
                "message": "No conversation found for this session"
            }
        
        conversation = self.conversations[session_id]
        return {
            "exists": True,
            "session_id": session_id,
            "created_at": conversation["created_at"].isoformat(),
            "last_activity": conversation["last_activity"].isoformat(),
            "message_count": len(conversation["messages"]),
            "recent_messages": conversation["messages"][-5:] if conversation["messages"] else []
        }
    
    def suggest_doctors_for_condition(self, condition: str, db: Session) -> List[Dict]:
        """Suggest doctors based on medical condition/specialty"""
        try:
            doctors = db.query(Doctor).all()
            suggestions = []
            
            # Simple keyword matching for specialties
            condition_lower = condition.lower()
            specialty_keywords = {
                'heart': ['cardiology', 'cardiac'],
                'skin': ['dermatology', 'dermatologist'],
                'bone': ['orthopedic', 'orthopedics'],
                'child': ['pediatric', 'pediatrics'],
                'brain': ['neurology', 'neurologist'],
                'eye': ['ophthalmology', 'ophthalmologist'],
                'mental': ['psychiatry', 'psychology'],
                'pregnancy': ['obstetrics', 'gynecology'],
                'surgery': ['surgery', 'surgical']
            }
            
            for doctor in doctors:
                available_slots = max(0, doctor.slots_per_day - len([
                    apt for apt in doctor.appointments if not apt.is_cancelled
                ]))
                
                if available_slots > 0:  # Only suggest doctors with available slots
                    doctor_info = {
                        "id": doctor.id,
                        "name": doctor.name,
                        "specialty": doctor.specialty,
                        "available_slots": available_slots,
                        "relevance_score": 0
                    }
                    
                    # Calculate relevance score
                    specialty_lower = doctor.specialty.lower()
                    
                    # Direct specialty match
                    if any(keyword in specialty_lower for keywords in specialty_keywords.values() for keyword in keywords):
                        for condition_key, keywords in specialty_keywords.items():
                            if condition_key in condition_lower:
                                if any(keyword in specialty_lower for keyword in keywords):
                                    doctor_info["relevance_score"] = 10
                                    break
                    
                    suggestions.append(doctor_info)
            
            # Sort by relevance score and available slots
            suggestions.sort(key=lambda x: (x["relevance_score"], x["available_slots"]), reverse=True)
            
            return suggestions[:3]  # Return top 3 suggestions
            
        except Exception as e:
            print(f"Error suggesting doctors: {str(e)}")
            return []

# Create global chatbot instance
healthcare_chatbot = HealthcareChatbot()