# Standard library imports
import os
import json 
import sqlite3
import random
from datetime import date, timedelta

# Django imports
from datetime import date, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render, redirect

# Twilio imports
from twilio.rest import Client

# Local app imports
from .models import Chore, Profile

# Twilio credentials (ensure these are set in your environment or settings)
from django.conf import settings
TWILIO_ACCOUNT_SID = settings.TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN = settings.TWILIO_AUTH_TOKEN
TWILIO_PHONE_NUMBER = "+18788797709"



DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
MEAL_TIMES = ['Breakfast', 'Lunch', 'Dinner']

# Check if the user is staff
def staff_required(view_func):
    return user_passes_test(lambda u: u.is_staff)(view_func)


@login_required
@staff_member_required
def admin_panel(request):
    user = request.user

    # Determine the start and end of the current week
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday of this week
    end_of_week = start_of_week + timedelta(days=6)  # Sunday of this week

    # Fetch chores for the current week
    chores = Chore.objects.filter(date__range=(start_of_week, end_of_week)).select_related('user').order_by('date', 'meal_time')

    # Check if the user is staff
    is_staff = user.is_staff

    # Prepare the context for the template
    context = {
        'is_staff': is_staff,  # Whether the user is staff
        'chores': chores,  # Chores for the week
    }

    return render(request, 'admin.html', context)

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

@csrf_exempt
@staff_member_required
def send_sms_reminders(request):
    """
    Form message by retreiving uncompleted chores.
    """
    if request.method == 'POST':
        try:
            # Determine the current week's date range
            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)

            # Query for uncompleted chores grouped by user
            chores = (
                Chore.objects.filter(
                    completed=False,
                    date__range=(start_of_week, end_of_week),
                    user__isnull=False,
                )
                .select_related("user__profile")
                .order_by("user__id", "date", "day_of_week", "meal_time")
            )

            # Group chores by user
            user_chores = {}
            for chore in chores:
                user = chore.user
                profile = user.profile
                if profile.phone_number:  # Only include users with phone numbers
                    user_key = (user.id, user.first_name, user.last_name, profile.phone_number)
                    if user_key not in user_chores:
                        user_chores[user_key] = []
                    user_chores[user_key].append((chore.day_of_week, chore.meal_time, chore.date))

            if not user_chores:
                return JsonResponse({'message': 'No uncompleted chores found for this week.'}, status=404)

            # Send SMS reminders
            sms_count = 0
            for (user_id, first_name, last_name, phone_number), chores in user_chores.items():
                # Build the list of chores
                chore_list = "\n".join(
                    [f"- {day_of_week} ({chore_date}) - {meal_time}" for day_of_week, meal_time, chore_date in chores]
                )

                # Compose the SMS message
                message = (
                    f"Hi {first_name}, here are your pending chores for this week:\n"
                    f"{chore_list}\n"
                    "Please complete them as soon as possible. Thank you!"
                )
                print("message: ", message)

                send_sms(phone_number, message)
                print(f"Sent reminder to {first_name} {last_name} at {phone_number}.")
                sms_count += 1

            return JsonResponse({'message': f'{sms_count} reminders have been sent successfully.'}, status=200)

        except Exception as e:
            return JsonResponse({'error': f'Error sending SMS reminders: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)

def get_week_dates(requested_date=None):
    if requested_date:
        try:
            requested_date = date.fromisoformat(requested_date)
            if requested_date.weekday() != 0:
                return None, None, "The provided date is not a Monday."
        except ValueError:
            return None, None, "Invalid date format. Please use YYYY-MM-DD."
    else:
        requested_date = date.today() - timedelta(days=date.today().weekday())

    start_of_week = requested_date
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week, None

@csrf_exempt
@staff_member_required
def add_chores(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(f"Received data: {data}")
            date = data.get('date')
            day_of_week = data.get('day_of_week')
            meal_time = data.get('meal_time')

            if not (date and day_of_week and meal_time):
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            # Connect to the SQLite database
            conn = sqlite3.connect(settings.DATABASES['default']['NAME'])
            cursor = conn.cursor()

            # Insert the chore into the database
            query = """
                INSERT INTO chores_manager_chore (date, day_of_week, meal_time, completed)
                VALUES (?, ?, ?, 0)
            """
            cursor.execute(query, (date, day_of_week, meal_time))
            conn.commit()

            # Close the connection
            cursor.close()
            conn.close()

            return JsonResponse({'message': 'Chore added successfully!'}, status=200)

        except Exception as e:
            print(f"Error adding chore: {e}")
            return JsonResponse({'error': 'An error occurred while adding the chore'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def get_users(cursor):
    # Connect to the SQLite database
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    print("Getting eligible users.")

    query = """
        SELECT id, first_name, last_name
        FROM auth_user;
    """
    cursor.execute(query)
    eligible_users = cursor.fetchall()
    print(eligible_users);

    cursor.close()
    conn.close()

    return eligible_users


@csrf_exempt
@staff_member_required
def assign_chores(request):
    if request.method == 'POST':
        try:
            # Determine the start and end of the week (default to the current week)
            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())  # Monday of this week
            end_of_week = start_of_week + timedelta(days=6)  # Sunday of this week

            print("Start of week:", start_of_week)
            print("End of week:", end_of_week)

            # Fetch unassigned chores for the week
            unassigned_chores = Chore.objects.filter(
                user__isnull=True,
               # date__range=(start_of_week, end_of_week) #not currently used...query selects all dates
            )

            print("Unassigned chores count:", unassigned_chores.count())

            #if not unassigned_chores.exists():
            #    return JsonResponse({'message': 'No unassigned chores found for the selected week.'}, status=404)

            if unassigned_chores.count() == 0:
                # No chores to assign, return a success response
                return JsonResponse({
                    'message': 'No unassigned chores found for the selected week.',
                    'assigned_chore_count': 0,
                    'unassigned_chore_count': 0,
                    'eligible_user_count': 0
                }, status=200)

            # Fetch all users excluding those who have completed more than X chores
            from django.contrib.auth import get_user_model
            User = get_user_model()
            #users = list(User.objects.all())  #use this to get all users
            MAX_COMPLETED_CHORES = 3  # Set the threshold for completed chores
            users = User.objects.annotate(
            completed_chore_count=Count('chore', filter=Q(chore__completed=True))
            ).filter(completed_chore_count__lte=MAX_COMPLETED_CHORES)

            print("Eligible users count:", len(users))

            if not users:
                return JsonResponse({'message': 'No eligible users available to assign chores.'}, status=404)

            # Randomly assign users to unassigned chores
            assigned_chore_count = 0
            for chore in unassigned_chores:
                assigned_user = random.choice(users)  # Randomly pick a user
                print(f"Assigning chore {chore.id} to user {assigned_user.id}")
                chore.user = assigned_user
                chore.save()
                assigned_chore_count += 1

            return JsonResponse({
                'message': f'All unassigned chores have been successfully assigned. {assigned_chore_count} chores were assigned to {len(users)} eligible users.'
            }, status=200)

        except Exception as e:
            return JsonResponse({'error': f'Error assigning chores: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)
