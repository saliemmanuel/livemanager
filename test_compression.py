#!/usr/bin/env python3
"""
🧪 Script de Test - Compression Vidéo LiveManager
Ce script teste le système de compression vidéo
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

def check_ffmpeg():
    """Vérifier que FFmpeg est installé et fonctionnel"""
    log("Vérification de FFmpeg...")
    
    try:
        # Vérifier la version
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            version = version_line.split(' ')[2]
            success(f"FFmpeg installé (version: {version})")
            return True
        else:
            error("FFmpeg ne répond pas correctement")
            return False
            
    except FileNotFoundError:
        error("FFmpeg n'est pas installé")
        return False
    except subprocess.TimeoutExpired:
        error("FFmpeg ne répond pas (timeout)")
        return False
    except Exception as e:
        error(f"Erreur lors de la vérification de FFmpeg: {e}")
        return False

def check_codecs():
    """Vérifier que les codecs nécessaires sont disponibles"""
    log("Vérification des codecs...")
    
    required_codecs = ['libx264', 'aac', 'libmp3lame']
    available_codecs = []
    
    try:
        result = subprocess.run(['ffmpeg', '-codecs'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            for codec in required_codecs:
                if codec in result.stdout:
                    available_codecs.append(codec)
                    success(f"Codec {codec} disponible")
                else:
                    warning(f"Codec {codec} manquant")
            
            if len(available_codecs) == len(required_codecs):
                success("Tous les codecs requis sont disponibles")
                return True
            else:
                warning(f"Seulement {len(available_codecs)}/{len(required_codecs)} codecs disponibles")
                return False
        else:
            error("Impossible de récupérer la liste des codecs")
            return False
            
    except Exception as e:
        error(f"Erreur lors de la vérification des codecs: {e}")
        return False

def create_test_video():
    """Créer une vidéo de test"""
    log("Création d'une vidéo de test...")
    
    try:
        # Créer un fichier temporaire pour la vidéo de test
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            test_video_path = temp_file.name
        
        # Créer une vidéo de test (5 secondes, 640x480, avec audio)
        cmd = [
            'ffmpeg', '-f', 'lavfi',
            '-i', 'testsrc=duration=5:size=640x480:rate=30',
            '-f', 'lavfi',
            '-i', 'sine=frequency=1000:duration=5',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'ultrafast',
            '-y',
            test_video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists(test_video_path):
            file_size = os.path.getsize(test_video_path)
            success(f"Vidéo de test créée ({file_size} bytes)")
            return test_video_path
        else:
            error(f"Échec de création de la vidéo de test: {result.stderr}")
            return None
            
    except Exception as e:
        error(f"Erreur lors de la création de la vidéo de test: {e}")
        return None

def test_compression(input_path):
    """Tester la compression vidéo"""
    log("Test de compression vidéo...")
    
    try:
        # Obtenir la taille du fichier original
        original_size = os.path.getsize(input_path)
        
        # Créer un fichier temporaire pour la sortie
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            output_path = temp_file.name
        
        # Commande de compression (similaire à celle utilisée dans l'app)
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'medium',
            '-crf', '23',
            '-movflags', '+faststart',
            '-y',
            output_path
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        end_time = time.time()
        
        if result.returncode == 0 and os.path.exists(output_path):
            compressed_size = os.path.getsize(output_path)
            compression_time = end_time - start_time
            
            # Calculer le ratio de compression
            if original_size > 0:
                compression_ratio = ((original_size - compressed_size) / original_size) * 100
                success(f"Compression réussie en {compression_time:.2f}s")
                success(f"Taille originale: {original_size} bytes")
                success(f"Taille compressée: {compressed_size} bytes")
                success(f"Ratio de compression: {compression_ratio:.1f}%")
                
                # Nettoyer
                os.unlink(output_path)
                return True
            else:
                error("Taille du fichier original invalide")
                return False
        else:
            error(f"Échec de la compression: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        error("Timeout lors de la compression")
        return False
    except Exception as e:
        error(f"Erreur lors du test de compression: {e}")
        return False

def test_django_integration():
    """Tester l'intégration avec Django"""
    log("Test de l'intégration Django...")
    
    try:
        # Vérifier que Django est installé
        import django
        success(f"Django installé (version: {django.get_version()})")
        
        # Vérifier que le projet est accessible
        project_dir = Path("/var/www/livemanager")
        if project_dir.exists():
            success("Répertoire du projet Django trouvé")
            
            # Vérifier manage.py
            manage_py = project_dir / "manage.py"
            if manage_py.exists():
                success("manage.py trouvé")
                
                # Test de configuration Django
                os.chdir(project_dir)
                result = subprocess.run(['python3', 'manage.py', 'check'], 
                                      capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    success("Configuration Django valide")
                    return True
                else:
                    warning(f"Problème de configuration Django: {result.stderr}")
                    return False
            else:
                warning("manage.py non trouvé")
                return False
        else:
            warning("Répertoire du projet Django non trouvé")
            return False
            
    except ImportError:
        error("Django n'est pas installé")
        return False
    except Exception as e:
        error(f"Erreur lors du test Django: {e}")
        return False

def main():
    """Fonction principale"""
    print("🧪 Test de Compression Vidéo - LiveManager")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Vérification de FFmpeg
    if check_ffmpeg():
        tests_passed += 1
    
    # Test 2: Vérification des codecs
    if check_codecs():
        tests_passed += 1
    
    # Test 3: Création d'une vidéo de test
    test_video = create_test_video()
    if test_video:
        tests_passed += 1
        
        # Test 4: Test de compression
        if test_compression(test_video):
            tests_passed += 1
        
        # Nettoyer la vidéo de test
        try:
            os.unlink(test_video)
        except:
            pass
    
    # Test 5: Intégration Django
    if test_django_integration():
        tests_passed += 1
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    if tests_passed == total_tests:
        success(f"Tous les tests sont passés ({tests_passed}/{total_tests})")
        print("\n🎉 Le système de compression vidéo est prêt !")
        print("📋 Prochaines étapes:")
        print("   1. Redémarrer le service Django: sudo systemctl restart livemanager")
        print("   2. Tester l'upload via l'interface web")
        print("   3. Vérifier les logs: sudo journalctl -u livemanager -f")
    else:
        error(f"Seulement {tests_passed}/{total_tests} tests sont passés")
        print("\n🔧 Actions recommandées:")
        print("   1. Installer FFmpeg: sudo ./install_ffmpeg.sh")
        print("   2. Vérifier les permissions: sudo chown -R www-data:www-data /var/www/livemanager")
        print("   3. Redémarrer les services: sudo systemctl restart livemanager nginx")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 