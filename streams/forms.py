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
            "name": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Ex: YouTube Principal"}
            ),
            "key": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "rtmp://a.rtmp.youtube.com/live2/...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Ajouter une option vide au début des choix de plateforme
        platform_choices = [("", "Sélectionnez une plateforme")] + list(
            self.fields["platform"].choices
        )
        self.fields["platform"].choices = platform_choices
        self.fields["platform"].widget.attrs.update({"class": "form-select"})

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
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Filtrer les clés de streaming pour l'utilisateur connecté
        if self.user:
            self.fields["stream_key"].queryset = StreamKey.objects.filter(
                user=self.user, is_active=True
            )
            self.fields["stream_key"].widget.attrs.update({"class": "form-select"})
            # Rendre le champ optionnel
            self.fields["stream_key"].required = False

        self.fields["video_file"].widget.attrs.update({"class": "form-input"})
        self.fields["is_scheduled"].widget.attrs.update({"class": "form-checkbox"})

    def clean(self):
        cleaned_data = super().clean()
        is_scheduled = cleaned_data.get("is_scheduled")
        scheduled_at = cleaned_data.get("scheduled_at")
        stream_key = cleaned_data.get("stream_key")
        video_file = self.files.get("video_file") if self.files else None

        # Vérifier que le fichier vidéo est présent
        if not video_file:
            raise forms.ValidationError(
                "Un fichier vidéo est requis pour créer un live."
            )

        # Vérifier la taille du fichier
        if video_file and video_file.size > 524288000:  # 500MB
            raise forms.ValidationError(
                f"Le fichier est trop volumineux. Taille maximale: 500MB, "
                f"reçu: {video_file.size / (1024*1024):.1f}MB"
            )

        # Vérifier le type de fichier
        allowed_types = [
            "video/mp4",
            "video/avi",
            "video/mov",
            "video/wmv",
            "video/flv",
        ]
        if video_file and hasattr(video_file, "content_type"):
            if video_file.content_type not in allowed_types:
                raise forms.ValidationError(
                    f"Type de fichier non supporté. "
                    f"Types autorisés: {', '.join(allowed_types)}"
                )

        if is_scheduled and not scheduled_at:
            raise forms.ValidationError(
                "La date et heure de programmation sont requises pour "
                "une diffusion programmée."
            )

        # Vérifier si l'utilisateur a des clés de streaming configurées
        if self.user and not stream_key:
            user_keys = StreamKey.objects.filter(user=self.user, is_active=True)
            if not user_keys.exists():
                raise forms.ValidationError(
                    "Vous devez d'abord configurer au moins une clé de streaming "
                    "dans votre profil avant de créer un live. "
                    "Allez dans votre profil pour ajouter une clé."
                )

        return cleaned_data
