from django.shortcuts import render

def login_view(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Login attempt - Role: {role}, Username: {username}")  # For testing
        
    return render(request, 'login-page/login.html')

def patron_login(request):
    return render(request, 'login-page/patron-landing.html')

def librarian_login(request):
    return render(request, 'login-page/librarian-landing.html')
