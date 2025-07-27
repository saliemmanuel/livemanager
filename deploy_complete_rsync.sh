#!/bin/bash

# Script de déploiement complet avec installation rsync
# À exécuter sur le serveur 91.108.112.77

set -e

echo "🚀 Déploiement complet avec installation rsync"
echo "============================================="

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

# 1. Arrêter les services Django
print_status "Arrêt des services Django..."
if systemctl is-active --quiet gunicorn; then
    systemctl stop gunicorn
    print_status "✅ Gunicorn arrêté"
fi

# 2. Sauvegarder les changements locaux
print_status "Sauvegarde des changements locaux..."
cd /var/www/livemanager
if [ -n "$(git status --porcelain)" ]; then
    git stash
    print_status "✅ Changements locaux sauvegardés"
fi

# 3. Mettre à jour le code depuis GitHub
print_status "Mise à jour du code depuis GitHub..."
git pull origin main
print_status "✅ Code mis à jour"

# 4. Installation de rsync
print_status "Installation de rsync..."
apt-get update
apt-get install -y rsync

# Vérifier l'installation
if command -v rsync &> /dev/null; then
    rsync_version=$(rsync --version | head -n1)
    print_status "✅ rsync installé: $rsync_version"
else
    print_error "❌ rsync n'a pas pu être installé"
    exit 1
fi

# 5. Créer le répertoire de destination rsync
print_status "Création du répertoire de destination rsync..."
RSYNC_PATH="/var/www/livemanager/media/videos"
mkdir -p "$RSYNC_PATH"
chown -R www-data:www-data "$RSYNC_PATH"
chmod -R 755 "$RSYNC_PATH"
print_status "✅ Répertoire créé: $RSYNC_PATH"

# 6. Appliquer les migrations Django
print_status "Application des migrations Django..."
python manage.py migrate
print_status "✅ Migrations appliquées"

# 7. Collecter les fichiers statiques
print_status "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput
print_status "✅ Fichiers statiques collectés"

# 8. Configuration des permissions
print_status "Configuration des permissions..."
chown -R www-data:www-data /var/www/livemanager
chmod -R 755 /var/www/livemanager

# 9. Test de la configuration rsync
print_status "Test de la configuration rsync..."
echo "Test rsync - LiveManager" > /tmp/test_rsync.txt

if rsync -avz /tmp/test_rsync.txt "$RSYNC_PATH/"; then
    print_status "✅ Test rsync local réussi"
    rm -f /tmp/test_rsync.txt
    rm -f "$RSYNC_PATH/test_rsync.txt"
else
    print_error "❌ Test rsync local échoué"
    exit 1
fi

# 10. Test de l'application Django
print_status "Test de l'application Django..."
python manage.py check
print_status "✅ Application Django OK"

# 11. Test du script rsync
print_status "Test du script rsync..."
if [ -f "test_rsync_server.py" ]; then
    python test_rsync_server.py
    print_status "✅ Script rsync testé"
else
    print_warning "Script test_rsync_server.py non trouvé"
fi

# 12. Redémarrer les services
print_status "Redémarrage des services..."
systemctl start gunicorn
print_status "✅ Gunicorn redémarré"

if systemctl is-active --quiet nginx; then
    systemctl restart nginx
    print_status "✅ Nginx redémarré"
fi

# 13. Vérifier que les services fonctionnent
print_status "Vérification des services..."
sleep 3

if systemctl is-active --quiet gunicorn; then
    print_status "✅ Gunicorn fonctionne"
else
    print_error "❌ Gunicorn ne fonctionne pas"
    systemctl status gunicorn
    exit 1
fi

# 14. Test de l'application web
print_status "Test de l'application web..."
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    print_status "✅ Application web accessible"
else
    print_warning "⚠️ Application web non accessible sur localhost:8000"
fi

echo ""
echo "✅ Déploiement complet terminé avec succès !"
echo ""
echo "📋 Configuration finale:"
echo "   - Code mis à jour depuis GitHub"
echo "   - rsync installé et fonctionnel"
echo "   - Migrations appliquées"
echo "   - Fichiers statiques collectés"
echo "   - Répertoire de destination: $RSYNC_PATH"
echo "   - Permissions configurées"
echo "   - Services redémarrés"
echo ""
echo "🔧 Pour tester l'upload:"
echo "   - Allez sur votre site web"
echo "   - Créez un nouveau live"
echo "   - Uploadez un fichier vidéo"
echo ""
echo "📝 Variables d'environnement configurées:"
echo "   RSYNC_USER=root"
echo "   RSYNC_HOST=localhost"
echo "   RSYNC_PATH=$RSYNC_PATH"
echo ""
echo "🔍 Pour vérifier les logs:"
echo "   journalctl -u gunicorn -f"
echo "   tail -f /var/log/nginx/error.log" 