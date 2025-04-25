from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Item, BorrowRequest, ItemImage, Library, UserProfile, Collection,Rating
from .forms import ItemForm, ProfileImageForm, ProfileTextForm, RatingForm
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

    # Get recent collections
    collections = Collection.objects.filter(is_public=True).order_by('-id')[:5]  # Get 5 most recent PUBLIC collections

    context = {
        'borrowed_items': borrowed_items,
        'pending_requests': pending_requests,
        'collections': collections,
    }
    
    return render(request, 'patron-landing.html', context)

@login_required
def librarian_login(request):
    # Set user as librarian when they access this page
    if not request.user.profile.is_librarian:
        request.user.profile.is_librarian = True
        request.user.profile.save()
        messages.success(request, "Your account has been updated to librarian status.")

    # Get pending borrow requests for items not yet "in circulation"
    requests = BorrowRequest.objects.filter(approved=False, item__status='checked_in').order_by('-requested_at')
    
    collections = Collection.objects.all().order_by('-id')[:5]  # Get 5 most recent collections
    
    context = {
        'requests': requests,
        'collections': collections,
    }
    
    return render(request, 'librarian-landing.html', context)

# @login_required
# def profile_view(request):
#     if request.method == 'POST':
#         if 'clear_picture' in request.POST:
#             # Clear the profile picture
#             request.user.profile.profile_picture = None
#             request.user.profile.save()
#             messages.success(request, 'Profile picture cleared successfully!')
#             return redirect('profile')
#
#         form = ProfileImageForm(request.POST, request.FILES, instance=request.user.profile)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Profile picture updated successfully!')
#             return redirect('profile')
#     else:
#         form = ProfileImageForm(instance=request.user.profile)
#
#     return render(request, 'profile.html', {'form': form})
#
# @login_required
# def image_upload_view(request):
#     profile = request.user.profile
#     if request.method == 'POST':
#         if 'profile_image_file' in request.FILES:
#             profile.profile_picture = request.FILES['profile_image_file']
#             profile.save()
#
#         # Librarians (ONLY) can also add an image to an item
#         if profile.is_librarian and request.POST.get('item_id'):
#             item_id = request.POST.get('item_id')
#             if 'item_image_file' in request.FILES:
#                 try:
#                     item = Item.objects.get(id=item_id)
#                     ItemImage.objects.create(item=item, image=request.FILES['item_image_file'])
#                 except Item.DoesNotExist:
#                     pass
#         return redirect('profile')
#
#     context = {'profile': profile}
#     if profile.is_librarian:
#         return render(request, 'librarian_image_upload.html', context)
#     else:
#         return render(request, 'patron_image_upload.html', context)
# @login_required
# def profile_text_view(request):
#     profile = request.user.profile
#     if request.method == 'POST':
#         form = ProfileTextForm(request.POST, request.FILES, instance=profile, user=request.user)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Profile updated successfully!")
#             return redirect('profile')
#     else:
#         form = ProfileTextForm(instance=profile, user=request.user)
#
#     borrowed = BorrowRequest.objects.filter(user=request.user, approved=True).order_by('-due_date')
#
#     lent = None
#     if profile.is_librarian:
#         lent = Item.objects.all().order_by('-id')  # Optional: filter by ownership if relevant
#
#     template = 'librarian_profile.html' if profile.is_librarian else 'patron_profile.html'
#
#     return render(request, template, {
#         'form': form,
#         'profile': profile,
#         'borrowed': borrowed,
#         'lent': lent,
#     })
@login_required
def profile_view(request):
    profile = request.user.profile

    picture_form = ProfileImageForm(request.POST or None, request.FILES or None, instance=profile)
    text_form = ProfileTextForm(request.POST or None, instance=profile, user=request.user)

    if request.method == 'POST':
        if 'clear_picture' in request.POST:
            profile.profile_picture = None
            profile.save()
            messages.success(request, 'Profile picture cleared successfully!')
            return redirect('profile')

        if 'update_picture' in request.POST and picture_form.is_valid():
            picture_form.save()
            messages.success(request, 'Profile picture updated successfully!')
            return redirect('profile')

        if 'update_text' in request.POST and text_form.is_valid():
            text_form.save()
            messages.success(request, 'Profile info updated successfully!')
            return redirect('profile')

    borrowed = BorrowRequest.objects.filter(user=request.user, approved=True).order_by('-due_date')
    lent = Item.objects.all().order_by('-id') if profile.is_librarian else None
    #
    # liked_items = Item.objects.filter(votes__user=request.user, votes__vote=1)
    # disliked_items = Item.objects.filter(votes__user=request.user, votes__vote=-1)

    return render(request, 'profile.html', {
        'form': picture_form,
        'text_form': text_form,
        'profile': profile,
        'borrowed': borrowed,
        'lent': lent,
        # 'liked_items': liked_items,
        # 'disliked_items': disliked_items,
    })
