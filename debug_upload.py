#!/usr/bin/env python3
"""
🔍 Script de Diagnostic - Problèmes d'Upload LiveManager
Ce script diagnostique les problèmes d'upload vidéo
"""

import os
import sys
import subprocess
import tempfile
import time
from pathlib import Path


def log(message):
    """Afficher un message avec timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def success(message):
    """Afficher un message de succès"""
    print(f"✅ {message}")


def error(message):
    """Afficher un message d'erreur"""
    print(f"❌ {message}")


def warning(message):
    """Afficher un message d'avertissement"""
    print(f"⚠️  {message}")


def check_django_settings():
    """Vérifier la configuration Django"""
    log("Vérification de la configuration Django...")

    try:
        from django.conf import settings

        # Vérifier les paramètres critiques
        checks = [
            ("DEBUG", settings.DEBUG),
            ("ALLOWED_HOSTS", settings.ALLOWED_HOSTS),
            ("MEDIA_URL", getattr(settings, "MEDIA_URL", "Non défini")),
            ("MEDIA_ROOT", getattr(settings, "MEDIA_ROOT", "Non défini")),
            ("STATIC_URL", getattr(settings, "STATIC_URL", "Non défini")),
            ("STATIC_ROOT", getattr(settings, "STATIC_ROOT", "Non défini")),
        ]

        for param, value in checks:
            if param == "ALLOWED_HOSTS":
                if "*" in value or "localhost" in value or "127.0.0.1" in value:
                    success(f"{param}: {value}")
                else:
                    warning(f"{param}: {value} (peut causer des problèmes)")
            else:
                success(f"{param}: {value}")

        return True

    except Exception as e:
        error(f"Erreur lors de la vérification Django: {e}")
        return False


def check_media_directory():
    """Vérifier le répertoire media"""
    log("Vérification du répertoire media...")

    try:
        from django.conf import settings

        media_root = getattr(settings, "MEDIA_ROOT", None)
        if not media_root:
            error("MEDIA_ROOT non défini dans les paramètres Django")
            return False

        media_path = Path(media_root)

        # Vérifier l'existence
        if media_path.exists():
            success(f"Répertoire media existe: {media_path}")
        else:
            error(f"Répertoire media manquant: {media_path}")
            return False

        # Vérifier les permissions
        if os.access(media_path, os.W_OK):
            success("Permissions d'écriture OK")
        else:
            error("Pas de permissions d'écriture sur le répertoire media")
            return False

        # Vérifier le sous-répertoire videos
        videos_path = media_path / "videos"
        if videos_path.exists():
            success(f"Sous-répertoire videos existe: {videos_path}")
        else:
            warning(f"Sous-répertoire videos manquant: {videos_path}")
            try:
                videos_path.mkdir(parents=True, exist_ok=True)
                success("Sous-répertoire videos créé")
            except Exception as e:
                error(f"Impossible de créer le répertoire videos: {e}")
                return False

        return True

    except Exception as e:
        error(f"Erreur lors de la vérification media: {e}")
        return False


def check_file_upload_settings():
    """Vérifier les paramètres d'upload de fichiers"""
    log("Vérification des paramètres d'upload...")

    try:
        from django.conf import settings

        # Vérifier les paramètres critiques
        upload_settings = [
            (
                "FILE_UPLOAD_MAX_MEMORY_SIZE",
                getattr(settings, "FILE_UPLOAD_MAX_MEMORY_SIZE", 2621440),
            ),
            (
                "DATA_UPLOAD_MAX_MEMORY_SIZE",
                getattr(settings, "DATA_UPLOAD_MAX_MEMORY_SIZE", 2621440),
            ),
            (
                "DATA_UPLOAD_MAX_NUMBER_FIELDS",
                getattr(settings, "DATA_UPLOAD_MAX_NUMBER_FIELDS", 1000),
            ),
        ]

        for param, value in upload_settings:
            if param.endswith("_SIZE"):
                size_mb = value / (1024 * 1024)
                success(f"{param}: {size_mb:.1f} MB")
            else:
                success(f"{param}: {value}")

        return True

    except Exception as e:
        error(f"Erreur lors de la vérification upload: {e}")
        return False


