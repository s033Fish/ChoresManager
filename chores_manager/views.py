from django.shortcuts import render

def homepage_action(request):
    return render(request, 'login.html')
