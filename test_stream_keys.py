#!/usr/bin/env python3
"""Script de test pour vérifier la sauvegarde des clés de streaming."""

import os
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'livemanager.settings')

import django
django.setup()

from streams.models import StreamKey, User
from streams.forms import StreamKeyForm


def test_stream_key_creation():
    """Test de création d'une clé de streaming."""
    print("=== Test de création de clé de streaming ===")

    # Trouver un utilisateur
    try:
        user = User.objects.first()
        if not user:
            print("❌ Aucun utilisateur trouvé dans la base de données")
            return False
        print(f"✅ Utilisateur trouvé: {user.username}")
    except Exception as e:
        print(f"❌ Erreur lors de la recherche d'utilisateur: {e}")
        return False

    # Données de test
    test_data = {
        'name': 'Test YouTube',
        'key': 'rtmp://a.rtmp.youtube.com/live2/test-key-123',
        'platform': 'YouTube',
        'is_active': True
    }

    print(f"📝 Données de test: {test_data}")

    # Créer le formulaire
    try:
        form = StreamKeyForm(data=test_data, user=user)
        print("✅ Formulaire créé")
        print(f"   Validité: {form.is_valid()}")

        if not form.is_valid():
            print(f"❌ Erreurs de validation: {form.errors}")
            return False

    except Exception as e:
        print(f"❌ Erreur lors de la création du formulaire: {e}")
        return False

    # Sauvegarder
    try:
        stream_key = form.save()
        print("✅ Clé de streaming sauvegardée avec succès!")
        print(f"   ID: {stream_key.id}")
        print(f"   Nom: {stream_key.name}")
        print(f"   Plateforme: {stream_key.platform}")
        print(f"   Utilisateur: {stream_key.user.username}")
        print(f"   Active: {stream_key.is_active}")
        print(f"   Créée le: {stream_key.created_at}")

    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return False

    # Vérifier dans la base de données
    try:
        saved_key = StreamKey.objects.get(id=stream_key.id)
        print("✅ Clé trouvée dans la base de données")
        print(f"   Nom: {saved_key.name}")
        print(f"   Clé: {saved_key.key[:50]}...")

    except StreamKey.DoesNotExist:
        print("❌ Clé non trouvée dans la base de données")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

    # Lister toutes les clés de l'utilisateur
    try:
        user_keys = StreamKey.objects.filter(user=user)
        print(f"\n📋 Clés de streaming de {user.username}:")
        for key in user_keys:
            status = 'Active' if key.is_active else 'Inactive'
            print(f"   - {key.name} ({key.platform}) - {status}")

    except Exception as e:
        print(f"❌ Erreur lors de la liste des clés: {e}")
        return False

    # Nettoyer (supprimer la clé de test)
    try:
        stream_key.delete()
        print("✅ Clé de test supprimée")
    except Exception as e:
        print(f"⚠️  Erreur lors de la suppression: {e}")

    return True


def test_stream_key_validation():
    """Test de validation du formulaire."""
    print("\n=== Test de validation du formulaire ===")

    # Trouver un utilisateur
    user = User.objects.first()
    if not user:
        print("❌ Aucun utilisateur trouvé")
        return False

    # Test avec données invalides
    invalid_data = {
        'name': '',  # Nom vide
        'key': '',   # Clé vide
        'platform': '',  # Plateforme vide
    }

    form = StreamKeyForm(data=invalid_data, user=user)
    print("📝 Test avec données invalides:")
    print(f"   Validité: {form.is_valid()}")
    if not form.is_valid():
        print(f"   Erreurs: {form.errors}")

    # Test avec données valides
    valid_data = {
        'name': 'Test Valide',
        'key': 'rtmp://test.com/live/valid-key',
        'platform': 'YouTube',
        'is_active': True
    }

    form = StreamKeyForm(data=valid_data, user=user)
    print("\n📝 Test avec données valides:")
    print(f"   Validité: {form.is_valid()}")
    if form.is_valid():
        print("   ✅ Formulaire valide")
    else:
        print(f"   ❌ Erreurs: {form.errors}")

    return True


if __name__ == "__main__":
    print("🔧 Test des clés de streaming")
    print("=" * 50)

    success = True

    # Test de création
    if not test_stream_key_creation():
        success = False

    # Test de validation
    if not test_stream_key_validation():
        success = False

    print("\n" + "=" * 50)
    if success:
        print("✅ Tous les tests ont réussi!")
    else:
        print("❌ Certains tests ont échoué!")

    sys.exit(0 if success else 1) 