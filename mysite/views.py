from django.shortcuts import render

def login_view(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        username = request.POST.get('username')
        password = request.POST.get('password')
        
    return render(request, 'login.html')

def patron_login(request):
    return render(request, 'patron-landing.html')

def librarian_login(request):
    return render(request, 'librarian-landing.html')
