from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from django.utils import timezone
from datetime import timedelta
from allauth.socialaccount.models import SocialAccount

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_librarian = models.BooleanField(default=False)
    
    def __str__(self):
        return self.user.email

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(user_signed_up)
def populate_profile(request, user, **kwargs):
    """
    When a user signs up via Google, this pulls their profile data from the Google account
    """
    if SocialAccount.objects.filter(user=user, provider='google').exists():
        social_account = SocialAccount.objects.get(user=user, provider='google')
        user_data = social_account.extra_data
        
        # Update profile with Google information
        if 'picture' in user_data:
            user.profile.profile_picture = user_data['picture']
    
    # set librarian variable on librarian logins
    # role setting didnt work
    # intermediary view didnt work
    next_url = request.GET.get('next', '')
    if next_url.startswith('/librarian-landing'):
        user.profile.is_librarian = True
    else:
        user.profile.is_librarian = False

    # Save the updated profile
    user.profile.save()

# Maybe unneeded, unclear if we will ever have >1 library https://s25.cs3240.org/project.html#libraries
class Library(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

# https://s25.cs3240.org/project.html#items
class Item(models.Model):
    # Defaults from project info examples; replaceable if unneeded
    STATUS_CHOICES = [
        ('checked_in', 'Checked In'),
        ('in_circulation', 'In Circulation'),
        ('being_repaired', 'Being Repaired'),
    ]
    
    title = models.CharField(max_length=255)
    primary_identifier = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='items')
    description = models.TextField(blank=True, null=True)
    # Items belong to 0-inf collections inclusive
    collections = models.ManyToManyField('Collection', related_name='items', blank=True)
    
    def __str__(self):
        return self.title

# Item images, fetched from S3
class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='item_images/', null=True, blank=True)
    time = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.item.title}"

# Item ratings/comments
class ItemReview(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True, null=True)
    time = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review for {self.item.title} by {self.user.email}"
    
class BorrowRequest(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='borrow_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)

    def approve(self):
        """Approve request and update item status"""
        self.approved = True
        self.due_date = timezone.now().date() + timedelta(days=14)  # 2-week borrow period
        self.item.status = 'in_circulation'
        self.item.save()
        self.save()

    def __str__(self):
        return f"{self.user.username} requested {self.item.title}"


# https://s25.cs3240.org/project.html#collections
class Collection(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=True)
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='collections')
    # Users who can access a PRIVATE collection (librarians bypass this automatically)
    allowed_users = models.ManyToManyField(User, blank=True)
    
    def __str__(self):
        return self.title
