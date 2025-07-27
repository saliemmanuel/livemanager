#!/usr/bin/env python3
"""
Script de test pour vérifier la gestion des timeouts lors de l'upload de gros fichiers.
"""

import os
import sys
import django
import time
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.contrib.auth import get_user_model

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'livemanager.settings')
django.setup()

User = get_user_model()

def test_large_file_upload():
    """Test d'upload d'un gros fichier pour vérifier les timeouts."""
    print("=== Test d'upload de gros fichier ===")
    
    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'is_approved': True,
            'is_admin': False
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"Utilisateur de test créé: {user.username}")
    else:
        print(f"Utilisateur de test existant: {user.username}")
    
    # Créer une clé de streaming de test
    from streams.models import StreamKey
    stream_key, created = StreamKey.objects.get_or_create(
        user=user,
        name='Test YouTube',
        defaults={
            'key': 'rtmp://a.rtmp.youtube.com/live2/test-key',
            'platform': 'YouTube',
            'is_active': True
        }
    )
    
    if created:
        print(f"Clé de streaming créée: {stream_key.name}")
    else:
        print(f"Clé de streaming existante: {stream_key.name}")
    
    # Créer un client de test
    client = Client()
    
    # Se connecter
    login_success = client.login(username='testuser', password='testpass123')
    if not login_success:
        print("❌ Échec de la connexion")
        return False
    
    print("✅ Connexion réussie")
    
    # Créer un fichier vidéo de test plus volumineux (10MB)
    print("📁 Création d'un fichier de test volumineux...")
    test_video_content = b'fake_video_content' * 655360  # ~10MB
    test_file = SimpleUploadedFile(
        "large_test_video.mp4",
        test_video_content,
        content_type="video/mp4"
    )
    
    print(f"📁 Fichier de test créé: {test_file.name} ({len(test_video_content)} bytes)")
    
    # Tester l'upload avec mesure du temps
    start_time = time.time()
    
    try:
        response = client.post('/create-live/', {
            'title': 'Test Large File Upload',
            'stream_key': stream_key.id,
            'video_file': test_file,
        }, follow=True)
        
        upload_time = time.time() - start_time
        print(f"⏱️ Temps d'upload: {upload_time:.2f} secondes")
        
        print(f"📤 Réponse du serveur: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Upload réussi!")
            
            # Vérifier que le fichier a été sauvegardé
            from streams.models import Live
            live = Live.objects.filter(user=user, title='Test Large File Upload').first()
            
            if live and live.video_file:
                print(f"✅ Live créé avec succès: {live.title}")
                print(f"📁 Fichier sauvegardé: {live.video_file.name}")
                
                # Vérifier que le fichier existe physiquement
                if os.path.exists(live.video_file.path):
                    print(f"✅ Fichier confirmé sur le disque: {live.video_file.path}")
                    file_size = os.path.getsize(live.video_file.path)
                    print(f"📊 Taille du fichier sur disque: {file_size} bytes")
                    
                    # Vérifier l'intégrité du fichier
                    if file_size == len(test_video_content):
                        print("✅ Intégrité du fichier vérifiée")
                        return True
                    else:
                        print(f"❌ Taille incorrecte: attendu {len(test_video_content)}, reçu {file_size}")
                        return False
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
            
    except Exception as e:
        upload_time = time.time() - start_time
        print(f"❌ Exception lors de l'upload après {upload_time:.2f} secondes: {str(e)}")
        return False

