#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier l'état d'un live
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "livemanager.settings")
django.setup()

# Import après django.setup() pour éviter les erreurs de configuration
from streams.models import Live  # noqa: E402


def debug_live(live_id):
    """Diagnostiquer un live spécifique."""
    try:
        live = Live.objects.get(id=live_id)

        print(f"🔍 Diagnostic du Live {live.id}: {live.title}")
        print("=" * 50)

        # Informations de base
        print(f"📋 Titre: {live.title}")
        print(f"👤 Utilisateur: {live.user.username} ({live.user.email})")
        print(f"📅 Créé le: {live.created_at}")
        print(f"🔄 Statut: {live.status}")
        print(f"🎬 PID FFmpeg: {live.ffmpeg_pid}")

        # Vérification de l'utilisateur
        print("\n👤 Statut de l'utilisateur:")
        print(f"  - Approuvé: {live.user.is_approved}")
        print(f"  - Admin: {live.user.is_admin}")
        print(f"  - Actif: {live.user.is_active}")

        # Vérification de la clé de streaming
        print("\n🔑 Clé de streaming:")
        if live.stream_key:
            print(f"  - Nom: {live.stream_key.name}")
            print(f"  - Plateforme: {live.stream_key.platform}")
            print(f"  - Active: {live.stream_key.is_active}")
            print(f"  - Clé: {live.stream_key.key[:20]}...")
        else:
            print("  ❌ Aucune clé de streaming configurée")

        # Vérification du fichier vidéo
        print("\n🎬 Fichier vidéo:")
        if live.video_file:
            video_path = os.path.join("media", live.video_file.name)
            print(f"  - Chemin: {video_path}")
            print(f"  - Existe: {os.path.exists(video_path)}")
            if os.path.exists(video_path):
                size = os.path.getsize(video_path)
                print(f"  - Taille: {size / (1024*1024):.2f} MB")
        else:
            print("  ❌ Aucun fichier vidéo")

        # Vérification des propriétés
        print("\n✅ Propriétés:")
        print(f"  - Peut démarrer (can_start): {live.can_start}")
        print(f"  - En cours (is_running): {live.is_running}")

        # Vérification du processus FFmpeg si en cours
        if live.ffmpeg_pid and live.status == "running":
            print("\n🔧 Processus FFmpeg:")
            try:
                import psutil

                proc = psutil.Process(live.ffmpeg_pid)
                print(f"  - PID: {live.ffmpeg_pid}")
                print(f"  - En cours: {proc.is_running()}")
                print(f"  - Nom: {proc.name()}")
                print(f"  - CPU: {proc.cpu_percent()}%")
                print(f"  - Mémoire: {proc.memory_info().rss / (1024*1024):.2f} MB")
            except psutil.NoSuchProcess:
                print(f"  ❌ Processus {live.ffmpeg_pid} n'existe pas")
            except Exception as e:
                print(f"  ❌ Erreur lors de la vérification: {e}")

        return True

    except Live.DoesNotExist:
        print(f"❌ Live {live_id} non trouvé")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du diagnostic: {e}")
        return False


def list_all_lives():
    """Lister tous les lives."""
    print("📋 Liste de tous les lives:")
    print("=" * 50)

    lives = Live.objects.all().order_by("-created_at")

    for live in lives:
        print(f"ID: {live.id} | {live.title} | {live.status} | {live.user.username}")

    return lives


def main():
    """Fonction principale."""
    if len(sys.argv) < 2:
        print("Usage: python debug_live.py <live_id>")
        print("   ou: python debug_live.py --list")
        return

    if sys.argv[1] == "--list":
        list_all_lives()
    else:
        try:
            live_id = int(sys.argv[1])
            debug_live(live_id)
        except ValueError:
            print("❌ L'ID du live doit être un nombre entier")


if __name__ == "__main__":
    main()
