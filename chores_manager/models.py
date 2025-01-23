from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    opt_in_sms = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class UserChoreSummary(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)

    def __str__(self):
        return f"Summary for {self.user.username}"


class Chore(models.Model):
    WEEKDAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
    ]

    MEAL_CHOICES = [
        ('Lunch', 'Lunch'),
        ('Dinner', 'Dinner'),
    ]

    day_of_week = models.CharField(max_length=10, choices=WEEKDAY_CHOICES)
    meal_time = models.CharField(max_length=6, choices=MEAL_CHOICES)
    completed = models.BooleanField(default=False)
    date = models.DateField(null=True, blank=True)

    # Add the foreign key to UserChoreSummary
    user_summary = models.ForeignKey(
        UserChoreSummary,
        on_delete=models.SET_NULL,
        related_name="chores",
        null=True,  # Allow the field to be null
        blank=True  # Allow blank values in forms
    )

    def __str__(self):
        return f"{self.day_of_week} - {self.meal_time} - {self.date if self.date else 'No Date'}"
