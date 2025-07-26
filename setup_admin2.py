#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "livemanager.settings")
django.setup()

from streams.models import User

# Récupérer l'utilisateur 'admin'
user = User.objects.get(username="admin")

# Le rendre admin et approuvé
user.is_admin = True
user.is_approved = True
user.save()

print(f"Utilisateur {user.username} configuré comme admin et approuvé.")
print(f"Email: {user.email}")
print(
    "Vous pouvez maintenant vous connecter avec ce compte pour "
    "approuver d'autres utilisateurs."
)
