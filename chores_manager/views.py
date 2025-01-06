from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from .models import Chore, UserChoreSummary
from social_django.models import UserSocialAuth
from django.http import JsonResponse, HttpResponse
import json
import os

def login(request):
    return render(request, 'login.html')

def datadeletion(request):
    return render(request, "data_deletion.html")

def privacy(request):
    return render(request, 'privacy.html')

@login_required
def home(request):
    user = request.user

    print(request.user)
    print(request.user.first_name)
    print(request.user.last_name)
    print(request.user.email)
    print(request.user.is_authenticated)
    social_account = UserSocialAuth.objects.filter(user=user, provider='facebook').first()
    facebook_data = social_account.extra_data if social_account else {}

    print(UserSocialAuth.objects.all())

    # Check if the user was selected for this week
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday of this week
    end_of_week = start_of_week + timedelta(days=6)  # Sunday of this week

    selected_chores = Chore.objects.filter(
        day_of_week__in=[start_of_week.strftime('%A'), end_of_week.strftime('%A')],
    )
    selected_this_week = selected_chores.exists()

    # Fetch the user's completed chores
    user_summary = UserChoreSummary.objects.filter(user=user).first()
    completed_chores = user_summary.completed_chore_events.all() if user_summary else []

    context = {
        'facebook_data': facebook_data,
        'selected_this_week': selected_this_week,
        'completed_chores': completed_chores,
    }

    return render(request, 'home.html', context)

VERIFY_TOKEN = os.getenv("FACEBOOK_VERIFY_TOKEN")

def facebook_webhook(request):
    print(f"VERIFY_TOKEN: {VERIFY_TOKEN}")

    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        print(f"Received GET Request: mode={mode}, token={token}, challenge={challenge}")


        if mode == "subscribe" and token == VERIFY_TOKEN:
            return HttpResponse(challenge, status=200)
        return HttpResponse("Forbidden", status=403)

    elif request.method == "POST":
        payload = json.loads(request.body)
        # Handle incoming events here
        print("Incoming Webhook Event:", payload)
        return JsonResponse({"status": "EVENT_RECEIVED"}, status=200)

    return HttpResponse("Method Not Allowed", status=405)
