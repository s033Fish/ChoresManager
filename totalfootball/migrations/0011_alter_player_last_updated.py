# Generated by Django 4.2.16 on 2024-11-19 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('totalfootball', '0010_player_new_assists_player_new_duels_player_new_goals_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='last_updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
