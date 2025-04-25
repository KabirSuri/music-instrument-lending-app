from django import forms
from .models import Item, ItemImage, Library, Collection, UserProfile, Rating

class ItemForm(forms.ModelForm):
    image = forms.ImageField(required=False, label='Item Image')
    
    class Meta:
        model = Item
        fields = ['title', 'primary_identifier', 'status', 'library', 'description', 'collections']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def save(self, commit=True):
        item = super().save(commit=commit)
        if commit and self.cleaned_data.get('image'):
            ItemImage.objects.create(item=item, image=self.cleaned_data['image'])
        return item 

class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']
        
    def clean_profile_picture(self):
        image = self.cleaned_data.get('profile_picture')
        if image:
            if image.size > 5*1024*1024:  # 5MB limit
                raise forms.ValidationError("Image file too large ( > 5MB )")
        return image

class ProfileTextForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(disabled=True)

    class Meta:
        model = UserProfile
        fields = ['bio']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['first_name'].initial = self.user.first_name
        self.fields['last_name'].initial = self.user.last_name
        self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        if commit:
            self.user.save()
            profile.save()
        return profile
    
class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['stars', 'comment']
        widgets = {
            'stars': forms.NumberInput(attrs={'min': 1, 'max': 5, 'step': 1}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