def test_upload_with_ajax_large():
    """Test d'upload AJAX avec un gros fichier."""
    print("\n=== Test d'upload AJAX gros fichier ===")
    
    client = Client()
    login_success = client.login(username='testuser', password='testpass123')
    
    if not login_success:
        print("❌ Échec de la connexion")
        return False
    
    # Créer un fichier vidéo de test volumineux (5MB)
    print("📁 Création d'un fichier de test volumineux pour AJAX...")
    test_video_content = b'fake_video_content' * 327680  # ~5MB
    test_file = SimpleUploadedFile(
        "large_test_video_ajax.mp4",
        test_video_content,
        content_type="video/mp4"
    )
    
    # Récupérer la clé de streaming
    from streams.models import StreamKey
    user = User.objects.get(username='testuser')
    stream_key = StreamKey.objects.filter(user=user, is_active=True).first()
    
    if not stream_key:
        print("❌ Aucune clé de streaming trouvée")
        return False
    
    # Tester l'upload AJAX avec mesure du temps
    start_time = time.time()
    
    try:
        response = client.post('/create-live/', {
            'title': 'Test Large File Upload AJAX',
            'stream_key': stream_key.id,
            'video_file': test_file,
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        upload_time = time.time() - start_time
        print(f"⏱️ Temps d'upload AJAX: {upload_time:.2f} secondes")
        
        print(f"📤 Réponse AJAX: {response.status_code}")
        
        if response.status_code == 200:
            try:
                import json
                data = json.loads(response.content)
                print(f"📄 Données JSON: {data}")
                
                if data.get('success'):
                    print("✅ Upload AJAX réussi!")
                    if 'file_size' in data:
                        print(f"📊 Taille du fichier: {data['file_size']} bytes")
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
            
    except Exception as e:
        upload_time = time.time() - start_time
        print(f"❌ Exception lors de l'upload AJAX après {upload_time:.2f} secondes: {str(e)}")
        return False

def test_timeout_configuration():
    """Test de la configuration des timeouts."""
    print("\n=== Test de la configuration des timeouts ===")
    
    from django.conf import settings
    
    print(f"📊 FILE_UPLOAD_MAX_MEMORY_SIZE: {settings.FILE_UPLOAD_MAX_MEMORY_SIZE} bytes")
    print(f"📊 DATA_UPLOAD_MAX_MEMORY_SIZE: {settings.DATA_UPLOAD_MAX_MEMORY_SIZE} bytes")
    print(f"📊 FILE_UPLOAD_TIMEOUT: {settings.FILE_UPLOAD_TIMEOUT} secondes")
    print(f"📊 CONN_MAX_AGE: {getattr(settings, 'CONN_MAX_AGE', 'Non défini')} secondes")
    
    # Vérifier que les valeurs sont correctes
    if settings.FILE_UPLOAD_MAX_MEMORY_SIZE >= 1048576000:  # 1GB
        print("✅ FILE_UPLOAD_MAX_MEMORY_SIZE correct")
    else:
        print("❌ FILE_UPLOAD_MAX_MEMORY_SIZE trop petit")
        return False
    
    if settings.FILE_UPLOAD_TIMEOUT >= 1800:  # 30 minutes
        print("✅ FILE_UPLOAD_TIMEOUT correct")
    else:
        print("❌ FILE_UPLOAD_TIMEOUT trop petit")
        return False
    
    return True

if __name__ == '__main__':
    print("🚀 Démarrage des tests de timeout d'upload...")
    
    # Test de la configuration
    config_ok = test_timeout_configuration()
    
    if not config_ok:
        print("❌ Configuration des timeouts incorrecte")
        sys.exit(1)
    
    # Test upload normal avec gros fichier
    success1 = test_large_file_upload()
    
    # Test upload AJAX avec gros fichier
    success2 = test_upload_with_ajax_large()
    
    print(f"\n📊 Résultats des tests:")
    print(f"   Configuration timeouts: {'✅ Correcte' if config_ok else '❌ Incorrecte'}")
    print(f"   Upload gros fichier: {'✅ Réussi' if success1 else '❌ Échec'}")
    print(f"   Upload AJAX gros fichier: {'✅ Réussi' if success2 else '❌ Échec'}")
    
    if config_ok and success1 and success2:
        print("\n🎉 Tous les tests de timeout sont passés!")
        sys.exit(0)
    else:
        print("\n💥 Certains tests de timeout ont échoué!")
        sys.exit(1) 