from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Live


class UserRegistrationForm(UserCreationForm):
    """Formulaire d'inscription utilisateur."""
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class LiveForm(forms.ModelForm):
    """Formulaire de création/modification de live."""
    
    class Meta:
        model = Live
        fields = ['title', 'video_file', 'stream_key', 'is_scheduled', 'scheduled_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'stream_key': forms.TextInput(attrs={'class': 'form-input'}),
            'scheduled_at': forms.DateTimeInput(
                attrs={'class': 'form-input', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['video_file'].widget.attrs.update({'class': 'form-input'})
        self.fields['is_scheduled'].widget.attrs.update({'class': 'form-checkbox'})
    
    def clean(self):
        cleaned_data = super().clean()
        is_scheduled = cleaned_data.get('is_scheduled')
        scheduled_at = cleaned_data.get('scheduled_at')
        
        if is_scheduled and not scheduled_at:
            raise forms.ValidationError(
                "La date et heure de programmation sont requises pour une diffusion programmée."
            )
        
        return cleaned_data 