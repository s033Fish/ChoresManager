import sqlite3
from datetime import date, datetime, timedelta
from twilio.rest import Client
from dotenv import load_dotenv
from pathlib import Path
import os

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Twilio credentials
account_sid = os.getenv('ACCOUNT_SID')
auth_token = os.getenv('AUTH_TOKEN')
twilio_phone_number = "+18788797709"  # Replace with your Twilio phone number

# Register adapters for date and datetime
sqlite3.register_adapter(date, lambda d: d.isoformat())
sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())

# Register converters for date and datetime
sqlite3.register_converter("DATE", lambda v: date.fromisoformat(v.decode("utf-8")))
sqlite3.register_converter("DATETIME", lambda v: datetime.fromisoformat(v.decode("utf-8")))

# Database path
DB_PATH = BASE_DIR / "db.sqlite3"

def send_sms(phone_number, message):
    """
    Send an SMS message using Twilio.
    """
    client = Client(account_sid, auth_token)

    try:
        # Send a message
        message = client.messages.create(
            body=message,               # Message content
            from_=twilio_phone_number,  # Your Twilio number
            to=phone_number             # Recipient's phone number
        )
        print(f"Message SID: {message.sid}")
    except Exception as e:
        print(f"Error sending SMS message: {e}")

def get_user_chores():
    """
    Fetch chores grouped by user for the current day and the upcoming meal.
    Returns a dictionary mapping user information to their uncompleted chores.
    """
    # Determine today's date and current time
    today = date.today()
    now = datetime.now()

    # Determine the upcoming meal based on the current time
    if now.hour < 12:
        meal_time = "breakfast"
    elif now.hour < 17:
        meal_time = "lunch"
    else:
        meal_time = "dinner"

    # Connect to the SQLite database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Query for uncompleted chores for the upcoming meal
    query = """
        SELECT u.id AS user_id, u.first_name, u.last_name, p.phone_number, 
               c.day_of_week, c.meal_time, c.date
        FROM chores_manager_chore AS c
        LEFT JOIN auth_user AS u ON c.user_id = u.id
        LEFT JOIN chores_manager_profile AS p ON u.id = p.user_id
        WHERE c.completed = 0
          AND c.date = ?
          AND c.meal_time = ?
          AND u.id IS NOT NULL
          AND p.phone_number IS NOT NULL
        ORDER BY u.id, c.date, c.day_of_week, c.meal_time;
    """
    cursor.execute(query, (today, meal_time))
    rows = cursor.fetchall()
    conn.close()

    # Group chores by user
    user_chores = {}
    for user_id, first_name, last_name, phone_number, day_of_week, meal_time, chore_date in rows:
        user_key = (user_id, first_name, last_name, phone_number)
        if user_key not in user_chores:
            user_chores[user_key] = []
        user_chores[user_key].append((day_of_week, meal_time, chore_date))

    return user_chores

def send_reminders():
    """
    Fetch users with uncompleted chores and send SMS reminders.
    """
    if not account_sid or not auth_token:
        print("Twilio credentials are missing. Check your .env file.")
        return

    # Get uncompleted chores grouped by user
    user_chores = get_user_chores()

    if not user_chores:
        print("No uncompleted chores found for the upcoming meal.")
        return

    # List to store details of users reminders were sent to
    users_contacted = []

    # Send SMS reminders
    for (user_id, first_name, last_name, phone_number), chores in user_chores.items():
        # Build the list of chores
        chore_list = "\n".join([f"- {day_of_week} ({chore_date}) - {meal_time}" for day_of_week, meal_time, chore_date in chores])

        # Compose the SMS message
        message = (
            f"Hi {first_name}, here are your pending chores for the upcoming meal:\n"
            f"{chore_list}\n"
            "Please complete them as soon as possible. Thank you!"
        )
        send_sms(phone_number, message)
        users_contacted.append(f"{first_name} {last_name} ({phone_number})")
        print(f"Sent reminder to {first_name} {last_name} at {phone_number}.")

    print("All reminders have been sent successfully.")
    print("Users contacted:")
    print("\n".join(users_contacted))

if __name__ == "__main__":
    send_reminders()

