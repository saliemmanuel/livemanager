#!/bin/bash

echo "=== Correction de l'erreur FFmpeg sur Ubuntu ==="
echo

# Variables
PROJECT_DIR="/var/www/livemanager"
VENV_DIR="$PROJECT_DIR/venv"

echo "1. Installation de FFmpeg..."
apt update
apt install -y ffmpeg

echo "2. Vérification de l'installation FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg installé avec succès !"
    FFMPEG_PATH=$(which ffmpeg)
    echo "Chemin: $FFMPEG_PATH"
else
    echo "❌ Erreur: FFmpeg n'a pas pu être installé"
    exit 1
fi

echo "3. Arrêt du service Django..."
systemctl stop livemanager

echo "4. Sauvegarde des modifications locales..."
cd $PROJECT_DIR
git stash

echo "5. Pull des dernières corrections..."
git pull origin main

echo "6. Configuration du chemin FFmpeg dans Django..."
# Ajouter la configuration FFmpeg dans settings.py
if ! grep -q "FFMPEG_PATH" livemanager/settings.py; then
    echo "" >> livemanager/settings.py
    echo "# Configuration FFmpeg" >> livemanager/settings.py
    echo "FFMPEG_PATH = '$FFMPEG_PATH'" >> livemanager/settings.py
    echo "✅ Configuration FFmpeg ajoutée"
else
    # Mettre à jour la configuration existante
    sed -i "s|FFMPEG_PATH = .*|FFMPEG_PATH = '$FFMPEG_PATH'|" livemanager/settings.py
    echo "✅ Configuration FFmpeg mise à jour"
fi

echo "7. Application des migrations..."
source $VENV_DIR/bin/activate
python3 manage.py migrate

echo "8. Collecte des fichiers statiques..."
python3 manage.py collectstatic --noinput

echo "9. Redémarrage du service Django..."
systemctl start livemanager

echo "10. Vérification du statut du service..."
systemctl status livemanager --no-pager

echo "11. Test de FFmpeg..."
ffmpeg -f lavfi -i testsrc=duration=1:size=320x240:rate=1 -f null - 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ FFmpeg fonctionne correctement"
else
    echo "❌ Erreur lors du test de FFmpeg"
fi

echo "12. Test de l'application..."
sleep 5
curl -I http://localhost:8000/ || echo "Erreur lors du test de l'application"

echo
echo "=== Correction terminée ==="
echo
echo "FFmpeg est maintenant installé et configuré."
echo "Le chemin configuré est: $FFMPEG_PATH"
echo
echo "Les corrections apportées :"
echo "- Installation de FFmpeg sur Ubuntu"
echo "- Configuration du chemin FFmpeg dans Django"
echo "- Mise à jour du code pour utiliser le bon chemin"
echo
echo "Pour tester :"
echo "1. Allez sur votre site web"
echo "2. Créez un nouveau live"
echo "3. Lancez le live"
echo "4. L'erreur 'ffmpeg not found' ne devrait plus apparaître" 