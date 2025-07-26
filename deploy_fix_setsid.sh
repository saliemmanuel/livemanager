#!/bin/bash

echo "=== Correction de l'erreur setsid sur le serveur de production ==="
echo

# Variables
PROJECT_DIR="/var/www/livemanager"
VENV_DIR="$PROJECT_DIR/venv"

echo "1. Arrêt du service Django..."
systemctl stop livemanager

echo "2. Sauvegarde des modifications locales..."
cd $PROJECT_DIR
git stash

echo "3. Pull des dernières corrections..."
git pull origin main

echo "4. Application des migrations..."
source $VENV_DIR/bin/activate
python3 manage.py migrate

echo "5. Collecte des fichiers statiques..."
python3 manage.py collectstatic --noinput

echo "6. Redémarrage du service Django..."
systemctl start livemanager

echo "7. Vérification du statut du service..."
systemctl status livemanager --no-pager

echo "8. Test de l'application..."
sleep 5
curl -I http://localhost:8000/ || echo "Erreur lors du test de l'application"

echo
echo "=== Correction terminée ==="
echo
echo "Les corrections apportées :"
echo "- Suppression de 'setsid' des commandes FFmpeg"
echo "- Adaptation pour compatibilité Windows/Linux"
echo "- Gestion des processus selon la plateforme"
echo
echo "L'erreur 'setsid' ne devrait plus apparaître lors du lancement des lives."
echo
echo "Pour tester :"
echo "1. Allez sur votre site web"
echo "2. Créez un nouveau live"
echo "3. Lancez le live"
echo "4. L'erreur setsid ne devrait plus apparaître" 