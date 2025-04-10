from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.account.signals import user_signed_up, user_logged_in
from django.utils import timezone
from datetime import timedelta
from allauth.socialaccount.models import SocialAccount
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = ProcessedImageField(
        upload_to='profile_images/',
        processors=[ResizeToFill(300, 300)],
        format='JPEG',
        options={'quality': 90},
        null=True,
        blank=True
    )
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

def update_user_role(user, request):
    """
    Helper function to update user role based on the login URL
    """
    if request and request.GET.get('next', '').endswith('librarian-landing/'):
        print(f"Setting user {user.email} as librarian")
        user.profile.is_librarian = True
    else:
        print(f"Setting user {user.email} as patron")
        user.profile.is_librarian = False
    user.profile.save()

@receiver(user_signed_up)
def populate_profile(request, user, **kwargs):
    """
    When a user signs up via Google, this pulls their profile data from the Google account
    and sets their role based on the login URL.
    """
    print(f"populate_profile signal triggered for user: {user.email}")
    
    if SocialAccount.objects.filter(user=user, provider='google').exists():
        social_account = SocialAccount.objects.get(user=user, provider='google')
        user_data = social_account.extra_data
        
        # Update profile with Google information
        if 'picture' in user_data:
            user.profile.profile_picture = user_data['picture']
    
    update_user_role(user, request)

@receiver(user_logged_in)
def update_role_on_login(request, user, **kwargs):
    """
    When a user logs in, update their role based on the login URL
    """
    print(f"update_role_on_login signal triggered for user: {user.email}")
    update_user_role(user, request)

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
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        default=1,
        related_name='collections_created'
        )
    is_public = models.BooleanField(default=True)
    library = models.ForeignKey(
        Library, 
        on_delete=models.CASCADE, 
        related_name='collections'
    )
    # Users who can access a PRIVATE collection (librarians bypass this automatically
    allowed_users = models.ManyToManyField(
        User, 
        blank=True,
        related_name='collections_allowed'
    )
    
    def __str__(self):
        return self.title

class LikeDislike(models.Model):
    LIKE = 1
    DISLIKE = -1
    VOTE_CHOICES = (
        (LIKE, 'Like'),
        (DISLIKE, 'Dislike'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='votes')
    vote = models.SmallIntegerField(choices=VOTE_CHOICES)

    class Meta:
        unique_together = ('user', 'item')