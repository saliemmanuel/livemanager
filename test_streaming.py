#!/usr/bin/env python3
"""
Script de test pour la commande FFmpeg de streaming
"""

import os
import subprocess
import time
import sys


def test_ffmpeg_command():
    """Teste la commande FFmpeg de streaming."""
    print("🧪 Test de la commande FFmpeg de streaming...")

    # Vérifier si FFmpeg est installé
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            print("❌ FFmpeg n'est pas installé ou ne fonctionne pas")
            return False
        print("✅ FFmpeg est installé")
    except FileNotFoundError:
        print("❌ FFmpeg n'est pas installé")
        return False

    # Vérifier si setsid est disponible (Linux/Unix seulement)
    if not sys.platform.startswith('win'):
        try:
            result = subprocess.run(
                ["setsid", "--help"], capture_output=True, text=True, timeout=5
            )
            print("✅ setsid est disponible")
        except FileNotFoundError:
            print("❌ setsid n'est pas disponible")
            return False
    else:
        print("✅ Windows détecté - setsid non nécessaire")

    # Créer un fichier vidéo de test si nécessaire
    test_video = "test_video.mp4"
    if not os.path.exists(test_video):
        print("📹 Création d'un fichier vidéo de test...")
        create_cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=5:size=640x360:rate=1",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1000:duration=5",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-y",
            test_video,
        ]

        result = subprocess.run(create_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"❌ Erreur lors de la création du fichier de test: {result.stderr}")
            return False
        print("✅ Fichier vidéo de test créé")

    # URL de test (remplacer par une vraie clé de streaming pour tester)
    test_rtmp_url = "rtmp://a.rtmp.youtube.com/live2/test-key"

    # Commande FFmpeg exacte comme spécifiée (sans setsid pour Windows)
    if sys.platform.startswith('win'):
        ffmpeg_cmd = [
            "ffmpeg",
            "-re",  # Lire à la vitesse réelle
            "-stream_loop",
            "-1",  # Boucle infinie
            "-i",
            test_video,  # Fichier d'entrée
            "-c:v",
            "libx264",  # Codec vidéo H.264
            "-preset",
            "ultrafast",  # Preset rapide pour streaming
            "-b:v",
            "500k",  # Bitrate vidéo 500k
            "-maxrate",
            "800k",  # Bitrate maximum 800k
            "-bufsize",
            "1200k",  # Taille du buffer 1200k
            "-s",
            "640x360",  # Résolution 640x360
            "-g",
            "60",  # GOP size 60
            "-keyint_min",
            "60",  # Keyframe minimum 60
            "-c:a",
            "aac",  # Codec audio AAC
            "-b:a",
            "96k",  # Bitrate audio 96k
            "-f",
            "flv",  # Format de sortie FLV
            "-reconnect",
            "1",  # Activer la reconnexion
            "-reconnect_streamed",
            "1",  # Reconnexion pour streaming
            "-reconnect_delay_max",
            "2",  # Délai max de reconnexion 2s
            test_rtmp_url,  # URL de destination RTMP
        ]
    else:
        # Linux/Unix: utiliser setsid
        ffmpeg_cmd = [
            "setsid",
            "ffmpeg",
            "-re",  # Lire à la vitesse réelle
            "-stream_loop",
            "-1",  # Boucle infinie
            "-i",
            test_video,  # Fichier d'entrée
            "-c:v",
            "libx264",  # Codec vidéo H.264
            "-preset",
            "ultrafast",  # Preset rapide pour streaming
            "-b:v",
            "500k",  # Bitrate vidéo 500k
            "-maxrate",
            "800k",  # Bitrate maximum 800k
            "-bufsize",
            "1200k",  # Taille du buffer 1200k
            "-s",
            "640x360",  # Résolution 640x360
            "-g",
            "60",  # GOP size 60
            "-keyint_min",
            "60",  # Keyframe minimum 60
            "-c:a",
            "aac",  # Codec audio AAC
            "-b:a",
            "96k",  # Bitrate audio 96k
            "-f",
            "flv",  # Format de sortie FLV
            "-reconnect",
            "1",  # Activer la reconnexion
            "-reconnect_streamed",
            "1",  # Reconnexion pour streaming
            "-reconnect_delay_max",
            "2",  # Délai max de reconnexion 2s
            test_rtmp_url,  # URL de destination RTMP
        ]

    print("\n🔧 Commande FFmpeg:")
    print(" ".join(ffmpeg_cmd))

    print("\n⚠️  ATTENTION: Cette commande va essayer de se connecter à YouTube!")
    print("Pour un test sans connexion réelle, utilisez une URL de test locale.")

    confirm = input("\nVoulez-vous continuer avec un test réel ? (y/N): ")
    if confirm.lower() != "y":
        print("Test annulé")
        return True

    print("\n🚀 Lancement du test de streaming...")
    print("Le processus va tourner pendant 10 secondes puis s'arrêter automatiquement")

    # Lancer le processus
    try:
        if sys.platform.startswith('win'):
            # Windows: utiliser subprocess.Popen avec creationflags
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            # Linux/Unix: utiliser subprocess.Popen normal
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True  # Créer une nouvelle session
            )

        print(f"✅ Processus FFmpeg démarré avec PID: {process.pid}")
        print("⏳ Attente de 10 secondes...")

        # Attendre 10 secondes
        time.sleep(10)

        # Arrêter le processus
        print("🛑 Arrêt du processus...")
        if sys.platform.startswith('win'):
            # Windows: utiliser taskkill
            subprocess.run(
                ["taskkill", "/F", "/PID", str(process.pid)],
                capture_output=True,
                timeout=10
            )
        else:
            # Linux/Unix: utiliser os.kill
            os.kill(process.pid, 15)  # SIGTERM
            time.sleep(2)
            try:
                os.kill(process.pid, 0)  # Test si le processus existe
                os.kill(process.pid, 9)  # SIGKILL si nécessaire
            except OSError:
                pass

        print("✅ Test terminé avec succès!")
        return True

    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False


if __name__ == "__main__":
    test_ffmpeg_command()
