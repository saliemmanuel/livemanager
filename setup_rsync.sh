#!/bin/bash

# Script d'installation et configuration rsync pour LiveManager
# À exécuter sur le serveur de production

set -e

echo "🚀 Installation et configuration rsync pour LiveManager"
echo "=================================================="

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
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

# 1. Installation de rsync
print_status "Installation de rsync..."
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    apt-get update
    apt-get install -y rsync
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    yum install -y rsync
elif command -v dnf &> /dev/null; then
    # Fedora
    dnf install -y rsync
else
    print_error "Gestionnaire de paquets non reconnu"
    exit 1
fi

# 2. Vérifier l'installation
print_status "Vérification de l'installation..."
if command -v rsync &> /dev/null; then
    rsync_version=$(rsync --version | head -n1)
    print_status "rsync installé: $rsync_version"
else
    print_error "rsync n'a pas pu être installé"
    exit 1
fi

# 3. Créer le répertoire de destination
print_status "Création du répertoire de destination..."
RSYNC_PATH="/var/www/livemanager/media/videos"
mkdir -p "$RSYNC_PATH"
chown -R www-data:www-data "$RSYNC_PATH"
chmod -R 755 "$RSYNC_PATH"
print_status "Répertoire créé: $RSYNC_PATH"

# 4. Configuration SSH pour rsync (optionnel)
print_status "Configuration SSH pour rsync..."
if [ ! -f ~/.ssh/id_rsa ]; then
    print_warning "Aucune clé SSH trouvée. Génération d'une nouvelle clé..."
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
    print_status "Clé SSH générée"
fi

# 5. Test de la configuration
print_status "Test de la configuration rsync..."
cd /var/www/livemanager

# Créer un fichier de test
echo "Test rsync - LiveManager" > /tmp/test_rsync.txt

# Tester l'upload local
if rsync -avz /tmp/test_rsync.txt "$RSYNC_PATH/"; then
    print_status "Test rsync local réussi"
    rm -f /tmp/test_rsync.txt
    rm -f "$RSYNC_PATH/test_rsync.txt"
else
    print_error "Test rsync local échoué"
    exit 1
fi

# 6. Configuration des permissions
print_status "Configuration des permissions..."
chown -R www-data:www-data /var/www/livemanager
chmod -R 755 /var/www/livemanager

# 7. Configuration du firewall (optionnel)
print_status "Configuration du firewall pour rsync..."
if command -v ufw &> /dev/null; then
    # Ubuntu/Debian avec ufw
    ufw allow 873/tcp
    print_status "Port 873 (rsync) ouvert dans ufw"
elif command -v firewall-cmd &> /dev/null; then
    # CentOS/RHEL avec firewalld
    firewall-cmd --permanent --add-service=rsync
    firewall-cmd --reload
    print_status "Service rsync ajouté au firewall"
fi

# 8. Configuration dans Django settings
print_status "Configuration Django..."
if [ -f /var/www/livemanager/livemanager/settings.py ]; then
    # Vérifier si la configuration rsync existe déjà
    if ! grep -q "RSYNC_" /var/www/livemanager/livemanager/settings.py; then
        cat >> /var/www/livemanager/livemanager/settings.py << EOF

# Rsync settings for file uploads
RSYNC_USER = config("RSYNC_USER", default="root")
RSYNC_HOST = config("RSYNC_HOST", default="localhost")
RSYNC_PATH = config("RSYNC_PATH", default="/var/www/livemanager/media/videos/")
EOF
        print_status "Configuration rsync ajoutée à Django settings"
    else
        print_warning "Configuration rsync déjà présente dans Django settings"
    fi
else
    print_warning "Fichier Django settings non trouvé"
fi

# 9. Redémarrage des services
print_status "Redémarrage des services..."
if systemctl is-active --quiet gunicorn; then
    systemctl restart gunicorn
    print_status "Gunicorn redémarré"
fi

if systemctl is-active --quiet nginx; then
    systemctl restart nginx
    print_status "Nginx redémarré"
fi

echo ""
echo "✅ Installation et configuration rsync terminées !"
echo ""
echo "📋 Configuration finale:"
echo "   - rsync installé et fonctionnel"
echo "   - Répertoire de destination: $RSYNC_PATH"
echo "   - Permissions configurées"
echo "   - Firewall configuré"
echo ""
echo "🔧 Pour tester depuis votre machine locale:"
echo "   python test_rsync.py"
echo ""
echo "📝 Variables d'environnement à configurer:"
echo "   RSYNC_USER=root"
echo "   RSYNC_HOST=$(hostname -I | awk '{print $1}')"
echo "   RSYNC_PATH=$RSYNC_PATH" 