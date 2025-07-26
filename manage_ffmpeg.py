#!/usr/bin/env python3
"""
Script de gestion des processus FFmpeg pour LiveManager
"""

import os
import sys
import django
import psutil
from django.db import transaction

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "livemanager.settings")
django.setup()

# Import après django.setup() pour éviter les erreurs de configuration
from streams.models import Live  # noqa: E402


def list_ffmpeg_processes():
    """Liste tous les processus FFmpeg en cours."""
    print("🔍 Recherche des processus FFmpeg...")

    ffmpeg_processes = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if proc.info["name"] and "ffmpeg" in proc.info["name"].lower():
                ffmpeg_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return ffmpeg_processes


def check_live_processes():
    """Vérifie la cohérence entre les lives en base et les processus FFmpeg."""
    print("\n📊 Vérification de la cohérence des lives...")

    # Lives en cours dans la base
    running_lives = Live.objects.filter(status="running")
    print(f"Lives en cours dans la base: {running_lives.count()}")

    for live in running_lives:
        print(f"  - Live {live.id}: {live.title} (PID: {live.ffmpeg_pid})")

        if live.ffmpeg_pid:
            try:
                # Vérifier si le processus existe
                proc = psutil.Process(live.ffmpeg_pid)
                if proc.is_running():
                    print(f"    ✅ Processus {live.ffmpeg_pid} en cours")
                else:
                    print(f"    ❌ Processus {live.ffmpeg_pid} arrêté")
                    # Marquer le live comme terminé
                    with transaction.atomic():
                        live.status = "completed"
                        live.ffmpeg_pid = None
                        live.save()
                    print(f"    🔄 Live {live.id} marqué comme terminé")
            except psutil.NoSuchProcess:
                print(f"    ❌ Processus {live.ffmpeg_pid} n'existe pas")
                # Marquer le live comme terminé
                with transaction.atomic():
                    live.status = "completed"
                    live.ffmpeg_pid = None
                    live.save()
                print(f"    🔄 Live {live.id} marqué comme terminé")


def kill_orphan_processes():
    """Tue les processus FFmpeg orphelins."""
    print("\n🧹 Nettoyage des processus orphelins...")

    ffmpeg_processes = list_ffmpeg_processes()
    running_lives = Live.objects.filter(status="running")
    running_pids = [live.ffmpeg_pid for live in running_lives if live.ffmpeg_pid]

    orphan_count = 0
    for proc in ffmpeg_processes:
        if proc.pid not in running_pids:
            print(f"  🗑️  Suppression du processus orphelin {proc.pid}")
            try:
                proc.terminate()
                orphan_count += 1
            except psutil.NoSuchProcess:
                pass

    print(f"  ✅ {orphan_count} processus orphelins supprimés")


def kill_all_ffmpeg():
    """Tue tous les processus FFmpeg (attention !)."""
    print("\n⚠️  ATTENTION: Suppression de TOUS les processus FFmpeg...")

    ffmpeg_processes = list_ffmpeg_processes()
    killed_count = 0

    for proc in ffmpeg_processes:
        print(f"  🗑️  Suppression du processus {proc.pid}")
        try:
            proc.terminate()
            killed_count += 1
        except psutil.NoSuchProcess:
            pass

    print(f"  ✅ {killed_count} processus FFmpeg supprimés")

    # Marquer tous les lives comme terminés
    with transaction.atomic():
        Live.objects.filter(status="running").update(
            status="completed", ffmpeg_pid=None
        )
    print("  🔄 Tous les lives marqués comme terminés")


def main():
    """Fonction principale."""
    if len(sys.argv) < 2:
        print("Usage: python manage_ffmpeg.py <command>")
        print("Commands:")
        print("  list     - Liste tous les processus FFmpeg")
        print("  check    - Vérifie la cohérence des lives")
        print("  clean    - Nettoie les processus orphelins")
        print("  kill-all - Tue tous les processus FFmpeg (ATTENTION!)")
        return

    command = sys.argv[1]

    if command == "list":
        ffmpeg_processes = list_ffmpeg_processes()
        print(f"\n📋 {len(ffmpeg_processes)} processus FFmpeg trouvés:")
        for proc in ffmpeg_processes:
            print(f"  - PID {proc.pid}: {' '.join(proc.cmdline())}")

    elif command == "check":
        check_live_processes()

    elif command == "clean":
        kill_orphan_processes()

    elif command == "kill-all":
        confirm = input(
            "Êtes-vous sûr de vouloir tuer TOUS les processus FFmpeg ? (y/N): "
        )
        if confirm.lower() == "y":
            kill_all_ffmpeg()
        else:
            print("Opération annulée")

    else:
        print(f"Commande inconnue: {command}")


if __name__ == "__main__":
    main()
