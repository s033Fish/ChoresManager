from twilio.rest import Client
from django.conf import settings

# Twilio credentials
TWILIO_ACCOUNT_SID = settings.TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN = settings.TWILIO_AUTH_TOKEN
TWILIO_PHONE_NUMBER = "+18788797709"  # Replace with your Twilio phone number

def send_sms(phone_number, message):
    """
    Send an SMS message using Twilio.
    """
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        message = client.messages.create(
            body=message,               # Message content
            from_=TWILIO_PHONE_NUMBER,  # Your Twilio number
            to=phone_number             # Recipient's phone number
        )
        print(f"Message SID: {message.sid}")
    except Exception as e:
        print(f"Error sending SMS message: {e}")

