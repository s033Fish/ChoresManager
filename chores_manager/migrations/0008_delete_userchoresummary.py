# Generated by Django 5.1.3 on 2025-01-23 22:20

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("chores_manager", "0007_remove_chore_user_summary_chore_user"),
    ]

    operations = [
        migrations.DeleteModel(
            name="UserChoreSummary",
        ),
    ]