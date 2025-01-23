#!/usr/bin/env python3

from pathlib import Path
from django.core.management.base import BaseCommand  # Add this import
from twilio.rest import Client
from dotenv import load_dotenv
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# Twilio credentials
account_sid = os.getenv('ACCOUNT_SID')
auth_token = os.getenv('AUTH_TOKEN')


def send_sms(phone_number, message):
    """
    Send an SMS message using Twilio.
    """
    # Initialize the client
    client = Client(account_sid, auth_token)

    try:
        # Send a message
        message = client.messages.create(
            body=message,               # Message content
            from_="+18788797709",       # Your Twilio number
            to=phone_number             # Recipient's phone number
        )
        print(f"Message SID: {message.sid}")
    except Exception as e:
        print(f"Error sending SNS message: {e}")


class Command(BaseCommand):
    help = "Send an SMS message using Twilio"

    def add_arguments(self, parser):
        parser.add_argument('phone_number', type=str, help="Recipient's phone number (e.g., +1234567890)")
        parser.add_argument('message', type=str, help="Message content to send")

    def handle(self, *args, **kwargs):
        phone_number = kwargs['phone_number']
        message = kwargs['message']

        if not account_sid or not auth_token:
            self.stdout.write(self.style.ERROR("Twilio credentials are missing. Check your .env file."))
            return

        self.stdout.write(f"Sending SMS to {phone_number}...")
        send_sms(phone_number, message)
        self.stdout.write(self.style.SUCCESS("SMS sent successfully."))

