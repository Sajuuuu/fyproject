from django import forms
from .models import Dog, DogImage


class DogListingForm(forms.ModelForm):
    class Meta:
        model = Dog
        fields = ['name', 'breed', 'gender', 'age', 'behaviour', 'description', 'price', 'location', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Max, Bella'}),
            'breed': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Golden Retriever, Labrador'}),
            'gender': forms.Select(attrs={'class': 'form-input'}),
            'age': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Age in months', 'min': '0'}),
            'behaviour': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Friendly, Energetic, Calm'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5, 'placeholder': 'Tell us about this dog...'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Adoption fee (रु)', 'min': '0'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'City or area'}),
            'image': forms.FileInput(attrs={'class': 'form-file'}),
        }
        labels = {
            'name': 'Dog Name',
            'breed': 'Breed',
            'gender': 'Gender',
            'age': 'Age (in months)',
            'behaviour': 'Behaviour',
            'description': 'Description',
            'price': 'Adoption Fee (रु)',
            'location': 'Location',
            'image': 'Main Image',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make image field optional when editing (instance exists)
        if self.instance and self.instance.pk:
            self.fields['image'].required = False


class DogImageForm(forms.ModelForm):
    class Meta:
        model = DogImage
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-file', 'accept': 'image/*'}),
        }
