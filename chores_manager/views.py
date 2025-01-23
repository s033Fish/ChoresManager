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

# Local app imports
from .models import Chore, UserChoreSummary
from .forms import CustomUserCreationForm

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
        user_summary__user=user
    )
    print("assigned chores: ", assigned_chores)

    # Check if the user has completed any chores ever
    completed_chores = Chore.objects.filter(
        completed=True,
        user_summary__user=user
    )
    print("completed chores: ", completed_chores)

    # Prepare the context for the template
    context = {
        'assigned_chores': assigned_chores,  # Chores assigned for this week
        'completed_chores': completed_chores,  # Chores completed ever
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
