#!/usr/bin/env python
"""
Script pour créer un administrateur rapidement
Usage: python create_admin.py username email
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'livemanager.settings')
django.setup()

from streams.models import User
from django.contrib.auth.hashers import make_password

def create_admin(username, email, password=None):
    """Crée un utilisateur administrateur."""
    try:
        # Vérifier si l'utilisateur existe déjà
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'password': make_password(password or 'admin123'),
                'is_admin': True,
                'is_approved': True,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if created:
            print(f"✅ Administrateur créé avec succès !")
            print(f"   Username: {username}")
            print(f"   Email: {email}")
            print(f"   Mot de passe: {password or 'admin123'}")
        else:
            # Mettre à jour l'utilisateur existant
            user.is_admin = True
            user.is_approved = True
            user.is_staff = True
            user.is_superuser = True
            user.save()
            print(f"✅ Utilisateur {username} promu administrateur !")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        email = sys.argv[2]
        password = sys.argv[3] if len(sys.argv) > 3 else None
        create_admin(username, email, password)
    else:
        print("Usage: python create_admin.py username email [password]")
        print("Exemple: python create_admin.py john john@example.com secret123") 