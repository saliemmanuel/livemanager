#!/usr/bin/env python3
"""
Script de test pour vérifier l'upload HTTP de fichiers vidéo.
"""

import os
import sys
import django
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.contrib.auth import get_user_model

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "livemanager.settings")
django.setup()

User = get_user_model()


def test_upload():
    """Test d'upload de fichier vidéo."""
    print("=== Test d'upload HTTP ===")

    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username="testuser",
        defaults={"email": "test@example.com", "is_approved": True, "is_admin": False},
    )

    if created:
        user.set_password("testpass123")
        user.save()
        print(f"Utilisateur de test créé: {user.username}")
    else:
        print(f"Utilisateur de test existant: {user.username}")

    # Créer une clé de streaming de test
    from streams.models import StreamKey

    stream_key, created = StreamKey.objects.get_or_create(
        user=user,
        name="Test YouTube",
        defaults={
            "key": "rtmp://a.rtmp.youtube.com/live2/test-key",
            "platform": "YouTube",
            "is_active": True,
        },
    )

    if created:
        print(f"Clé de streaming créée: {stream_key.name}")
    else:
        print(f"Clé de streaming existante: {stream_key.name}")

    # Créer un client de test
    client = Client()

    # Se connecter
    login_success = client.login(username="testuser", password="testpass123")
    if not login_success:
        print("❌ Échec de la connexion")
        return False

    print("✅ Connexion réussie")

    # Créer un fichier vidéo de test (1MB de données factices)
    test_video_content = b"fake_video_content" * 65536  # ~1MB
    test_file = SimpleUploadedFile(
        "test_video.mp4", test_video_content, content_type="video/mp4"
    )

    print(
        f"📁 Fichier de test créé: {test_file.name} ({len(test_video_content)} bytes)"
    )

    # Tester l'upload
    response = client.post(
        "/create-live/",
        {
            "title": "Test Live Upload",
            "stream_key": stream_key.id,
            "video_file": test_file,
        },
        follow=True,
    )

    print(f"📤 Réponse du serveur: {response.status_code}")

    if response.status_code == 200:
        print("✅ Upload réussi!")

        # Vérifier que le fichier a été sauvegardé
        from streams.models import Live

        live = Live.objects.filter(user=user, title="Test Live Upload").first()

        if live and live.video_file:
            print(f"✅ Live créé avec succès: {live.title}")
            print(f"📁 Fichier sauvegardé: {live.video_file.name}")

            # Vérifier que le fichier existe physiquement
            if os.path.exists(live.video_file.path):
                print(f"✅ Fichier confirmé sur le disque: {live.video_file.path}")
                file_size = os.path.getsize(live.video_file.path)
                print(f"📊 Taille du fichier sur disque: {file_size} bytes")
                return True
            else:
                print(f"❌ Fichier non trouvé sur le disque: {live.video_file.path}")
                return False
        else:
            print("❌ Live non trouvé en base de données")
            return False
    else:
        print(f"❌ Échec de l'upload: {response.status_code}")
        print(f"📄 Contenu de la réponse: {response.content[:500]}...")
        return False


def test_upload_with_ajax():
    """Test d'upload avec requête AJAX."""
    print("\n=== Test d'upload AJAX ===")

    client = Client()
    login_success = client.login(username="testuser", password="testpass123")

    if not login_success:
        print("❌ Échec de la connexion")
        return False

    # Créer un fichier vidéo de test
    test_video_content = b"fake_video_content" * 32768  # ~500KB
    test_file = SimpleUploadedFile(
        "test_video_ajax.mp4", test_video_content, content_type="video/mp4"
    )

    # Récupérer la clé de streaming
    from streams.models import StreamKey

    user = User.objects.get(username="testuser")
    stream_key = StreamKey.objects.filter(user=user, is_active=True).first()

    if not stream_key:
        print("❌ Aucune clé de streaming trouvée")
        return False

    # Tester l'upload AJAX
    response = client.post(
        "/create-live/",
        {
            "title": "Test Live Upload AJAX",
            "stream_key": stream_key.id,
            "video_file": test_file,
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    print(f"📤 Réponse AJAX: {response.status_code}")

    if response.status_code == 200:
        try:
            import json

            data = json.loads(response.content)
            print(f"📄 Données JSON: {data}")

            if data.get("success"):
                print("✅ Upload AJAX réussi!")
                return True
            else:
                print(f"❌ Erreur dans la réponse: {data.get('message')}")
                return False
        except json.JSONDecodeError:
            print(f"❌ Réponse non-JSON: {response.content[:200]}...")
            return False
    else:
        print(f"❌ Échec de l'upload AJAX: {response.status_code}")
        return False


if __name__ == "__main__":
    print("🚀 Démarrage des tests d'upload...")

    # Test upload normal
    success1 = test_upload()

    # Test upload AJAX
    success2 = test_upload_with_ajax()

    print("\n📊 Résultats des tests:")
    print(f"   Upload normal: {'✅ Réussi' if success1 else '❌ Échec'}")
    print(f"   Upload AJAX: {'✅ Réussi' if success2 else '❌ Échec'}")

    if success1 and success2:
        print("\n🎉 Tous les tests d'upload sont passés!")
        sys.exit(0)
    else:
        print("\n💥 Certains tests ont échoué!")
        sys.exit(1)
