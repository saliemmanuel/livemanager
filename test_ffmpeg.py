#!/usr/bin/env python3
"""
Script de test pour vérifier l'installation de FFmpeg
"""

import subprocess
import sys
import os

def test_ffmpeg():
    """Teste si FFmpeg est installé et fonctionnel."""
    print("🔍 Test de l'installation de FFmpeg...")
    
    try:
        # Test de la commande ffmpeg
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ FFmpeg est installé et fonctionnel")
            print(f"Version: {result.stdout.split('ffmpeg version')[1].split()[0]}")
            return True
        else:
            print("❌ FFmpeg retourne une erreur")
            print(f"Erreur: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ FFmpeg n'est pas installé ou n'est pas dans le PATH")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Timeout lors du test de FFmpeg")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test de FFmpeg: {e}")
        return False

def test_ffmpeg_processing():
    """Teste le traitement vidéo avec FFmpeg."""
    print("\n🔍 Test du traitement vidéo...")
    
    # Créer un fichier vidéo de test simple
    test_input = "test_input.mp4"
    test_output = "test_output.mp4"
    
    try:
        # Créer une vidéo de test avec FFmpeg
        create_cmd = [
            "ffmpeg", "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=1",
            "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
            "-c:v", "libx264", "-c:a", "aac", "-y", test_input
        ]
        
        print("Création d'une vidéo de test...")
        result = subprocess.run(create_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"❌ Erreur lors de la création de la vidéo de test: {result.stderr}")
            return False
        
        # Traiter la vidéo de test
        process_cmd = [
            "ffmpeg", "-i", test_input,
            "-c:v", "libx264", "-c:a", "aac",
            "-preset", "medium", "-crf", "23",
            "-movflags", "+faststart", "-y", test_output
        ]
        
        print("Traitement de la vidéo de test...")
        result = subprocess.run(process_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Traitement vidéo réussi")
            
            # Nettoyer les fichiers de test
            if os.path.exists(test_input):
                os.remove(test_input)
            if os.path.exists(test_output):
                os.remove(test_output)
            
            return True
        else:
            print(f"❌ Erreur lors du traitement: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test de traitement: {e}")
        return False

def main():
    """Fonction principale."""
    print("🚀 Test de l'environnement FFmpeg pour LiveManager\n")
    
    # Test de base
    if not test_ffmpeg():
        print("\n💡 Solutions possibles:")
        print("1. Installer FFmpeg: sudo apt update && sudo apt install ffmpeg")
        print("2. Vérifier que FFmpeg est dans le PATH")
        print("3. Redémarrer le service Django après installation")
        sys.exit(1)
    
    # Test de traitement
    if not test_ffmpeg_processing():
        print("\n💡 Le traitement vidéo échoue. Vérifiez:")
        print("1. Les permissions d'écriture dans le répertoire")
        print("2. L'espace disque disponible")
        print("3. Les codecs installés")
        sys.exit(1)
    
    print("\n🎉 Tous les tests sont passés ! FFmpeg est prêt pour LiveManager.")

if __name__ == "__main__":
    main() 