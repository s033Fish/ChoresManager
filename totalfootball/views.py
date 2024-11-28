from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import Http404, HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Sum
from django.utils.timezone import now
import logging
from math import log
logger = logging.getLogger(__name__)

import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import User, Player, Team, League, LeagueTeam, DraftPick
from django.contrib.auth.decorators import login_required
from .forms import LoginForm, RegisterForm, ProfileForm, JoinLeagueForm, CreateLeagueForm

import requests

API_URL = "https://api-football-v1.p.rapidapi.com/v3"
API_KEY = "9f340e84c7msh3a8fcf6665f37f2p134bc1jsn68c53749acd7"

HEADERS = {
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
    "x-rapidapi-key": API_KEY,
}

# Returns all valid player IDs in the database in JSON format
@login_required
def get_all_player_ids(request):
    player_ids = list(Player.objects.values_list('api_football_id', flat=True))
    return JsonResponse({"player_ids": player_ids})


def homepage_action(request):
    # Displays the top ten overall players on the home page
    top_players = Player.objects.order_by('-past_points')[:10]

    # Displays each team and their points
    teams = Team.objects.all()
    team_points = []

    for team in teams:
        print(team.starting_lineup.all())
        captain_points = 0
        non_captain_points = 0
        
        if team.captain:
            captain_points = (team.captain.points or 0) * 2
        
        non_captain_points = team.starting_lineup.exclude(id=team.captain_id).aggregate(
            total=Sum('past_points')
        )['total'] or 0

        total_points = captain_points + non_captain_points

        team_points.append({
            'username': team.user.username,
            'total_points': total_points,
        })

    # Sorts the league teams by their total points scored
    top_users = sorted(team_points, key=lambda x: x['total_points'], reverse=True)[:10]

    context = {
        'top_players': top_players,
        'top_users': top_users,
    }

    return render(request, 'homepage.html', context)

# Login page for the user
def login_action(request):
    if request.user.is_authenticated:
        return redirect('homepage')

    context = {}

    if request.method == 'GET':
        context['form'] = LoginForm()
        return render(request, 'start.html', context)

    form = LoginForm(request.POST)
    context['form'] = form

    if not form.is_valid():
        return render(request, 'start.html', context)

    username = form.cleaned_data['username']
    password = form.cleaned_data['password']
    new_user = authenticate(username=username, password=password)

    if new_user is None:
        messages.error(request, "Invalid username or password.")
        return render(request, 'start.html', context)

    login(request, new_user)
    return redirect('homepage')

# User can register if they are not already logged in
def register_action(request):
    context = {}

    if request.method == 'GET':
        context['form'] = RegisterForm()
        print("Returning form")
        return render(request, 'register.html', context)

    form = RegisterForm(request.POST)
    context['form'] = form

    if not form.is_valid():
        return render(request, 'register.html', context)
    
    if form.cleaned_data['password1'] != form.cleaned_data['password2']:
        context['error'] = 'Passwords do not match.'
        print("Password error")
        return render(request, 'register.html', context)

    new_user = User.objects.create_user(username=form.cleaned_data['username'], 
                                        password=form.cleaned_data['password1'],
                                        email=form.cleaned_data['email'],
                                        first_name=form.cleaned_data['first_name'],
                                        last_name=form.cleaned_data['last_name'])
    new_user.is_active = True
    new_user.save()
    
    new_user = authenticate(username=form.cleaned_data['username'],
                            password=form.cleaned_data['password1'])

    if new_user:
        login(request, new_user)
        print("Finished logging in, trying to go to global stream")
        return redirect(reverse('homepage'))
    else:
        print("Authentication failed.")
        return render(request, 'register.html', {'form': form, 'error': 'Authentication failed.'})

# Enables the user to log out when necessary
def logout_action(request):
    logout(request)
    
    return redirect('login')

