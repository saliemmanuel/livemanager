from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Live, StreamKey


class UserRegistrationForm(UserCreationForm):
    """Formulaire d'inscription utilisateur."""

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class StreamKeyForm(forms.ModelForm):
    """Formulaire pour créer/modifier une clé de streaming."""
    
    class Meta:
        model = StreamKey
        fields = ["name", "key", "platform", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Ex: YouTube Principal"}),
            "key": forms.TextInput(attrs={"class": "form-input", "placeholder": "rtmp://a.rtmp.youtube.com/live2/..."}),
            "platform": forms.Select(attrs={"class": "form-select"}, choices=[
                ("YouTube", "YouTube"),
                ("Twitch", "Twitch"),
                ("Facebook", "Facebook"),
                ("Instagram", "Instagram"),
                ("TikTok", "TikTok"),
                ("Autre", "Autre"),
            ]),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        stream_key = super().save(commit=False)
        if self.user:
            stream_key.user = self.user
        if commit:
            stream_key.save()
        return stream_key


class LiveForm(forms.ModelForm):
    """Formulaire de création/modification de live."""

    class Meta:
        model = Live
        fields = ["title", "video_file", "stream_key", "is_scheduled", "scheduled_at"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-input"}),
            "scheduled_at": forms.DateTimeInput(
                attrs={"class": "form-input", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les clés de streaming pour l'utilisateur connecté
        if self.user:
            self.fields["stream_key"].queryset = StreamKey.objects.filter(
                user=self.user, 
                is_active=True
            )
            self.fields["stream_key"].widget.attrs.update({"class": "form-select"})
        
        self.fields["video_file"].widget.attrs.update({"class": "form-input"})
        self.fields["is_scheduled"].widget.attrs.update({"class": "form-checkbox"})

    def clean(self):
        cleaned_data = super().clean()
        is_scheduled = cleaned_data.get("is_scheduled")
        scheduled_at = cleaned_data.get("scheduled_at")

        if is_scheduled and not scheduled_at:
            raise forms.ValidationError(
                "La date et heure de programmation sont requises pour "
                "une diffusion programmée."
            )

        return cleaned_data