@login_required
def borrow_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    borrow_request = BorrowRequest.objects.filter(item=item, user=request.user, approved=False).first()

    if borrow_request: #the item already has been requested, now cancel
        borrow_request.delete()
        messages.success(request, f"Your borrow request for '{item.title}' has been canceled.")
    else: #request the item
        BorrowRequest.objects.create(item=item, user=request.user)
        messages.success(request, f"Your borrow request for '{item.title}' has been submitted.")

    return redirect('item_detail', item_id=item.id)  # Redirect back to the item detail page

def manage_borrow_request(request, request_id):
    borrow_request = get_object_or_404(BorrowRequest, id=request_id)
    item = borrow_request.item

    # Only allow librarians to approve/deny requests
    if not request.user.profile.is_librarian:
        messages.error(request, "You do not have permission to manage borrow requests.")
        return redirect('librarian-landing')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            # Approve the request and update the item status to "in circulation"
            borrow_request.approve()
            messages.success(request, f"Request for '{item.title}' has been approved and item is now in circulation.")
        
        elif action == 'deny':
            # Deny the borrow request (delete it)
            borrow_request.delete()
            messages.success(request, f"Request for '{item.title}' has been denied.")
    
    return redirect('librarian-landing')

def search_items(request):
    """Display and search for items."""
    query = request.GET.get('q', '')
    
    if query:
        items = Item.objects.filter(title__icontains=query)
    else:
        items = Item.objects.all()

    return render(request, "item_list.html", {"items": items, "query": query})


@login_required
def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    has_requested = BorrowRequest.objects.filter(item=item, user=request.user, approved=False).exists()

    return render(request, 'item_detail.html', {
        'item': item,
        'has_requested': has_requested,
    })

@login_required
def create_item(request):
    if not request.user.profile.is_librarian:
        messages.error(request, "Only librarians can create items.")
        return redirect('catalog')

    if request.method == 'POST':
        # Get the default library (assuming single library system)
        library = Library.objects.first()
        if not library:
            library= Library.objects.create(name="Main Library")

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
    """Delete an existing item."""
    if not request.user.profile.is_librarian:
        messages.error(request, "Only librarians can delete items.")
        return redirect('catalog')
    
    item = get_object_or_404(Item, id=item_id)
    
    if request.method == 'POST':
        item_title = item.title  # Save title before deletion for messaging
        item.delete()
        messages.success(request, f"Item '{item_title}' deleted successfully!")
        return redirect('catalog')  # Adjust if your item list URL is different
    
    return redirect('item_detail', item_id=item.id)

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
    """Display collections with search functionality.
       Librarians see all collections; patrons only see public collections.
    """
    query = request.GET.get('q', '')
    if request.user.profile.is_librarian:
        collections = Collection.objects.all().order_by('-id')
        if query:
            collections = collections.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )
    else:
        collections = Collection.objects.filter(is_public=True).order_by('-id')
        if query:
            collections = collections.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )
    return render(request, 'collections/collection_list.html', {
        'collections': collections,
        'query': query
    })

@login_required
def create_collection(request):
    """Create a new collection."""
    default_library = Library.objects.get(id=1) #the single library in this project

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        # Librarians can choose private; Patrons forced public
        if request.user.profile.is_librarian:
            is_public = request.POST.get('is_public') == 'on'
        else:
            is_public = True

        if title:
            collection = Collection.objects.create(
                title=title,
                description=description,
                is_public=is_public,
                creator=request.user,
                library=default_library
            )
            
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
    collection = get_object_or_404(Collection, id=collection_id)
    
    if not (request.user.profile.is_librarian or collection.creator == request.user):
        messages.error(request, "You don't have permission to edit this collection.")
        return redirect('catalog')
    
    if request.method == 'POST':
        collection.title = request.POST.get('title', collection.title)
        collection.description = request.POST.get('description', collection.description)
        if request.user.profile.is_librarian:
            collection.is_public = request.POST.get('is_public') == 'on'
        else:
            collection.is_public = True
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

@login_required
def delete_collection(request, collection_id):
    """Delete an existing collection."""
    collection = get_object_or_404(Collection, id=collection_id)
    
    if not (request.user.profile.is_librarian or collection.creator == request.user):
        messages.error(request, "You don't have permission to delete this collection.")
        return redirect('catalog')
    
    if request.method == 'POST':
        collection_title = collection.title
        collection.delete()
        messages.success(request, f"Collection '{collection_title}' deleted successfully!")
        return redirect('collections')
    
    return redirect('collection-detail', collection_id=collection.id)

@login_required
def rate_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating, created = Rating.objects.update_or_create(
                item=item,
                user=request.user,
                defaults={'stars': form.cleaned_data['stars'],
                          'comment': form.cleaned_data['comment']
                          }
            )
            return redirect('item_detail', item_id=item.id)
    else:
        form = RatingForm()
    return render(request, 'rate_item.html', {'item': item, 'form': form})
