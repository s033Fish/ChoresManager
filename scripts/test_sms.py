import sys, os
from twilio.rest import Client
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Twilio credentials
account_sid = os.getenv('ACCOUNT_SID')
auth_token = os.getenv('AUTH_TOKEN')


def send_sns_message(phone_number, message):
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



def main():
    print("Messaging Script")
    print("====================")
    print(account_sid)
    
    phone_number = input("Enter the recipient phone number (e.g., +1234567890): ")
    message = input("Enter your message: ")

    send_sns_message(phone_number, message)
    


if __name__ == "__main__":
    main()

