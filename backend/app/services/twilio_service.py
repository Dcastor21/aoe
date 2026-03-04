# app/services/twilio_service.py
from twilio.rest import Client
from app.config import settings


twilio = Client(settings.twilio_account_sid, settings.twilio_auth_token)


async def send_sms(to: str, message: str) -> bool:
    try:
        msg = twilio.messages.create(
            body=message,
            from_=settings.twilio_from_number,
            to=to
        )
        print(f'SMS sent: {msg.sid}')
        return True
    except Exception as e:
        print(f'SMS failed: {e}')
        return False


# Message templates matching TSD Section 6.3
TEMPLATES = {
    'booking_confirmed':  'Hi {name}! Cleaning confirmed {date}. Quote: ${price}. Code: {code}',
    'tech_dispatch':      'Job: {address}. Client: {client}. Time: {time}.',
    'qa_alert':           'QA Alert: Job {job_id} scored {score}/5. Review required.',
    'route_updated':      'Route updated. Next stop: {address} at {eta}.',
}

