from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Live


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Configuration admin pour le modèle User personnalisé."""

    list_display = (
        "username",
        "email",
        "is_admin",
        "is_approved",
        "is_active",
        "date_joined",
    )
    list_filter = ("is_admin", "is_approved", "is_active", "date_joined")
    search_fields = ("username", "email")
    ordering = ("-date_joined",)

    fieldsets = UserAdmin.fieldsets + (
        ("LiveManager", {"fields": ("is_admin", "is_approved")}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("LiveManager", {"fields": ("is_admin", "is_approved")}),
    )


@admin.register(Live)
class LiveAdmin(admin.ModelAdmin):
    """Configuration admin pour le modèle Live."""

    list_display = (
        "title",
        "user",
        "status",
        "is_scheduled",
        "scheduled_at",
        "created_at",
    )
    list_filter = ("status", "is_scheduled", "created_at")
    search_fields = ("title", "user__username", "user__email")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "ffmpeg_pid")

    fieldsets = (
        (
            "Informations générales",
            {"fields": ("user", "title", "video_file", "stream_key")},
        ),
        ("Programmation", {"fields": ("is_scheduled", "scheduled_at")}),
        ("Statut", {"fields": ("status", "ffmpeg_pid")}),
        (
            "Métadonnées",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
