from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from .models import Chore, UserChoreSummary
from allauth.socialaccount.models import SocialAccount

def login(request):
    return render(request, 'login.html')

def datadeletion(request):
    return render(request, "data_deletion.html")

def privacy(request):
    return render(request, 'privacy.html')

@login_required
def home(request):
    user = request.user

    social_account = SocialAccount.objects.filter(user=user, provider='facebook').first()
    facebook_data = social_account.extra_data if social_account else {}

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
