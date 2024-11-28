import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from datetime import timedelta

# User Model
class User(AbstractUser):
    email = models.EmailField(unique=True)
    team_name = models.CharField(max_length=100, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    leagues = models.ManyToManyField('League', related_name='members', blank=True)

    def __str__(self):
        return self.username


# Player Model
class Player(models.Model):
    name = models.CharField(max_length=100)
    team = models.CharField(max_length=100)
    league = models.CharField(max_length=100)
    position = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    points = models.IntegerField(default=0)
    past_points = models.IntegerField(default=0)

    # Additional statistics
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    tackles = models.IntegerField(default=0)
    saves = models.IntegerField(default=0)
    duels = models.IntegerField(default=0)

    new_goals = models.IntegerField(default=0)
    new_assists = models.IntegerField(default=0)
    new_tackles = models.IntegerField(default=0)
    new_saves = models.IntegerField(default=0)
    new_duels = models.IntegerField(default=0)

    # for AJAX purposes
    last_updated = models.DateTimeField(null=True, blank=True)

    # API-Football Specific Fields -> helps us obtain live player stats more easily
    api_football_id = models.IntegerField(unique=True, null=True, blank=True)
    team_api_id = models.IntegerField(null=True, blank=True)
    league_api_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.team})"


# League Model
class League(models.Model):
    name = models.CharField(max_length=100)
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_leagues', null=True, blank=True)
    draft_room_members = models.ManyToManyField(User, related_name='draft_rooms', blank=True)
    draft_started = models.BooleanField(default=False)
    draft_direction = models.BooleanField(default=True)
    draft_round = models.IntegerField(default=1)
    current_pick = models.IntegerField(default=1)
    total_picks = models.IntegerField(default=15)
    round_number = models.IntegerField(default=1)  # Tracks the current round in the draft
    direction = models.BooleanField(default=True)  # True for forward, False for reverse

    def next_pick(self):
        total_teams = self.league_teams.count()
        if self.draft_round > 11:
            self.draft_started = False
            return

        if self.draft_direction:
            self.current_pick += 1
            if self.current_pick > total_teams:
                self.draft_direction = False
                self.current_pick = total_teams
                self.draft_round += 1
        else:
            self.current_pick -= 1
            if self.current_pick < 1:
                self.draft_direction = True
                self.current_pick = 1
                self.draft_round += 1

    def __str__(self):
        return f"{self.name} (Draft)"


class Team(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='team')
    players = models.ManyToManyField(Player, related_name='teams')
    captain = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='captain_teams')
    starting_lineup = models.ManyToManyField(Player, related_name='starting_lineups', blank=True)

    @property
    def calculated_points(self):
        captain_points = self.captain.points * 2 if self.captain else 0
        other_points = self.players.exclude(id=self.captain.id).aggregate(total=Sum('points'))['total'] or 0
        return captain_points + other_points

    def clean(self):
        if not self.players.exists():
            raise ValidationError("A team must have at least one player.")

    def __str__(self):
        return f"{self.user.username}'s Team"



# League Team Model
class LeagueTeam(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='league_teams')
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='league_teams')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    players = models.ManyToManyField(Player, related_name='league_teams')
    captain = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='league_team_captain')
    starting_lineup = models.ManyToManyField(Player, related_name='league_team_starting_lineup', blank=True)

    def add_player(self, player):
        if self.players.filter(id=player.id).exists():
            raise ValueError("Player already selected by another team.")
        self.players.add(player)

    @property
    def calculated_points(self):
        # Points from the captain are doubled
        captain_points = (self.captain.past_points or 0) * 2 if self.captain else 0
        # Points from other players
        other_players_points = self.players.exclude(id=self.captain_id).aggregate(
            total_points=Sum('past_points')
        )['total_points'] or 0
        return captain_points + other_players_points

    def __str__(self):
        return f"{self.user.username}'s Team in {self.league.name}"

# DraftPick Model
class DraftPick(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='draft_picks')
    team = models.ForeignKey(LeagueTeam, on_delete=models.CASCADE, related_name='draft_picks')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='draft_picks')
    pick_number = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['league', 'player'], name='unique_draft_pick_per_league')
        ]

    def __str__(self):
        return f"Pick {self.pick_number}: {self.player.name} by {self.team.user.username}"


# Match Model
class Match(models.Model):
    team_1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    team_2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    score = models.CharField(max_length=20, blank=True, null=True)
    date = models.DateField()

    def __str__(self):
        return f"{self.team_1} vs {self.team_2} on {self.date}"
