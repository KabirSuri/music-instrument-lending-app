from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Item, BorrowRequest, ItemImage, Library, UserProfile, Collection
from .forms import ItemForm, ProfileImageForm
from django.urls import reverse
from django.contrib.auth.views import LogoutView
from allauth.socialaccount.providers.google.views import oauth2_login

def login_view(request):
    # Clear any existing messages
    storage = messages.get_messages(request)
    storage.used = True
    
    if request.user.is_authenticated:
        return redirect('catalog')
    return render(request, 'login.html')

def logout_view(request):
    storage = messages.get_messages(request)
    storage.used = True
    return LogoutView.as_view(next_page='login')(request)

def patron_login(request):
    # Get current user's borrowed items (approved requests with due dates)
    borrowed_items = BorrowRequest.objects.filter(
        user=request.user,
        approved=True,
        due_date__isnull=False
    ).order_by('due_date')

    # Get pending requests
    pending_requests = BorrowRequest.objects.filter(
        user=request.user,
        approved=False
    ).order_by('-requested_at')

    context = {
        'borrowed_items': borrowed_items,
        'pending_requests': pending_requests,
    }
    
    return render(request, 'patron-landing.html', context)

@login_required
def librarian_login(request):
    # Set user as librarian when they access this page
    if not request.user.profile.is_librarian:
        request.user.profile.is_librarian = True
        request.user.profile.save()
        messages.success(request, "Your account has been updated to librarian status.")

    # Get pending borrow requests
    requests = BorrowRequest.objects.filter(approved=False).order_by('-requested_at')
    
    # Get recent collections
    collections = Collection.objects.all().order_by('-id')[:5]  # Get 5 most recent collections
    
    context = {
        'requests': requests,
        'collections': collections,
    }
    
    return render(request, 'librarian-landing.html', context)

@login_required
def profile_view(request):
    if request.method == 'POST':
        if 'clear_picture' in request.POST:
            # Clear the profile picture
            request.user.profile.profile_picture = None
            request.user.profile.save()
            messages.success(request, 'Profile picture cleared successfully!')
            return redirect('profile')
            
        form = ProfileImageForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile picture updated successfully!')
            return redirect('profile')
    else:
        form = ProfileImageForm(instance=request.user.profile)
    
    return render(request, 'profile.html', {'form': form})

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

@login_required
def create_item(request):
    if not request.user.profile.is_librarian:
        messages.error(request, "Only librarians can create items.")
        return redirect('catalog')

    if request.method == 'POST':
        # Get the default library (assuming single library system)
        library = Library.objects.first()
        if not library:
            library = Library.objects.create(name="Main Library")

        # Create the item
        item = Item.objects.create(
            title=request.POST.get('title'),
            primary_identifier=request.POST.get('primary_identifier'),
            description=request.POST.get('description'),
            status=request.POST.get('status'),
            library=library
        )

        # Handle image upload
        if 'image' in request.FILES:
            ItemImage.objects.create(
                item=item,
                image=request.FILES['image']
            )

        messages.success(request, f"Item '{item.title}' created successfully!")
        return redirect('item_detail', item_id=item.id)

    return render(request, 'create_item.html')

@login_required
def edit_item(request, item_id):
    if not request.user.profile.is_librarian:
        messages.error(request, "Only librarians can edit items.")
        return redirect('librarian-landing')
    
    item = get_object_or_404(Item, id=item_id)
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            item = form.save()
            messages.success(request, f"Item '{item.title}' updated successfully!")
            return redirect('item_detail', item_id=item.id)
    else:
        form = ItemForm(instance=item)
    
    return render(request, 'edit_item.html', {'form': form, 'item': item})

@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    
    if not request.user.profile.is_librarian:
        messages.error(request, "You don't have permission to delete this item.")
        return redirect('item_detail', item_id=item_id)

    if request.method == 'POST':
        item.delete()
        messages.success(request, "Item deleted successfully.")
        return redirect('catalog')  # or wherever you want to redirect after deletion

    return redirect('item_detail', item_id=item_id)

def catalog_view(request):
    """Display the catalog of all items with search functionality."""
    query = request.GET.get('q', '')
    
    if query:
        items = Item.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(primary_identifier__icontains=query)
        )
    else:
        items = Item.objects.all()
    
    return render(request, "catalog.html", {
        "items": items,
        "query": query
    })

@login_required
def collection_list(request):
    """Display all collections with search functionality."""
    if not request.user.profile.is_librarian:
        messages.error(request, "Only librarians can view collections.")
        return redirect('catalog')
    
    query = request.GET.get('q', '')
    if query:
        collections = Collection.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
    else:
        collections = Collection.objects.all().order_by('-id')
    
    return render(request, 'collections/collection_list.html', {
        'collections': collections,
        'query': query
    })

@login_required
def create_collection(request):
    """Create a new collection."""
    if not request.user.profile.is_librarian:
        messages.error(request, "Only librarians can create collections.")
        return redirect('catalog')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        is_public = request.POST.get('is_public') == 'on'
        default_library=Library.objects.get(id=1) #the single library in this project

        if title:
            collection = Collection.objects.create(
                title=title,
                description=description,
                is_public=is_public,
                creator=request.user,
                library=default_library
            )
            
            # Handle selected items
            item_ids = request.POST.getlist('items')
            if item_ids:
                items = Item.objects.filter(id__in=item_ids)
                collection.items.add(*items)
            
            messages.success(request, f"Collection '{collection.title}' created successfully!")
            return redirect('collection-detail', collection_id=collection.id)
    
    # Get available items for the collection
    items = Item.objects.all()
    return render(request, 'collections/create_collection.html', {'items': items})

@login_required
def collection_detail(request, collection_id):
    """Display details of a specific collection."""
    collection = get_object_or_404(Collection, id=collection_id)
    
    if not collection.is_public and not request.user.profile.is_librarian:
        messages.error(request, "You don't have permission to view this collection.")
        return redirect('catalog')
    
    return render(request, 'collections/collection_detail.html', {
        'collection': collection
    })

@login_required
def edit_collection(request, collection_id):
    """Edit an existing collection."""
    if not request.user.profile.is_librarian:
        messages.error(request, "Only librarians can edit collections.")
        return redirect('catalog')
    
    collection = get_object_or_404(Collection, id=collection_id)
    
    if request.method == 'POST':
        collection.title = request.POST.get('title', collection.title)
        collection.description = request.POST.get('description', collection.description)
        collection.is_public = request.POST.get('is_public') == 'on'
        collection.save()
        
        # Update items
        item_ids = request.POST.getlist('items')
        collection.items.clear()
        if item_ids:
            items = Item.objects.filter(id__in=item_ids)
            collection.items.add(*items)
        
        messages.success(request, f"Collection '{collection.title}' updated successfully!")
        return redirect('collection-detail', collection_id=collection.id)
    
    # Get available items for the collection
    items = Item.objects.all()
    return render(request, 'collections/edit_collection.html', {
        'collection': collection,
        'items': items
    })