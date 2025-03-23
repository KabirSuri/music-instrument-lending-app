from django import forms
from .models import Item, ItemImage, Library, Collection

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