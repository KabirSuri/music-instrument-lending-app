from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from allauth.socialaccount.models import SocialAccount

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
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
        
        # Save the updated profile
        user.profile.save()