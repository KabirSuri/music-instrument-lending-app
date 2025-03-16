from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Item, ItemImage

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

@login_required
def profile_view(request):
    # Renders a different template for librarians  and patrons
    # Anonymous users are redirected to the login page
    profile = request.user.profile
    context = {'profile': profile}
    if profile.is_librarian:
        return render(request, 'librarian_profile.html', context)
    else:
        return render(request, 'patron_profile.html', context)

@login_required
def image_upload_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        if 'profile_image_file' in request.FILES:
            profile.profile_picture = request.FILES['profile_image_file']
            profile.save()
        
        # Librarians (ONLY) can also add an image to an item
        if profile.is_librarian and request.POST.get('item_id'):
            item_id = request.POST.get('item_id')
            if 'item_image_file' in request.FILES:
                try:
                    item = Item.objects.get(id=item_id)
                    ItemImage.objects.create(item=item, image=request.FILES['item_image_file'])
                except Item.DoesNotExist:
                    pass
        return redirect('profile')
    
    context = {'profile': profile}
    if profile.is_librarian:
        return render(request, 'librarian_image_upload.html', context)
    else:
        return render(request, 'patron_image_upload.html', context)

