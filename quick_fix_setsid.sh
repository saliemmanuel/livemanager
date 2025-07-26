#!/bin/bash

echo "🔧 Correction rapide de l'erreur setsid..."

# Aller dans le répertoire du projet
cd /var/www/livemanager

# Arrêter le service
echo "1. Arrêt du service..."
systemctl stop livemanager

# Sauvegarder les modifications locales
echo "2. Sauvegarde des modifications..."
git stash

# Récupérer les dernières corrections
echo "3. Récupération des corrections..."
git pull origin main

# Redémarrer le service
echo "4. Redémarrage du service..."
systemctl start livemanager

# Vérifier le statut
echo "5. Vérification du statut..."
systemctl status livemanager --no-pager

echo "✅ Correction terminée !"
echo "L'erreur setsid ne devrait plus apparaître." 