import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

try:
    from email_config import *
except ImportError:
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SENDER_EMAIL = "healthcare.booking.system@gmail.com"
    SENDER_PASSWORD = "your_app_password_here"
    SENDER_NAME = "Healthcare Booking System"
    DEVELOPMENT_MODE = True
    SEND_WELCOME_EMAILS = True
    SEND_APPOINTMENT_NOTIFICATIONS = True

class EmailService:
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.sender_email = SENDER_EMAIL
        self.sender_password = SENDER_PASSWORD
        self.sender_name = SENDER_NAME
        self.development_mode = DEVELOPMENT_MODE

    def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        try:
            if self.development_mode:
                print(f"\n{'='*80}\n📧 EMAIL SENT (DEVELOPMENT MODE)\n{'='*80}\nTo: {to_email}\nSubject: {subject}\nContent:\n{text_content if text_content else 'HTML content available'}\n{'='*80}")
                return True

            print(f"🔄 Attempting to send email to {to_email}...")
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = to_email

            if text_content:
                message.attach(MIMEText(text_content, "plain"))
            message.attach(MIMEText(html_content, "html"))

            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, message.as_string())

            print(f"✅ Email sent successfully to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication Error: {str(e)}")
            return False
        except smtplib.SMTPRecipientsRefused as e:
            print(f"❌ Invalid recipient email: {str(e)}")
            return False
        except smtplib.SMTPServerDisconnected as e:
            print(f"❌ SMTP Server disconnected: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Error sending email to {to_email}: {str(e)}")
            return False

    def send_appointment_notification(self, doctor_email: str, doctor_name: str, 
                                    patient_name: str, appointment_date: str, 
                                    time_slot: str, appointment_id: int) -> bool:
        """
        Send appointment notification to doctor
        """
        # Format the date and time
        try:
            date_obj = datetime.strptime(appointment_date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%B %d, %Y')  # e.g., "December 25, 2024"
        except:
            formatted_date = appointment_date

        # Format time
        try:
            time_obj = datetime.strptime(time_slot, '%H:%M')
            formatted_time = time_obj.strftime('%I:%M %p')  # e.g., "10:00 AM"
        except:
            formatted_time = time_slot

        subject = f"🏥 New Appointment Booked - {patient_name}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                    border: 1px solid #e9ecef;
                }}
                .appointment-details {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border-left: 4px solid #667eea;
                }}
                .detail-row {{
                    display: flex;
                    justify-content: space-between;
                    margin: 10px 0;
                    padding: 5px 0;
                }}
                .label {{
                    font-weight: bold;
                    color: #495057;
                }}
                .value {{
                    color: #2d3748;
                }}
                .footer {{
                    text-align: center;
                    color: #6c757d;
                    font-size: 14px;
                    margin-top: 30px;
                }}
                .emoji {{
                    font-size: 1.2em;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1><span class="emoji">🏥</span> Healthcare Booking System</h1>
                <p>New Appointment Notification</p>
            </div>
            
            <div class="content">
                <h2>Hello Dr. {doctor_name},</h2>
                
                <p>You have a new appointment booking! A patient has scheduled an appointment with you.</p>
                
                <div class="appointment-details">
                    <h3><span class="emoji">📋</span> Appointment Details</h3>
                    
                    <div class="detail-row">
                        <span class="label"><span class="emoji">👤</span> Patient Name:</span>
                        <span class="value">{patient_name}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="label"><span class="emoji">📅</span> Date:</span>
                        <span class="value">{formatted_date}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="label"><span class="emoji">🕐</span> Time:</span>
                        <span class="value">{formatted_time}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="label"><span class="emoji">🔢</span> Appointment ID:</span>
                        <span class="value">#{appointment_id}</span>
                    </div>
                </div>
                
                <p><strong>Please note:</strong> This appointment has been confirmed and is now in your schedule. 
                The patient is expecting to meet with you at the specified time.</p>
                
                <p>If you need to make any changes or have questions about this appointment, 
                please contact our healthcare administration team.</p>
                
                <p>Thank you for your continued service to our patients!</p>
                
                <p>Best regards,<br>
                <strong>Healthcare Booking System Team</strong></p>
            </div>
            
            <div class="footer">
                <p>This is an automated notification from Healthcare Booking System.</p>
                <p>Please do not reply to this email. For support, contact our administration team.</p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Healthcare Booking System - New Appointment Notification

        Hello Dr. {doctor_name},

        You have a new appointment booking!

        Appointment Details:
        - Patient Name: {patient_name}
        - Date: {formatted_date}
        - Time: {formatted_time}
        - Appointment ID: #{appointment_id}

        This appointment has been confirmed and is now in your schedule.

        Best regards,
        Healthcare Booking System Team
        """

        return self.send_email(doctor_email, subject, html_content, text_content)

    def send_welcome_doctor_email(self, doctor_email: str, doctor_name: str, doctor_id: int) -> bool:
        """
        Send welcome email to newly registered doctor
        """
        subject = f"🎉 Welcome to Healthcare Booking System, Dr. {doctor_name}!"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                    border: 1px solid #e9ecef;
                }}
                .doctor-info {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border-left: 4px solid #28a745;
                }}
                .footer {{
                    text-align: center;
                    color: #6c757d;
                    font-size: 14px;
                    margin-top: 30px;
                }}
                .emoji {{
                    font-size: 1.2em;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1><span class="emoji">🏥</span> Healthcare Booking System</h1>
                <p>Welcome to Our Platform!</p>
            </div>
            
            <div class="content">
                <h2>Welcome Dr. {doctor_name}!</h2>
                
                <p>Congratulations! Your registration with Healthcare Booking System has been completed successfully.</p>
                
                <div class="doctor-info">
                    <h3><span class="emoji">👨‍⚕️</span> Your Profile Information</h3>
                    <p><strong>Doctor ID:</strong> #{doctor_id}</p>
                    <p><strong>Email:</strong> {doctor_email}</p>
                    <p><strong>Registration Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
                </div>
                
                <h3><span class="emoji">📋</span> What's Next?</h3>
                <ul>
                    <li><span class="emoji">📧</span> You'll receive email notifications when patients book appointments with you</li>
                    <li><span class="emoji">📅</span> Patients can now schedule appointments based on your availability</li>
                    <li><span class="emoji">👥</span> Manage your schedule through our healthcare administration team</li>
                </ul>
                
                <p>We're excited to have you as part of our healthcare network. Your expertise and dedication 
                will help us provide excellent care to our patients.</p>
                
                <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                
                <p>Thank you for joining us!</p>
                
                <p>Best regards,<br>
                <strong>Healthcare Booking System Team</strong></p>
            </div>
            
            <div class="footer">
                <p>This is an automated welcome message from Healthcare Booking System.</p>
                <p>For support, contact our administration team.</p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Healthcare Booking System - Welcome!

        Welcome Dr. {doctor_name}!

        Your registration has been completed successfully.

        Your Profile Information:
        - Doctor ID: #{doctor_id}
        - Email: {doctor_email}
        - Registration Date: {datetime.now().strftime('%B %d, %Y')}

        What's Next:
        - You'll receive email notifications for new appointments
        - Patients can now book appointments with you
        - Manage your schedule through our administration team

        Thank you for joining us!

        Best regards,
        Healthcare Booking System Team
        """

        return self.send_email(doctor_email, subject, html_content, text_content)

    def send_cancellation_notification(self, doctor_email: str, doctor_name: str,
                                     patient_name: str, appointment_date: str,
                                     time_slot: str, appointment_id: int,
                                     cancellation_reason: str = "Patient request") -> bool:
        """
        Send appointment cancellation notification to doctor
        """
        # Format the date and time
        try:
            date_obj = datetime.strptime(appointment_date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%B %d, %Y')  # e.g., "December 25, 2024"
        except:
            formatted_date = appointment_date

        # Format time
        try:
            time_obj = datetime.strptime(time_slot, '%H:%M')
            formatted_time = time_obj.strftime('%I:%M %p')  # e.g., "10:00 AM"
        except:
            formatted_time = time_slot

        subject = f"❌ Appointment Cancelled - {patient_name}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #fc8181 0%, #e53e3e 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                    border: 1px solid #e9ecef;
                }}
                .appointment-details {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border-left: 4px solid #e53e3e;
                }}
                .detail-row {{
                    display: flex;
                    justify-content: space-between;
                    margin: 10px 0;
                    padding: 5px 0;
                }}
                .label {{
                    font-weight: bold;
                    color: #495057;
                }}
                .value {{
                    color: #2d3748;
                }}
                .cancellation-notice {{
                    background: #fed7d7;
                    border: 1px solid #feb2b2;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    color: #742a2a;
                }}
                .footer {{
                    text-align: center;
                    color: #6c757d;
                    font-size: 14px;
                    margin-top: 30px;
                }}
                .emoji {{
                    font-size: 1.2em;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1><span class="emoji">🏥</span> Healthcare Booking System</h1>
                <p>Appointment Cancellation Notice</p>
            </div>
            
            <div class="content">
                <h2>Hello Dr. {doctor_name},</h2>
                
                <div class="cancellation-notice">
                    <h3><span class="emoji">❌</span> Appointment Cancelled</h3>
                    <p>An appointment that was scheduled with you has been cancelled.</p>
                </div>
                
                <div class="appointment-details">
                    <h3><span class="emoji">📋</span> Cancelled Appointment Details</h3>
                    
                    <div class="detail-row">
                        <span class="label"><span class="emoji">👤</span> Patient Name:</span>
                        <span class="value">{patient_name}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="label"><span class="emoji">📅</span> Date:</span>
                        <span class="value">{formatted_date}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="label"><span class="emoji">🕐</span> Time:</span>
                        <span class="value">{formatted_time}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="label"><span class="emoji">🔢</span> Appointment ID:</span>
                        <span class="value">#{appointment_id}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="label"><span class="emoji">📝</span> Cancellation Reason:</span>
                        <span class="value">{cancellation_reason}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="label"><span class="emoji">🕒</span> Cancelled At:</span>
                        <span class="value">{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</span>
                    </div>
                </div>
                
                <p><strong>Good News:</strong> This time slot is now available for other patients to book!</p>
                
                <p>This cancellation has been processed automatically, and your schedule has been updated accordingly. 
                You don't need to take any further action.</p>
                
                <p>If you have any questions about this cancellation or need to review your schedule, 
                please contact our healthcare administration team.</p>
                
                <p>Thank you for your understanding!</p>
                
                <p>Best regards,<br>
                <strong>Healthcare Booking System Team</strong></p>
            </div>
            
            <div class="footer">
                <p>This is an automated notification from Healthcare Booking System.</p>
                <p>Please do not reply to this email. For support, contact our administration team.</p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Healthcare Booking System - Appointment Cancellation Notice

        Hello Dr. {doctor_name},

        An appointment scheduled with you has been cancelled.

        Cancelled Appointment Details:
        - Patient Name: {patient_name}
        - Date: {formatted_date}
        - Time: {formatted_time}
        - Appointment ID: #{appointment_id}
        - Cancellation Reason: {cancellation_reason}
        - Cancelled At: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

        This time slot is now available for other patients to book.
        Your schedule has been updated automatically.

        Best regards,
        Healthcare Booking System Team
        """

        return self.send_email(doctor_email, subject, html_content, text_content)

# Create a global instance
email_service = EmailService()