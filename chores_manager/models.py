from django.db import models
from django.contrib.auth.models import User

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

    def __str__(self):
        return f"{self.chore.name} on {self.day_of_week} ({self.meal_time})"

class User(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chore_summary')
    completed_chore_events = models.ManyToManyField(Chore, related_name='completed_by_users', blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.completed_chore_events.count()} chores completed"