from django.shortcuts import render, redirect, render_to_response
from django.template import RequestContext
from drafter.forms import LeagueCreationForm, LeagueEditForm, UserCreationForm, RequestCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from drafter.models import League, User, FantasyTeam, Message
from django.core.urlresolvers import reverse


def index(request):
    return render(request, 'drafter/index.html')

"""
User-related views
"""
"""
Create a new user
"""
def new_user(request):
    if request.method == 'POST': # If the form was submitted...
        form = UserCreationForm(request.POST) # Make a form bound to the POST data
        if form.is_valid():
            new_user = form.save()
            username = request.POST['username']
            password = request.POST['password1']
            new_user = authenticate(username=username, password=password)
            login(request, new_user)
            return redirect(reverse('drafter.views.user', kwargs={ 'user_id': new_user.id })) 
    else:
        form = UserCreationForm() # Unbound form
    
    return render(request, 'drafter/users/new.html', { 'form': form })    

"""
View a specific user
"""
def user(request, user_id=None, username=None): # id=None, nick=None, for nick in url?
    if user_id:
        user = User.objects.get(id=user_id)
    else:
        user = User.objects.get(username=username)
    return render(request, 'drafter/users/user.html', { 'viewed_user': user })
"""
View all users
"""
def users(request):
    users = list(User.objects.all())
    return render(request, 'drafter/users/users.html', { 'users': users })



"""
League-related views
"""
"""
Create a new league
"""
@login_required
def new_league(request):
    if request.method == 'POST': # If the form was submitted...
        form = LeagueCreationForm(request.POST) # Make a form bound to the POST data
        if form.is_valid():
            new_league = form.save(commit=False)
            new_league.commish = request.user
            new_league.save()
            FantasyTeam.objects.create(manager=request.user, league=new_league)
            return redirect(reverse('drafter.views.league', kwargs={ 'league_id': new_league.id })) 
    else:
        form = LeagueCreationForm() # Unbound form
    return render(request, 'drafter/leagues/new.html', { 'form': form })

"""
View a specific league's default tab (for now hardcoded to Standings)
"""
def league(request, league_id=None):
    return redirect(reverse('drafter.views.league_standings', kwargs={ 'league_id': league_id })) 

"""
View a league's standings
"""
def league_standings(request, league_id=None):
    league = League.objects.get(id=league_id)
    teams = FantasyTeam.objects.filter(league=league)
    return render(request, 'drafter/leagues/details/league/standings.html', { 'league': league, 'teams': teams })

"""
View a league's rosters
"""
def league_rosters(request, league_id=None):
    league = League.objects.get(id=league_id)
    teams = FantasyTeam.objects.filter(league=league)
    return render(request, 'drafter/leagues/details/league/rosters.html', { 'league': league, 'teams': teams })
    
"""
View a league's scoring rules
"""
def league_scoring(request, league_id=None):
    league = League.objects.get(id=league_id)
    return render(request, 'drafter/leagues/details/league/scoring.html', { 'league': league })
"""
View a league's playoff bracket
"""
def league_playoffs(request, league_id=None):
    league = League.objects.get(id=league_id)
    return render(request, 'drafter/leagues/details/league/playoffs.html', { 'league': league })

"""
View a league's schedule
"""
def league_schedule(request, league_id=None):
    league = League.objects.get(id=league_id)
    return render(request, 'drafter/leagues/details/league/schedule.html', { 'league': league })
    
"""
View a league's draft management page
"""
@login_required
def league_draft(request, league_id=None):
    league = League.objects.get(id=league_id)
    if league in request.user.leagues.all() or league.commish == request.user:
        return render(request, 'drafter/leagues/details/league/draft.html', { 'league': league })
    else:
        return redirect(reverse('drafter.views.league', kwargs={ 'league_id': league_id }))
    
"""
View a league's commish panel
"""
@login_required
def league_settings(request, league_id=None):
    league = League.objects.get(id=league_id)
    if league.commish == request.user:
        if request.method == 'POST':
            form = LeagueEditForm(request.POST, instance=league)
            if form.is_valid():
                form.save()
        else:
            form = LeagueEditForm(instance=league) 
        return render(request, 'drafter/leagues/details/settings/settings.html', { 'league': league, 'form': form })
    else:
        return redirect(reverse('drafter.views.league', kwargs={ 'league_id': league_id }))

"""
View a league's join requests
"""
@login_required
def league_requests(request, league_id=None):
    league = League.objects.get(id=league_id)
    if league.commish == request.user:
        requests = Message.objects.filter(request=True, target_league=league_id)
        return render(request, 'drafter/leagues/details/settings/requests.html', { 'league': league, 'requests': requests })
    else:
        return redirect(reverse('drafter.views.league', kwargs={ 'league_id': league_id }))
"""
Join request
"""
@login_required
def join_league(request, league_id=None):
    league = League.objects.get(id=league_id)
    if request.method == 'POST':
        # If the league is full we return:
        if league.users.count() >= league.size:
            return redirect(reverse('drafter.views.league', kwargs={ 'league_id': league_id }))
        
        # If the league is public, let the logged in user join
        if league.public:
            FantasyTeam.objects.create(manager=request.user, league=league)
            return redirect(reverse('drafter.views.league', kwargs={ 'league_id': league_id }))
        else:
            # If the league is private, send a join request
            form = RequestCreationForm(request.POST)
            # REQUEST NOT = TRUE yet
            if form.is_valid():
                form.save()
                return redirect(reverse('drafter.views.league', kwargs={ 'league_id': league_id }))
    return redirect(reverse('drafter.views.league', kwargs={ 'league_id': league_id }))
"""
View all leagues
"""
def leagues(request):
    all_leagues = list(League.objects.all())
    if request.user.is_authenticated():
        my_leagues = list(request.user.leagues.all())
        commish_leagues = list(request.user.managed_leagues.all())
    else:
        my_leagues = None
        commish_leagues = None
    return render(request, 'drafter/leagues/leagues.html', { 'all_leagues': all_leagues, 'my_leagues': my_leagues, 'commish_leagues': commish_leagues })


    
