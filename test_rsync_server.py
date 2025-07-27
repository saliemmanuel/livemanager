#!/usr/bin/env python3
"""Script de test pour vérifier la configuration rsync sur le serveur."""

import os
import sys
import tempfile
from pathlib import Path

# Ajouter le répertoire du projet au PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'livemanager.settings')

import django  # noqa: E402
django.setup()

from django.conf import settings  # noqa: E402
from streams.upload_rsync import upload_with_rsync  # noqa: E402


def test_rsync_server():
    """Test de la configuration rsync sur le serveur."""
    print("🔧 Test de la configuration rsync sur le serveur...")

    # Récupérer la configuration depuis les settings
    remote_user = getattr(settings, "RSYNC_USER", "root")
    remote_host = getattr(settings, "RSYNC_HOST", "localhost")
    remote_path = getattr(settings, "RSYNC_PATH", "/var/www/livemanager/media/videos/")

    print("📋 Configuration rsync:")
    print(f"   Utilisateur: {remote_user}")
    print(f"   Hôte: {remote_host}")
    print(f"   Chemin: {remote_path}")

    # Vérifier si on est sur le serveur
    if remote_host == "localhost":
        print("✅ Test local - serveur détecté")
    else:
        print(f"🌐 Test distant vers {remote_host}")

    # Créer un fichier de test
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
        temp_file.write(b"Test rsync serveur - LiveManager\n")
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

            # Vérifier si le fichier existe sur le serveur
            if remote_host == "localhost":
                server_file = os.path.join(remote_path, os.path.basename(temp_path))
                if os.path.exists(server_file):
                    print(f"✅ Fichier trouvé sur le serveur: {server_file}")
                    # Nettoyer le fichier de test sur le serveur
                    os.unlink(server_file)
                    print("🧹 Fichier de test supprimé du serveur")
                else:
                    print(f"❌ Fichier non trouvé sur le serveur: {server_file}")
        else:
            print("❌ Upload rsync échoué!")
            print(f"   Erreur: {msg}")

    except Exception as e:
        print(f"💥 Erreur lors du test: {e}")

    finally:
        # Nettoyage du fichier local
        if os.path.exists(temp_path):
            os.unlink(temp_path)
            print("🧹 Fichier de test local supprimé")


def check_server_environment():
    """Vérifier l'environnement du serveur."""
    print("🔍 Vérification de l'environnement serveur...")

    # Vérifier rsync
    import shutil

    if shutil.which("rsync"):
        print("✅ rsync est installé")

        # Vérifier la version
        import subprocess

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

    # Vérifier les permissions
    remote_path = getattr(settings, "RSYNC_PATH", "/var/www/livemanager/media/videos/")
    if os.path.exists(remote_path):
        print(f"✅ Répertoire de destination existe: {remote_path}")

        # Vérifier les permissions
        import stat

        st = os.stat(remote_path)
        mode = stat.S_IMODE(st.st_mode)
        print(f"   Permissions: {oct(mode)}")

        # Vérifier si on peut écrire
        if os.access(remote_path, os.W_OK):
            print("✅ Permissions d'écriture OK")
        else:
            print("❌ Pas de permissions d'écriture")
    else:
        print(f"❌ Répertoire de destination n'existe pas: {remote_path}")

    # Vérifier la configuration Django
    print("📋 Configuration Django:")
    print(f"   RSYNC_USER: {getattr(settings, 'RSYNC_USER', 'Non défini')}")
    print(f"   RSYNC_HOST: {getattr(settings, 'RSYNC_HOST', 'Non défini')}")
    print(f"   RSYNC_PATH: {getattr(settings, 'RSYNC_PATH', 'Non défini')}")


if __name__ == "__main__":
    print("🚀 Test de configuration rsync serveur pour LiveManager")
    print("=" * 60)

    check_server_environment()
    print()
    test_rsync_server()

    print("\n" + "=" * 60)
    print("✅ Test terminé!")
