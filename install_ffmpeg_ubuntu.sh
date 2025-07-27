#!/bin/bash

echo "=== Installation de FFmpeg sur Ubuntu ==="
echo

# Mettre à jour les paquets
echo "1. Mise à jour des paquets système..."
apt update

# Installer FFmpeg
echo "2. Installation de FFmpeg..."
apt install -y ffmpeg

# Vérifier l'installation
echo "3. Vérification de l'installation..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg installé avec succès !"
    ffmpeg -version | head -n 1
    echo "Chemin: $(which ffmpeg)"
else
    echo "❌ Erreur: FFmpeg n'a pas pu être installé"
    exit 1
fi

# Vérifier le chemin par défaut
echo "4. Vérification du chemin par défaut..."
if [ -f "/usr/bin/ffmpeg" ]; then
    echo "✅ FFmpeg trouvé dans /usr/bin/ffmpeg"
    FFMPEG_PATH="/usr/bin/ffmpeg"
elif [ -f "/usr/local/bin/ffmpeg" ]; then
    echo "✅ FFmpeg trouvé dans /usr/local/bin/ffmpeg"
    FFMPEG_PATH="/usr/local/bin/ffmpeg"
else
    echo "⚠️  FFmpeg installé mais chemin non standard"
    FFMPEG_PATH=$(which ffmpeg)
fi

echo
echo "=== Configuration Django ==="
echo

# Aller dans le répertoire du projet
cd /var/www/livemanager

# Créer un fichier de configuration local pour FFmpeg
echo "5. Configuration du chemin FFmpeg dans Django..."
cat > livemanager/ffmpeg_config.py << EOF
# Configuration FFmpeg pour Ubuntu
FFMPEG_PATH = "$FFMPEG_PATH"
EOF

# Modifier settings.py pour utiliser le bon chemin
echo "6. Mise à jour des paramètres Django..."
if grep -q "FFMPEG_PATH" livemanager/settings.py; then
    # Remplacer la ligne existante
    sed -i "s|FFMPEG_PATH = .*|FFMPEG_PATH = '$FFMPEG_PATH'|" livemanager/settings.py
else
    # Ajouter la ligne
    echo "" >> livemanager/settings.py
    echo "# Configuration FFmpeg" >> livemanager/settings.py
    echo "FFMPEG_PATH = '$FFMPEG_PATH'" >> livemanager/settings.py
fi

echo "7. Redémarrage du service Django..."
systemctl restart livemanager

echo "8. Vérification du statut du service..."
systemctl status livemanager --no-pager

echo
echo "=== Test de FFmpeg ==="
echo

# Test simple de FFmpeg
echo "9. Test de FFmpeg..."
ffmpeg -f lavfi -i testsrc=duration=1:size=320x240:rate=1 -f null - 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ FFmpeg fonctionne correctement"
else
    echo "❌ Erreur lors du test de FFmpeg"
fi

echo
echo "=== Installation terminée ==="
echo
echo "FFmpeg est maintenant installé et configuré."
echo "Le chemin configuré est: $FFMPEG_PATH"
echo
echo "Pour tester le streaming :"
echo "1. Allez sur votre site web"
echo "2. Créez un nouveau live"
echo "3. Lancez le live"
echo "4. L'erreur 'ffmpeg not found' ne devrait plus apparaître" 