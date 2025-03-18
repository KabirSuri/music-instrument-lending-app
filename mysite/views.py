from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Item, BorrowRequest, ItemImage
from django.urls import reverse
from allauth.socialaccount.providers.google.views import oauth2_login

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

@login_required
def borrow_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    # Prevent duplicate requests
    existing_request = BorrowRequest.objects.filter(item=item, user=request.user, approved=False).exists()
    if existing_request:
        return redirect('item_detail', item_id=item.id)

    # Create a borrow request
    BorrowRequest.objects.create(item=item, user=request.user)

    return redirect('item_detail', item_id=item.id)  # Redirect back to item page

def search_items(request):
    """Display and search for items."""
    query = request.GET.get('q', '')
    
    if query:
        items = Item.objects.filter(title__icontains=query)
    else:
        items = Item.objects.all()

    return render(request, "item_list.html", {"items": items, "query": query})


def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    return render(request, "item_detail.html", {"item": item})