# Profile page actions
def profile_action(request, user_id):
    user = get_object_or_404(User, id=user_id)
    context = {}

    context['other'] = user_id != request.user.id

    if not context['other']:
        print("User is viewing their own profile")

        if request.method == "GET":
            form = ProfileForm(initial={
                'team_name': request.user.team_name,
                'profile_image': request.user.profile_image
            })
            context['form'] = form
            return render(request, 'profile.html', context)

        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            request.user.team_name = form.cleaned_data['team_name']
            if 'profile_image' in request.FILES:
                request.user.profile_image = form.cleaned_data['profile_image']
            request.user.save()

            return redirect('profile', user_id=request.user.id)
        else:
            context['form'] = form
            return render(request, 'profile.html', context)

    else:
        context['form'] = None
        context['otherUser'] = user

    return render(request, "profile.html", context)

# Enables users to upload their profile picture
@login_required
def get_profile_picture(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if not user.profile_image:
        raise Http404("No profile image found for this user.")

    try:
        with open(user.profile_image.path, 'rb') as f:
            image_data = f.read()
    except FileNotFoundError:
        raise Http404("Profile image file not found.")

    return HttpResponse(image_data, content_type='image/jpeg')

# Enables updates using the API
def update_player_stats(request, player_id):
    if request.method == "POST":
        try:
            # Fetch stats from the external API by calling the helper method defined above
            result = fetch_player_stats(player_id)

            if result["success"]:
                # Retrieve the updated player object
                player = Player.objects.get(api_football_id=player_id)
                
                # Create a dictionary of updated player stats
                updated_stats = {
                    "name": player.name,
                    "position": player.position,
                    "goals": player.goals,
                    "assists": player.assists,
                    "tackles": player.tackles,
                    "saves": player.saves,
                    "duels": player.duels,
                    "points": player.points,
                    "last_updated": player.last_updated.strftime('%Y-%m-%d %H:%M:%S') if player.last_updated else None,
                }

                return JsonResponse({
                    "success": True,
                    "message": f"Player {player_id} updated successfully.",
                    "updated_stats": updated_stats
                })

            else:
                return JsonResponse({"success": False, "error": result["error"]}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method."}, status=405)

@login_required
def draft_view(request, league_id):
    league = get_object_or_404(League, id=league_id)

    if not league.draft_started:
        league.draft_started = True
        league.save()

    # The following information enables us to simulate a snake draft to choose players. 

    # Total teams in the league
    total_teams = league.league_teams.count()

    if league.current_pick > (total_teams * 15):
        league.draft_started = False
        league.save()
        return redirect('league_details', league_id=league.id)

    # Calculate the current round number
    round_number = (league.current_pick - 1) // total_teams + 1

    # Determine the direction based on the round number
    direction = 'id' if round_number % 2 == 1 else '-id'
    teams = league.league_teams.order_by(direction)

    # Handle draft pick submission
    if request.method == 'POST':
        player_id = request.POST.get('player_id')
        player = get_object_or_404(Player, id=player_id)

        # Check if player is already picked
        if DraftPick.objects.filter(league=league, player=player).exists():
            messages.error(request, 'Player already drafted.')
        else:
            # Record the draft pick
            current_team_index = (league.current_pick - 1) % total_teams
            current_team = teams[current_team_index]
            DraftPick.objects.create(
                league=league,
                team=current_team,
                player=player,
                pick_number=league.current_pick
            )
            current_team.players.add(player)

            # Advance the draft
            league.current_pick += 1
            
            # We end the snake draft once teams have selected their 15 players
            if league.current_pick > (total_teams * 15):
                league.draft_started = False
                league.save()
                return redirect('league_details', league_id=league.id)
            league.save()

    # Recalculate the team that should be drafting
    if league.current_pick <= league.total_picks:
        round_number = (league.current_pick - 1) // total_teams + 1
        direction = 'id' if round_number % 2 == 1 else '-id'
        teams = league.league_teams.order_by(direction)
        current_team_index = (league.current_pick - 1) % total_teams
        current_team = teams[current_team_index]
    else:
        current_team = None  

    # Get available players (not yet drafted)
    drafted_players = DraftPick.objects.filter(league=league).values_list('player_id', flat=True)
    available_players = Player.objects.exclude(id__in=drafted_players)

    # Categorize and sort players by position and points to display (this gives users an idea of who to draft)
    players_by_position = {
        "Goalkeepers": available_players.filter(position="Goalkeeper").order_by('-past_points'),
        "Defenders": available_players.filter(position="Defender").order_by('-past_points'),
        "Midfielders": available_players.filter(position="Midfielder").order_by('-past_points'),
        "Attackers": available_players.filter(position="Attacker").order_by('-past_points'),
    }

    for position, players in players_by_position.items():
        for player in players:
            player.team_picture_url = f"img/{player.team.lower().replace(' ', '_')}.png"

    context = {
        'league': league,
        'current_team': current_team,
        'players_by_position': players_by_position,
        'drafted_players': DraftPick.objects.filter(league=league).order_by('pick_number'),
    }

    return render(request, 'draft.html', context)

# Calculates the fantasy points for each player using their stats
def calculate_points(goals, assists, saves, tackles, duels, position):
    new_score = 0
    if position == "Goalkeeper":
        new_score += saves*0.5 + tackles*0.25 + duels*0.25
    elif position == "Defender":
        new_score += saves*0.15 + duels*0.3 + tackles*0.25 + goals*6 + assists*4
    elif position == "Midfielder":
        new_score += assists*4 + goals*5 + tackles*0.2 + duels*0.2
    elif position == "Attacker":
        new_score += assists*3 + goals*4 + tackles*0.15 + duels*0.1
    
    return new_score

# Fetch live stats for a player by their API ID and update the database if 6 hours have passed since the last update.

def calculate_player_price(player):
    base_price = {
        'Goalkeeper': 50,
        'Defender': 60,
        'Midfielder': 80,
        'Attacker': 100
    }.get(player.position, 50)

    performance_factor = log(player.past_points + 1) * 10

    form_factor = (player.new_goals * 2 + player.new_assists * 1.5 +
                   player.new_saves * 0.5 + player.new_tackles * 0.3 + player.new_duels * 0.2)

    price = base_price + performance_factor + form_factor

    minimum_price = 50
    return round(max(price, minimum_price), 2)

def fetch_player_stats(player_id):    
    # logger.info(f"[{now()}] Sending request for player {player_id}")

    url = f"{API_URL}/players"
    params = {"id": player_id, "season": "2024"}  # Update the season dynamically as needed

    try:
        response = requests.get(url, headers=HEADERS, params=params)

        if response.status_code == 200:
            data = response.json()
            # logger.info(f"[{now()}] Successfully fetched stats for player {player_id}. Response: {data}")

            player = Player.objects.get(api_football_id=player_id)

            stats = data['response'][0]['statistics'][0]
            player.goals = stats.get("goals", {}).get("total", 0) or 0
            player.assists = stats.get("goals", {}).get("assists", 0) or 0
            player.saves = stats.get("goals", {}).get("saves", 0) or 0
            player.tackles = stats.get("tackles", {}).get("total", 0) or 0
            player.duels = stats.get("duels", {}).get("won", 0) or 0
            player.price = calculate_player_price(player)

            player.past_points = calculate_points(player.goals, player.assists, player.saves, player.tackles, player.duels, player.position)
            player.last_updated = now()

            player.save()

            return {"success": True, "message": f"Stats fetched for player {player_id}"}
        else:
            # logger.warning(f"[{now()}] Failed to fetch stats for player {player_id}. Status: {response.status_code}")
            return {"success": False, "error": f"API request failed with status code {response.status_code}"}
    except Exception as e:
        # logger.error(f"[{now()}] Error fetching stats for player {player_id}: {str(e)}")
        return {"success": False, "error": "An unexpected error occurred."}

# This function allows users to set their lineups after drafting
def select_lineup(request):
    print("Here is the request", request)
    
    # Fetch or create a Team object for the user and league
    league = League.objects.first()
    if not league:
        return HttpResponse("No league available", status=400)

    # Ensure to use the new Team model
    team, created = Team.objects.get_or_create(user=request.user)

    # Filter players by those assigned to the user's team
    drafted_players = Player.objects.all()
    print("Drafted Players for the team:", list(drafted_players.values()))

    # Group players by position for better organization in the template
    players_by_position = {
        'Goalkeepers': drafted_players.filter(position='Goalkeeper').order_by('name'),
        'Defenders': drafted_players.filter(position='Defender').order_by('name'),
        'Midfielders': drafted_players.filter(position='Midfielder').order_by('name'),
        'Forwards': drafted_players.filter(position='Forward').order_by('name'),
    }

    if request.method == "POST":
        # Check if the request is JSON or a regular POST
        if request.content_type == "application/json":
            data = json.loads(request.body)
            player_ids = data.get('players')
            captain_id = data.get('captain_id')
            print("IDs", player_ids)
            print("Captain ID", captain_id)
        else:
            player_ids = request.POST.getlist('players')
            captain_id = request.POST.get('captain')

        if not player_ids or not captain_id:
            if request.content_type == "application/json":
                return JsonResponse({'error': "You must select players and a captain."}, status=400)
            else:
                messages.error(request, "You must select players and a captain.")
                return redirect('select_lineup')

        # Fetch all drafted players based on provided IDs
        players_selected = drafted_players.filter(id__in=player_ids)
        captain = drafted_players.filter(id=captain_id).first()

        print("Players Selected:", list(players_selected.values()))
        print("Captain Selected:", captain)

        if len(players_selected) != 11:
            if request.content_type == "application/json":
                return JsonResponse({'error': "You must select exactly 11 players."}, status=400)
            else:
                messages.error(request, "You must select exactly 11 players.")
                return redirect('select_lineup')

        if not captain or captain not in players_selected:
            if request.content_type == "application/json":
                return JsonResponse({'error': "The captain must be one of the selected players."}, status=400)
            else:
                messages.error(request, "The captain must be one of the selected players.")
                return redirect('select_lineup')

        # Save the selected lineup and captain
        team.starting_lineup.set(players_selected)
        team.captain = captain
        team.save()

        if request.content_type == "application/json":
            return JsonResponse({'message': "Your lineup has been saved successfully!"})
        else:
            messages.success(request, "Your lineup has been saved successfully!")
            return redirect('homepage')

    # If the request is not POST, render the select lineup page
    context = {
        'players_by_position': players_by_position,
    }
    return render(request, 'select_lineup.html', context)

# Enables us to check points player has amassed over the course of the season
def fetch_past_player_points(player_id):
    player = Player.objects.get(api_football_id=player_id)
    return player.past_points

# Enables the user to view their team
@login_required
def my_team_view(request):
    try:
        # Retrieve the user's team and its players
        team = Team.objects.get(user=request.user)
        players = team.starting_lineup.all()  # Retrieve all players in the lineup
        captain = team.captain

        # Calculate total points including captain's bonus
        captain_points = (captain.past_points or 0) * 2 if captain else 0
        non_captain_points = sum(player.past_points for player in players if player != captain)
        total_points = captain_points + non_captain_points

        # Print debugging information for sanity checking
        # print("My Team:")
        # for player in players:
        #     player.past_points = calculate_points(player.goals, player.assists, player.saves, player.tackles, player.duels, player.position)
        #     print(f"Player: {player.name}, Position: {player.position}, Points: {player.points}, Past Points: {player.past_points}")

    except Team.DoesNotExist:
        # Handle case where the user does not have a team
        messages.error(request, "You haven't selected a team yet.")
        return redirect('select_lineup')

    context = {
        'team': team,
        'players': players,
        'captain': captain,
        'total_points': total_points,
    }

    return render(request, 'my_team.html', context)

# Enables the user to create their league
@login_required
def create_league(request):
    if request.method == 'POST':
        form = CreateLeagueForm(request.POST)
        if form.is_valid():
            league = form.save(commit=False)
            league.creator = request.user
            league.save()
            
            league.members.add(request.user)
            
            LeagueTeam.objects.create(user=request.user, league=league)
            
            return redirect('league_details', league_id=league.id)
    else:
        form = CreateLeagueForm()
    return render(request, 'create_league.html', {'form': form})

# User can join a league if they have the unique code
@login_required
def join_league(request):
    if request.method == 'POST':
        form = JoinLeagueForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                league = League.objects.get(code=code)
                
                if request.user not in league.members.all():
                    league.members.add(request.user)
                
                league_team, created = LeagueTeam.objects.get_or_create(user=request.user, league=league)
                
                return redirect('league_details', league_id=league.id)
                
            except League.DoesNotExist:
                form.add_error('code', 'Invalid league code.')
    else:
        form = JoinLeagueForm()
    return render(request, 'join_league.html', {'form': form})

# Provides a little league detail update
@login_required
def league_details(request, league_id):
    league = get_object_or_404(League, id=league_id)
    
    league_teams = league.league_teams.all()
    teams_with_players = league_teams.filter(players__isnull=False).distinct()
    show_members_for_draft = not teams_with_players.exists()

    user_team = league_teams.filter(user=request.user).first()
    drafted_players = user_team.players.all() if user_team else []

    return render(request, 'league_details.html', {
        'league': league,
        'league_teams': league_teams,
        'show_members_for_draft': show_members_for_draft,
        'drafted_players': drafted_players,
    })
    

# Endpoint for react app
def get_players(request):
    players = Player.objects.all().values('id', 'name', 'team', 'position', 'points', 'price', 'past_points')
    return JsonResponse({'players': list(players)})

@login_required
def get_selected_players(request):
    try:
        team = Team.objects.get(user=request.user)
        players = team.starting_lineup.all() 
        captain = team.captain

        selected_players = {f"player_{idx}": {
            "id": player.id,
            "name": player.name,
            "team": player.team,
            "position": player.position,
            "price": player.price
        } for idx, player in enumerate(players)}

        response_data = {
            "selectedPlayers": selected_players,
            "captain": {
                "id": captain.id,
                "name": captain.name,
                "team": captain.team,
                "position": captain.position
            } if captain else None
        }
        return JsonResponse(response_data)
    except Team.DoesNotExist:
        return JsonResponse({"selectedPlayers": {}, "captain": None})
    
@login_required
def select_player(request):
    if request.method == 'POST':
        try:
            # Handle JSON payload if the request contains JSON data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                league_id = data.get('league_id')
                player_id = data.get('player_id')
            else:
                league_id = request.POST.get('league_id')
                player_id = request.POST.get('player_id')

            # Validate incoming data
            if not league_id or not player_id:
                return JsonResponse({'success': False, 'error_message': 'League ID and Player ID are required.'}, status=400)

            # Get league and user
            league = get_object_or_404(League, id=league_id)
            user = request.user

            # Get list of all league teams in draft order
            teams = list(league.league_teams.order_by('id'))
            if not league.draft_direction:
                teams.reverse()  # Reverse the order for the backward round

            # Validate current pick index
            current_team_index = league.current_pick - 1
            if current_team_index < 0 or current_team_index >= len(teams):
                return JsonResponse({'success': False, 'error_message': 'Invalid current pick index.'}, status=400)

            current_team = teams[current_team_index]

            # Ensure it's the user's turn
            if current_team.user != user:
                return JsonResponse({'success': False, 'error_message': 'It is not your turn.'}, status=403)

            # Get the player and check if they are already drafted
            player = get_object_or_404(Player, id=player_id)
            if DraftPick.objects.filter(league=league, player=player).exists():
                return JsonResponse({'success': False, 'error_message': 'Player already drafted.'}, status=400)

            # Record the draft pick
            DraftPick.objects.create(
                league=league,
                team=current_team,
                player=player,
                pick_number=league.current_pick
            )
            current_team.players.add(player)

            # Update the draft state to the next pick
            league.next_pick()  # Make sure this method works as expected
            league.save()

            return JsonResponse({
                'success': True,
                'user_name': user.username,
                'player_name': player.name,
                'pick_number': league.current_pick
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error_message': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            logger.error(f"Error selecting player: {str(e)}")
            return JsonResponse({'success': False, 'error_message': 'An unexpected error occurred.'}, status=500)

    return JsonResponse({'success': False, 'error_message': 'Invalid request method.'}, status=400)

@login_required
def get_draft_state(request):
    league_id = request.GET.get('league_id')
    league = get_object_or_404(League, id=league_id)
    
    # Find the current pick user
    current_team_index = league.current_pick - 1
    teams = list(league.league_teams.order_by('id'))
    if not league.draft_direction:
        teams.reverse()  # Reverse for backwards rounds

    current_team = teams[current_team_index]
    
    response_data = {
        'current_pick': league.current_pick,
        'draft_round': league.draft_round,
        'current_turn_user_id': current_team.user.id,  # Make sure this is included
        'current_turn_user_name': current_team.user.username,
    }
    return JsonResponse(response_data)
    
@login_required
def get_league_members(request):
    league_id = request.GET.get('league_id')
    league = get_object_or_404(League, pk=league_id)

    members = league.members.all()
    members_list = [{'username': member.username} for member in members]

    # Determine if the draft can be started
    teams_with_players = league.league_teams.filter(players__isnull=False).distinct()
    show_members_for_draft = not teams_with_players.exists()

    return JsonResponse({
        'members': members_list,
        'show_members_for_draft': show_members_for_draft,
    })

@login_required
def join_draft_room(request):
    if request.method == 'POST':
        league_id = request.POST.get('league_id')
        user = request.user
        league = get_object_or_404(League, id=league_id)

        if not league.draft_started:
            if user not in league.draft_room_members.all():
                league.draft_room_members.add(user)
                league.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error_message': 'User already in draft room.'})
        else:
            return JsonResponse({'success': False, 'error_message': 'Draft has already started.'})

    return JsonResponse({'success': False, 'error_message': 'Invalid request method.'}, status=400)

@login_required
def get_draft_room_status(request):
    league_id = request.GET.get('league_id')
    league = get_object_or_404(League, id=league_id)
    members = league.draft_room_members.all()
    all_ready = members.count() == league.members.count()  # All members have joined the draft room if counts match
    members_list = [{'username': member.username} for member in members]

    return JsonResponse({'members': members_list, 'all_ready': all_ready})

@login_required
def start_draft(request, league_id):
    league = get_object_or_404(League, id=league_id)
    if request.user == league.creator and not league.draft_started:
        league.draft_started = True
        league.save()
    return redirect('draft', league_id=league.id)

@login_required
def get_user_drafted_players(request):
    league_id = request.GET.get('league_id')
    league = get_object_or_404(League, id=league_id)
    user = request.user
    drafted_picks = DraftPick.objects.filter(league=league, team__user=user)

    drafted_players = [
        {
            'pick_number': pick.pick_number,
            'player_name': pick.player.name,
            'position': pick.player.position,
        }
        for pick in drafted_picks
    ]

    return JsonResponse({'drafted_players': drafted_players})

@login_required
def get_available_players(request):
    league_id = request.GET.get('league_id')
    league = get_object_or_404(League, id=league_id)

    # Get players that have not been drafted in this league
    drafted_players = DraftPick.objects.filter(league=league).values_list('player_id', flat=True)
    available_players = Player.objects.exclude(id__in=drafted_players)

    # Group players by position for a structured response
    players_by_position = []
    for position in ["Goalkeeper", "Defender", "Midfielder", "Attacker"]:
        players = available_players.filter(position=position).order_by('name')
        players_data = [
            {
                'id': player.id,
                'name': player.name,
                'position': player.position,
                'team_picture_url': f"../../static/img/{player.team.lower().replace(' ', '_')}.png",
                'past_points': player.past_points,
            }
            for player in players
        ]
        players_by_position.append({'position': position, 'players': players_data})

    return JsonResponse({'players_by_position': players_by_position})