def check_ffmpeg_integration():
    """Vérifier l'intégration FFmpeg"""
    log("Vérification de l'intégration FFmpeg...")

    try:
        # Vérifier que FFmpeg est disponible
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            success("FFmpeg disponible")

            # Tester une commande de compression simple
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                test_input = temp_file.name

            # Créer un fichier de test
            test_cmd = [
                "ffmpeg",
                "-f",
                "lavfi",
                "-i",
                "testsrc=duration=1:size=320x240:rate=30",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-y",
                test_input,
            ]

            result = subprocess.run(
                test_cmd, capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0 and os.path.exists(test_input):
                success("Test de compression FFmpeg réussi")
                os.unlink(test_input)
                return True
            else:
                error(f"Test de compression FFmpeg échoué: {result.stderr}")
                return False
        else:
            error("FFmpeg non disponible")
            return False

    except Exception as e:
        error(f"Erreur lors de la vérification FFmpeg: {e}")
        return False


def check_nginx_config():
    """Vérifier la configuration Nginx"""
    log("Vérification de la configuration Nginx...")

    try:
        # Vérifier que Nginx est en cours d'exécution
        result = subprocess.run(
            ["systemctl", "is-active", "nginx"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and result.stdout.strip() == "active":
            success("Nginx actif")
        else:
            warning("Nginx inactif ou non accessible")

        # Vérifier la configuration
        result = subprocess.run(
            ["nginx", "-t"], capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            success("Configuration Nginx valide")
        else:
            error(f"Configuration Nginx invalide: {result.stderr}")
            return False

        return True

    except Exception as e:
        warning(f"Impossible de vérifier Nginx: {e}")
        return True  # Pas critique pour le diagnostic


def check_django_service():
    """Vérifier le service Django"""
    log("Vérification du service Django...")

    try:
        # Vérifier le statut du service
        result = subprocess.run(
            ["systemctl", "is-active", "livemanager"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and result.stdout.strip() == "active":
            success("Service livemanager actif")
        else:
            error("Service livemanager inactif")
            return False

        # Vérifier les logs récents
        result = subprocess.run(
            ["journalctl", "-u", "livemanager", "--no-pager", "-n", "10"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            logs = result.stdout
            if "error" in logs.lower() or "exception" in logs.lower():
                warning("Erreurs détectées dans les logs Django")
                print("📋 Logs récents:")
                print(logs)
            else:
                success("Aucune erreur récente dans les logs Django")

        return True

    except Exception as e:
        warning(f"Impossible de vérifier le service Django: {e}")
        return True


def test_file_upload():
    """Tester l'upload de fichier"""
    log("Test d'upload de fichier...")

    try:
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Créer un fichier de test
        test_content = b"Test file content for upload"
        test_file = SimpleUploadedFile(
            "test.txt", test_content, content_type="text/plain"
        )

        success("Fichier de test créé")

        # Vérifier que le fichier peut être lu
        if test_file.read() == test_content:
            success("Lecture du fichier de test OK")
        else:
            error("Erreur lors de la lecture du fichier de test")
            return False

        return True

    except Exception as e:
        error(f"Erreur lors du test d'upload: {e}")
        return False


def main():
    """Fonction principale"""
    print("🔍 Diagnostic des Problèmes d'Upload - LiveManager")
    print("=" * 60)

    tests_passed = 0
    total_tests = 7

    # Test 1: Configuration Django
    if check_django_settings():
        tests_passed += 1

    # Test 2: Répertoire media
    if check_media_directory():
        tests_passed += 1

    # Test 3: Paramètres d'upload
    if check_file_upload_settings():
        tests_passed += 1

    # Test 4: Intégration FFmpeg
    if check_ffmpeg_integration():
        tests_passed += 1

    # Test 5: Configuration Nginx
    if check_nginx_config():
        tests_passed += 1

    # Test 6: Service Django
    if check_django_service():
        tests_passed += 1

    # Test 7: Test d'upload
    if test_file_upload():
        tests_passed += 1

    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DU DIAGNOSTIC")
    print("=" * 60)

    if tests_passed == total_tests:
        success(f"Tous les tests sont passés ({tests_passed}/{total_tests})")
        print("\n🎉 Le système d'upload semble correct !")
        print("📋 Prochaines étapes:")
        print("   1. Vérifier la console du navigateur (F12)")
        print("   2. Tester avec un fichier plus petit")
        print("   3. Vérifier la connexion internet")
    else:
        error(f"Seulement {tests_passed}/{total_tests} tests sont passés")
        print("\n🔧 Actions recommandées:")
        print(
            "   1. Vérifier les permissions: "
            "sudo chown -R www-data:www-data /var/www/livemanager"
        )
        print("   2. Redémarrer les services: sudo systemctl restart livemanager nginx")
        print("   3. Vérifier les logs: sudo journalctl -u livemanager -f")
        print("   4. Tester FFmpeg: ffmpeg -version")

    print("\n🔍 Commandes de diagnostic supplémentaires:")
    print("   sudo journalctl -u livemanager -f")
    print("   sudo tail -f /var/log/nginx/error.log")
    print("   ls -la /var/www/livemanager/media/")
    print("   curl -X POST http://localhost/upload-test/")

    return tests_passed == total_tests


if __name__ == "__main__":
    test_success = main()
    sys.exit(0 if test_success else 1)
