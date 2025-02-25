from django.shortcuts import render
from django.contrib.auth import logout

def home(request):
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return render(request, '/')

def patron_login(request):
    return render(request, 'patron-landing.html')

def librarian_login(request):
    return render(request, 'librarian-landing.html')