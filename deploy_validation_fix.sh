#!/bin/bash

echo "=== Correction du problème de validation du compte utilisateur ==="
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
echo "- Correction de la vue dashboard pour passer les bonnes variables"
echo "- Ajout d'une vérification automatique du statut d'approbation"
echo "- Amélioration de la fonction approve_user"
echo "- Ajout d'une vue AJAX pour vérifier le statut en temps réel"
echo
echo "Maintenant :"
echo "1. Quand un admin approuve un utilisateur, le statut sera mis à jour"
echo "2. L'utilisateur verra automatiquement le changement sur son dashboard"
echo "3. La page se rafraîchira automatiquement si le statut change"
echo
echo "Pour tester :"
echo "1. Connectez-vous en tant qu'admin"
echo "2. Allez dans 'Gestion des utilisateurs'"
echo "3. Approuvez un utilisateur"
echo "4. L'utilisateur verra immédiatement le changement sur son dashboard" 