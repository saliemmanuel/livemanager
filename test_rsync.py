#!/usr/bin/env python3
"""Script de test pour vérifier la configuration rsync."""

import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path

# Ajouter le répertoire du projet au PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "livemanager.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from streams.upload_rsync import upload_with_rsync  # noqa: E402


def test_rsync_config():
    """Test de la configuration rsync."""
    print("🔧 Test de la configuration rsync...")

    # Récupérer la configuration depuis les settings
    remote_user = getattr(settings, "RSYNC_USER", "root")
    remote_host = getattr(settings, "RSYNC_HOST", "localhost")
    remote_path = getattr(settings, "RSYNC_PATH", "/var/www/livemanager/media/videos/")

    print("📋 Configuration rsync:")
    print(f"   Utilisateur: {remote_user}")
    print(f"   Hôte: {remote_host}")
    print(f"   Chemin: {remote_path}")

    # Créer un fichier de test
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
        temp_file.write(b"Test rsync - LiveManager\n")
        temp_path = temp_file.name

    print(f"📁 Fichier de test créé: {temp_path}")

    try:
        # Tester l'upload
        print("🚀 Test d'upload rsync...")
        success, msg = upload_with_rsync(
            temp_path, remote_user, remote_host, remote_path
        )

        if success:
            print("✅ Upload rsync réussi!")
            print(f"   Message: {msg}")
        else:
            print("❌ Upload rsync échoué!")
            print(f"   Erreur: {msg}")

    except Exception as e:
        print(f"💥 Erreur lors du test: {e}")

    finally:
        # Nettoyage
        if os.path.exists(temp_path):
            os.unlink(temp_path)
            print("🧹 Fichier de test supprimé")


def check_rsync_installation():
    """Vérifier si rsync est installé."""
    print("🔍 Vérification de l'installation rsync...")

    if shutil.which("rsync"):
        print("✅ rsync est installé")

        # Vérifier la version
        try:
            result = subprocess.run(
                ["rsync", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                version_line = result.stdout.split("\n")[0]
                print(f"   Version: {version_line}")
        except Exception as e:
            print(f"   Impossible de récupérer la version: {e}")
    else:
        print("❌ rsync n'est pas installé")
        print("   Installez rsync avec: sudo apt-get install rsync (Ubuntu/Debian)")


if __name__ == "__main__":
    print("🚀 Test de configuration rsync pour LiveManager")
    print("=" * 50)

    check_rsync_installation()
    print()
    test_rsync_config()

    print("\n" + "=" * 50)
    print("✅ Test terminé!")
