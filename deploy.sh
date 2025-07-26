#!/bin/bash

# Script de déploiement pour LiveManager sur VPS Hostinger
# Usage: ./deploy.sh [production|staging]

set -e  # Arrêter en cas d'erreur

# Configuration
ENVIRONMENT=${1:-production}
PROJECT_DIR="/var/www/livemanager"
BACKUP_DIR="/var/backups/livemanager"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
GIT_REPO="https://github.com/votre-username/livemanager.git"
BRANCH="main"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERREUR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCÈS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[ATTENTION]${NC} $1"
}

# Vérifier si on est root
if [[ $EUID -eq 0 ]]; then
   error "Ce script ne doit pas être exécuté en tant que root"
fi

log "🚀 Démarrage du déploiement LiveManager en mode $ENVIRONMENT"

# Créer les répertoires si ils n'existent pas
log "📁 Création des répertoires..."
sudo mkdir -p $PROJECT_DIR
sudo mkdir -p $BACKUP_DIR
sudo mkdir -p /var/log/livemanager

# Sauvegarder l'ancienne version
if [ -d "$PROJECT_DIR" ] && [ "$(ls -A $PROJECT_DIR)" ]; then
    log "💾 Création du backup..."
    sudo tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" -C $PROJECT_DIR .
    success "Backup créé: backup_$TIMESTAMP.tar.gz"
fi

# Aller dans le répertoire du projet
cd $PROJECT_DIR

# Arrêter les services
log "⏹️ Arrêt des services..."
sudo systemctl stop livemanager || true
sudo systemctl stop livemanager-celery || true
sudo systemctl stop nginx || true

# Nettoyer le répertoire
log "🧹 Nettoyage du répertoire..."
sudo rm -rf *

# Cloner le nouveau code
log "📥 Clonage du code depuis Git..."
sudo git clone -b $BRANCH $GIT_REPO .

# Créer l'environnement virtuel
log "🐍 Configuration de l'environnement Python..."
if [ ! -d "venv" ]; then
    sudo python3 -m venv venv
fi
sudo chown -R $USER:$USER venv

# Activer l'environnement virtuel et installer les dépendances
log "📦 Installation des dépendances..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Configurer les variables d'environnement
log "⚙️ Configuration des variables d'environnement..."
if [ ! -f ".env" ]; then
    sudo cp .env.example .env
    warning "Fichier .env créé depuis .env.example. Veuillez le configurer manuellement."
fi

# Appliquer les migrations
log "🗄️ Application des migrations..."
python manage.py migrate

# Collecter les fichiers statiques
log "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Créer le superuser si il n'existe pas
log "👤 Vérification du superuser..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@livemanager.com', 'admin123') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell

# Configurer les permissions
log "🔐 Configuration des permissions..."
sudo chown -R www-data:www-data $PROJECT_DIR
sudo chmod -R 755 $PROJECT_DIR
sudo chmod 664 $PROJECT_DIR/.env

# Installer et configurer les services systemd
log "🔧 Configuration des services systemd..."

# Service principal Django
sudo tee /etc/systemd/system/livemanager.service > /dev/null <<EOF
[Unit]
Description=LiveManager Django Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --workers 3 --bind unix:$PROJECT_DIR/livemanager.sock livemanager.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Service Celery (optionnel)
sudo tee /etc/systemd/system/livemanager-celery.service > /dev/null <<EOF
[Unit]
Description=LiveManager Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/celery -A livemanager worker --loglevel=info --detach
ExecStop=$PROJECT_DIR/venv/bin/celery control shutdown
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Recharger systemd
sudo systemctl daemon-reload

# Configurer Nginx
log "🌐 Configuration de Nginx..."
sudo tee /etc/nginx/sites-available/livemanager > /dev/null <<EOF
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;

    # Redirection HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com www.votre-domaine.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Logs
    access_log /var/log/nginx/livemanager_access.log;
    error_log /var/log/nginx/livemanager_error.log;

    # Static files
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias $PROJECT_DIR/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Django application
    location / {
        proxy_pass http://unix:$PROJECT_DIR/livemanager.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
}
EOF

# Activer le site Nginx
sudo ln -sf /etc/nginx/sites-available/livemanager /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Tester la configuration Nginx
sudo nginx -t

# Démarrer les services
log "🚀 Démarrage des services..."
sudo systemctl start livemanager
sudo systemctl enable livemanager
sudo systemctl start nginx
sudo systemctl enable nginx

# Démarrer Celery si configuré
if grep -q "celery" requirements.txt; then
    sudo systemctl start livemanager-celery
    sudo systemctl enable livemanager-celery
fi

# Vérifier le statut des services
log "📊 Vérification du statut des services..."
sudo systemctl status livemanager --no-pager -l
sudo systemctl status nginx --no-pager -l

# Nettoyer les anciens backups (garder seulement les 5 plus récents)
log "🧹 Nettoyage des anciens backups..."
cd $BACKUP_DIR
ls -t *.tar.gz | tail -n +6 | xargs -r rm --

success "🎉 Déploiement terminé avec succès!"
log "🌐 Votre application est accessible sur: https://votre-domaine.com"
log "👤 Superuser: admin / admin123"
log "📁 Répertoire du projet: $PROJECT_DIR"
log "📋 Logs: /var/log/livemanager/"

# Afficher les commandes utiles
echo ""
echo "🔧 Commandes utiles:"
echo "  sudo systemctl status livemanager"
echo "  sudo systemctl restart livemanager"
echo "  sudo journalctl -u livemanager -f"
echo "  sudo nginx -t"
echo "  sudo systemctl restart nginx" 