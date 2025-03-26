from django import forms
from .models import Item, ItemImage, Library, Collection, UserProfile

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