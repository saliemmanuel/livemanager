#!/bin/bash

echo "=== Déploiement des nouvelles fonctionnalités de gestion des clés de streaming ==="
echo

# Variables
PROJECT_DIR="/var/www/livemanager"
VENV_DIR="$PROJECT_DIR/venv"

echo "1. Arrêt du service Django..."
systemctl stop livemanager

echo "2. Sauvegarde de la base de données..."
cd $PROJECT_DIR
source $VENV_DIR/bin/activate
python3 manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json

echo "3. Pull des derniers changements..."
git pull origin main

echo "4. Installation des nouvelles dépendances..."
source $VENV_DIR/bin/activate
pip install -r requirements.txt

echo "5. Application des migrations..."
python3 manage.py migrate

echo "6. Collecte des fichiers statiques..."
python3 manage.py collectstatic --noinput

echo "7. Redémarrage du service Django..."
systemctl start livemanager

echo "8. Vérification du statut du service..."
systemctl status livemanager --no-pager

echo "9. Test de l'application..."
sleep 5
curl -I http://localhost:8000/profile/ || echo "Erreur lors du test de l'application"

echo
echo "=== Déploiement terminé ==="
echo
echo "Nouvelles fonctionnalités disponibles :"
echo "- Page de profil utilisateur : /profile/"
echo "- Ajout de clés de streaming : /add-stream-key/"
echo "- Modification de clés : /edit-stream-key/<id>/"
echo "- Suppression de clés : /delete-stream-key/<id>/"
echo "- Activation/désactivation : /toggle-stream-key/<id>/"
echo
echo "Les utilisateurs peuvent maintenant :"
echo "1. Aller dans leur profil"
echo "2. Configurer leurs clés de streaming"
echo "3. Choisir une clé lors de la création d'un live"
echo 