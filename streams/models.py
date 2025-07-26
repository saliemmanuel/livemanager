from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Modèle utilisateur personnalisé avec champs d'approbation."""

    is_admin = models.BooleanField(default=False, verbose_name="Administrateur")
    is_approved = models.BooleanField(default=False, verbose_name="Approuvé")

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return self.email


class StreamKey(models.Model):
    """Modèle pour les clés de streaming des utilisateurs."""

    PLATFORM_CHOICES = [
        ("YouTube", "YouTube"),
        ("Twitch", "Twitch"),
        ("Facebook", "Facebook"),
        ("Instagram", "Instagram"),
        ("TikTok", "TikTok"),
        ("Autre", "Autre"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    name = models.CharField(max_length=100, verbose_name="Nom de la clé")
    key = models.CharField(max_length=500, verbose_name="Clé de diffusion")
    platform = models.CharField(
        max_length=50, 
        verbose_name="Plateforme", 
        choices=PLATFORM_CHOICES,
        default="YouTube"
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        verbose_name = "Clé de streaming"
        verbose_name_plural = "Clés de streaming"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.user.email}"


class Live(models.Model):
    """Modèle pour les lives/diffusions."""

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("running", "En cours"),
        ("completed", "Terminé"),
        ("failed", "Échoué"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    title = models.CharField(max_length=200, verbose_name="Titre")
    video_file = models.FileField(upload_to="videos/", verbose_name="Fichier vidéo")
    stream_key = models.ForeignKey(
        StreamKey,
        on_delete=models.CASCADE,
        verbose_name="Clé de diffusion",
        null=True,
        blank=True,
    )
    scheduled_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Programmé pour"
    )
    is_scheduled = models.BooleanField(
        default=False, verbose_name="Diffusion programmée"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Statut"
    )
    ffmpeg_pid = models.IntegerField(null=True, blank=True, verbose_name="PID FFmpeg")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        verbose_name = "Live"
        verbose_name_plural = "Lives"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    @property
    def is_running(self):
        """Vérifie si le live est en cours."""
        return self.status == "running"

    @property
    def can_start(self):
        """Vérifie si le live peut être démarré."""
        return self.status == "pending" and self.user.is_approved
