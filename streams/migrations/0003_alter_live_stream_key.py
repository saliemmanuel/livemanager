# Generated manually for data migration

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("streams", "0002_add_streamkey_model"),
    ]

    operations = [
        # Modifier le champ stream_key dans Live
        migrations.AlterField(
            model_name="live",
            name="stream_key",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="streams.streamkey",
                verbose_name="Clé de diffusion",
            ),
        ),
    ]
