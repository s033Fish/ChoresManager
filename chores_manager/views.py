# Standard library imports
import os
import json
from datetime import date, timedelta

# Django imports
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

# Twilio imports
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator

# Local app imports
from .models import Chore 
from .forms import CustomUserCreationForm

TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')

def is_valid_twilio_request(request):
    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    signature = request.META.get("HTTP_X_TWILIO_SIGNATURE", "")
    url = request.build_absolute_uri()
    post_data = request.POST
    return validator.validate(url, post_data, signature)

def login_view(request):
    form = AuthenticationForm(data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('home')  # Replace 'home' with your desired URL
    return render(request, 'login.html', {'form': form})

def datadeletion(request):
    return render(request, "data_deletion.html")

def privacy(request):
    return render(request, 'privacy.html')

def terms(request):
    return render(request, 'terms.html')

def logout_view(request):
    logout(request)  # Logs the user out and clears the session
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')  # Redirect to the home page or login page

@login_required
def home(request):
    user = request.user
    print(request.user)

    # Determine the start and end of the current week
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday of this week
    end_of_week = start_of_week + timedelta(days=6)  # Sunday of this week

    # Check if the user has been assigned any chores this week
    assigned_chores = Chore.objects.filter(
        date__range=(start_of_week, end_of_week),
        completed=False,
        #user_summary__user=user
        user=user
    )
    print("assigned chores: ", assigned_chores)

    # Check if the user has completed any chores ever
    completed_chores = Chore.objects.filter(
        completed=True,
        #user_summary__user=user
        user=user
    )
    print("completed chores: ", completed_chores)

    # Check if the user is staff
    is_staff = user.is_staff

    # Prepare the context for the template
    context = {
        'assigned_chores': assigned_chores,  # Chores assigned for this week
        'completed_chores': completed_chores,  # Chores completed ever
        'is_staff': is_staff,  # Whether the user is staff
    }

    return render(request, 'home.html', context)

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Your account has been created successfully!")
            return redirect('home')  
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

def process_message(from_number, message_body):
    try:
        # Assume users reply with the chore ID to mark it as completed
        chore_id = int(message_body.strip())
        chore = Chore.objects.get(id=chore_id)

        # Verify if the chore belongs to the user
        if chore.user.profile.phone_number == from_number:
            chore.completed = True
            chore.save()
            return f"Chore {chore_id} marked as completed!"
        else:
            return "You are not assigned to this chore."
    except (ValueError, Chore.DoesNotExist):
        return "Invalid chore ID. Please check and try again."

@csrf_exempt  # Disable CSRF protection for webhook requests
def sms_reply_webhook(request):
    #if not is_valid_twilio_request(request):
    #    return HttpResponse("Invalid request.", status=403)
    if request.method == "POST":
        from_number = request.POST.get("From")
        message_body = request.POST.get("Body")

        # Process the incoming message
        response_message = process_message(from_number, message_body)

        # Send a response back
        resp = MessagingResponse()
        resp.message(response_message)

        return HttpResponse(resp.to_xml(), content_type="text/xml")
    else:
        return HttpResponse("Invalid request method.", status=405)


