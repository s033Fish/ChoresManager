# Generated by Django 5.1.3 on 2024-12-25 01:40

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("chores_manager", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name="User",
            new_name="UserChoreSummary",
        ),
    ]