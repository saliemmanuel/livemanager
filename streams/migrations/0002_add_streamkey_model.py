# Generated manually for data migration

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("streams", "0001_initial"),
    ]

    operations = [
        # Créer le modèle StreamKey
        migrations.CreateModel(
            name="StreamKey",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=100, verbose_name="Nom de la clé"),
                ),
                (
                    "key",
                    models.CharField(max_length=500, verbose_name="Clé de diffusion"),
                ),
                (
                    "platform",
                    models.CharField(
                        default="YouTube", max_length=50, verbose_name="Plateforme"
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="Active")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Créé le"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Modifié le"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Utilisateur",
                    ),
                ),
            ],
            options={
                "verbose_name": "Clé de streaming",
                "verbose_name_plural": "Clés de streaming",
                "ordering": ["-created_at"],
            },
        ),
    ] 