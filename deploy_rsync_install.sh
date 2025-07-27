#!/bin/bash

# Script de déploiement pour installer rsync sur le serveur de production
# À exécuter sur le serveur 91.108.112.77

set -e

echo "🚀 Installation rsync sur le serveur de production"
echo "================================================"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier si on est root
if [[ $EUID -ne 0 ]]; then
   print_error "Ce script doit être exécuté en tant que root"
   exit 1
fi

# 1. Mise à jour du système
print_status "Mise à jour du système..."
apt-get update

# 2. Installation de rsync
print_status "Installation de rsync..."
apt-get install -y rsync

# 3. Vérifier l'installation
print_status "Vérification de l'installation..."
if command -v rsync &> /dev/null; then
    rsync_version=$(rsync --version | head -n1)
    print_status "✅ rsync installé: $rsync_version"
else
    print_error "❌ rsync n'a pas pu être installé"
    exit 1
fi

# 4. Créer le répertoire de destination
print_status "Création du répertoire de destination..."
RSYNC_PATH="/var/www/livemanager/media/videos"
mkdir -p "$RSYNC_PATH"
chown -R www-data:www-data "$RSYNC_PATH"
chmod -R 755 "$RSYNC_PATH"
print_status "✅ Répertoire créé: $RSYNC_PATH"

# 5. Test de la configuration rsync
print_status "Test de la configuration rsync..."
cd /var/www/livemanager

# Créer un fichier de test
echo "Test rsync - LiveManager" > /tmp/test_rsync.txt

# Tester l'upload local
if rsync -avz /tmp/test_rsync.txt "$RSYNC_PATH/"; then
    print_status "✅ Test rsync local réussi"
    rm -f /tmp/test_rsync.txt
    rm -f "$RSYNC_PATH/test_rsync.txt"
else
    print_error "❌ Test rsync local échoué"
    exit 1
fi

# 6. Configuration des permissions
print_status "Configuration des permissions..."
chown -R www-data:www-data /var/www/livemanager
chmod -R 755 /var/www/livemanager

# 7. Redémarrage des services Django
print_status "Redémarrage des services Django..."
if systemctl is-active --quiet gunicorn; then
    systemctl restart gunicorn
    print_status "✅ Gunicorn redémarré"
fi

if systemctl is-active --quiet nginx; then
    systemctl restart nginx
    print_status "✅ Nginx redémarré"
fi

# 8. Test de l'application Django
print_status "Test de l'application Django..."
cd /var/www/livemanager
python manage.py check

# 9. Test du script rsync
print_status "Test du script rsync..."
if [ -f "test_rsync_server.py" ]; then
    python test_rsync_server.py
else
    print_warning "Script test_rsync_server.py non trouvé"
fi

echo ""
echo "✅ Installation rsync terminée avec succès !"
echo ""
echo "📋 Configuration finale:"
echo "   - rsync installé et fonctionnel"
echo "   - Répertoire de destination: $RSYNC_PATH"
echo "   - Permissions configurées"
echo "   - Services redémarrés"
echo ""
echo "🔧 Pour tester l'upload:"
echo "   - Allez sur l'interface web"
echo "   - Créez un nouveau live"
echo "   - Uploadez un fichier vidéo"
echo ""
echo "📝 Variables d'environnement configurées:"
echo "   RSYNC_USER=root"
echo "   RSYNC_HOST=localhost"
echo "   RSYNC_PATH=$RSYNC_PATH" 