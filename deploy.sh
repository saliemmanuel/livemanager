#!/bin/bash

# 🚀 Script de Déploiement Complet LiveManager
# Ce script déploie automatiquement votre site en ligne
# Usage: sudo ./deploy.sh

set -e  # Arrêter en cas d'erreur

# Variables de configuration
PROJECT_DIR="/var/www/livemanager"
BACKUP_DIR="/var/backups/livemanager"
REPO_URL="https://github.com/saliemmanuel/livemanager.git"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DOMAIN=""  # Sera demandé à l'utilisateur

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

step() {
    echo -e "${PURPLE}🔧 $1${NC}"
}

# Vérifier si on est root
if [ "$EUID" -ne 0 ]; then
    error "Ce script doit être exécuté en tant que root (sudo ./deploy.sh)"
    exit 1
fi

# Bannière de démarrage
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🚀 LiveManager Deployer                   ║"
echo "║                Script de déploiement automatique             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Demander le domaine
echo -e "${YELLOW}🌐 Configuration du domaine${NC}"
read -p "Entrez votre nom de domaine (ex: mon-site.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    warning "Aucun domaine saisi, utilisation de l'IP du serveur"
    DOMAIN=$(hostname -I | awk '{print $1}')
fi

log "🚀 Démarrage du déploiement LiveManager pour $DOMAIN..."

# ============================================================================
# ÉTAPE 1: MISE À JOUR DU SYSTÈME
# ============================================================================
step "Étape 1/8: Mise à jour du système"
log "📦 Mise à jour des packages système..."
apt update && apt upgrade -y
success "Système mis à jour"

# ============================================================================
# ÉTAPE 2: INSTALLATION DES DÉPENDANCES
# ============================================================================
step "Étape 2/8: Installation des dépendances"
log "📦 Installation des packages nécessaires..."

# Packages système
apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server git curl wget unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Installation de Node.js (pour les assets frontend si nécessaire)
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Installation de FFmpeg
apt install -y ffmpeg

# Installation de Certbot pour SSL
apt install -y certbot python3-certbot-nginx

# Installation de UFW (firewall)
apt install -y ufw

# Installation de Fail2ban
apt install -y fail2ban

success "Toutes les dépendances installées"

# ============================================================================
# ÉTAPE 3: CONFIGURATION DE LA BASE DE DONNÉES
# ============================================================================
step "Étape 3/8: Configuration de la base de données"
log "🗄️ Configuration de PostgreSQL..."

# Démarrer PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Créer la base de données et l'utilisateur
sudo -u postgres psql -c "CREATE DATABASE livemanager_db;"
sudo -u postgres psql -c "CREATE USER livemanager_user WITH PASSWORD 'livemanager_password_2024';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE livemanager_db TO livemanager_user;"
sudo -u postgres psql -c "ALTER USER livemanager_user CREATEDB;"

success "Base de données PostgreSQL configurée"

# ============================================================================
# ÉTAPE 4: CONFIGURATION DE REDIS
# ============================================================================
step "Étape 4/8: Configuration de Redis"
log "🔴 Configuration de Redis..."

# Démarrer Redis
systemctl start redis-server
systemctl enable redis-server

success "Redis configuré et démarré"

# ============================================================================
# ÉTAPE 5: CONFIGURATION DU FIREWALL
# ============================================================================
step "Étape 5/8: Configuration du firewall"
log "🔥 Configuration du firewall UFW..."

# Réinitialiser UFW
ufw --force reset

# Règles par défaut
ufw default deny incoming
ufw default allow outgoing

# Autoriser SSH
ufw allow ssh

# Autoriser HTTP et HTTPS
ufw allow 80
ufw allow 443

# Activer UFW
ufw --force enable

success "Firewall configuré et activé"

# ============================================================================
# ÉTAPE 6: DÉPLOIEMENT DE L'APPLICATION
# ============================================================================
step "Étape 6/8: Déploiement de l'application"
log "📁 Création des répertoires..."
mkdir -p $PROJECT_DIR
mkdir -p $BACKUP_DIR

# Aller dans le répertoire du projet
cd $PROJECT_DIR

# Vérifier si c'est un repository Git existant
if [ -d ".git" ]; then
    log "🔄 Repository Git existant détecté - Mise à jour..."
    
    # Sauvegarder les fichiers sensibles
    if [ -f ".env" ]; then
        cp .env /tmp/livemanager_env_backup
        log "📄 Fichier .env sauvegardé"
    fi
    
    # Sauvegarder les médias si ils existent
    if [ -d "media" ]; then
        tar -czf "$BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz" media/
        log "📁 Dossier media sauvegardé"
    fi
    
    # Sauvegarder les fichiers statiques si ils existent
    if [ -d "staticfiles" ]; then
        tar -czf "$BACKUP_DIR/staticfiles_backup_$TIMESTAMP.tar.gz" staticfiles/
        log "📁 Dossier staticfiles sauvegardé"
    fi
    
    # Faire un pull pour mettre à jour le code
    log "⬇️ Mise à jour du code depuis GitHub..."
    git fetch origin
    git reset --hard origin/main
    
    # Restaurer les fichiers sensibles
    if [ -f "/tmp/livemanager_env_backup" ]; then
        cp /tmp/livemanager_env_backup .env
        rm /tmp/livemanager_env_backup
        log "📄 Fichier .env restauré"
    fi
    
    # Restaurer les médias
    if [ -f "$BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz" ]; then
        tar -xzf "$BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz" -C .
        log "📁 Dossier media restauré"
    fi
    
    # Restaurer les fichiers statiques
    if [ -f "$BACKUP_DIR/staticfiles_backup_$TIMESTAMP.tar.gz" ]; then
        tar -xzf "$BACKUP_DIR/staticfiles_backup_$TIMESTAMP.tar.gz" -C .
        log "📁 Dossier staticfiles restauré"
    fi
    
else
    log "🆕 Nouveau déploiement - Clonage du repository..."
    
    # Sauvegarder l'ancienne version si elle existe
    if [ "$(ls -A)" ]; then
        tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" -C $PROJECT_DIR .
        log "💾 Backup créé: backup_$TIMESTAMP.tar.gz"
    fi
    
    # Nettoyer le répertoire
    rm -rf *
    
    # Cloner le nouveau code
    git clone $REPO_URL .
fi

# Créer l'environnement virtuel s'il n'existe pas
if [ ! -d "venv" ]; then
    log "🐍 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Configurer les permissions de l'environnement virtuel
chown -R www-data:www-data venv

# Activer l'environnement virtuel et installer/mettre à jour les dépendances
log "📦 Installation/mise à jour des dépendances..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Configurer les variables d'environnement
log "⚙️ Configuration des variables d'environnement..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    
    # Générer une clé secrète
    SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    
    # Configurer le fichier .env
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    sed -i "s/DEBUG=.*/DEBUG=False/" .env
    sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=$DOMAIN,localhost,127.0.0.1/" .env
    sed -i "s/DATABASE_URL=.*/DATABASE_URL=postgresql:\/\/livemanager_user:livemanager_password_2024@localhost:5432\/livemanager_db/" .env
    sed -i "s/REDIS_URL=.*/REDIS_URL=redis:\/\/localhost:6379\/0/" .env
    sed -i "s/CSRF_TRUSTED_ORIGINS=.*/CSRF_TRUSTED_ORIGINS=https:\/\/$DOMAIN/" .env
    
    log "🔑 Clé secrète générée et configuration mise à jour"
fi

# Appliquer les migrations
log "🗄️ Application des migrations..."
python manage.py migrate

# Collecter les fichiers statiques
log "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Créer le superuser si il n'existe pas
log "👤 Création du superuser..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@$DOMAIN', 'admin123') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell

success "Application déployée avec succès"

# ============================================================================
# ÉTAPE 7: CONFIGURATION DES SERVICES
# ============================================================================
step "Étape 7/8: Configuration des services"
log "⚙️ Configuration des services systemd..."

# Service principal Django
cat > /etc/systemd/system/livemanager.service << EOF
[Unit]
Description=LiveManager Django Application
After=network.target postgresql.service redis-server.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
Environment=DJANGO_SETTINGS_MODULE=livemanager.settings
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --workers 3 --bind unix:$PROJECT_DIR/livemanager.sock livemanager.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Service Celery
cat > /etc/systemd/system/livemanager-celery.service << EOF
[Unit]
Description=LiveManager Celery Worker
After=network.target postgresql.service redis-server.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
Environment=DJANGO_SETTINGS_MODULE=livemanager.settings
ExecStart=$PROJECT_DIR/venv/bin/celery -A livemanager multi start worker1 --pidfile=/var/run/celery/%n.pid --logfile=/var/log/celery/%n%I.log --loglevel=INFO
ExecStop=$PROJECT_DIR/venv/bin/celery multi stopwait worker1 --pidfile=/var/run/celery/%n.pid
ExecReload=$PROJECT_DIR/venv/bin/celery -A livemanager multi restart worker1 --pidfile=/var/run/celery/%n.pid --logfile=/var/log/celery/%n%I.log --loglevel=INFO
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Créer les répertoires pour Celery
mkdir -p /var/run/celery
mkdir -p /var/log/celery
chown -R www-data:www-data /var/run/celery /var/log/celery

# Configurer Nginx
log "🌐 Configuration de Nginx..."
cat > /etc/nginx/sites-available/livemanager << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Redirection vers HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # Configuration SSL temporaire (sera remplacée par Let's Encrypt)
    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;
    
    # Sécurité SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Headers de sécurité
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Fichiers statiques
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Fichiers média
    location /media/ {
        alias $PROJECT_DIR/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Proxy vers Gunicorn
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
ln -sf /etc/nginx/sites-available/livemanager /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Tester la configuration Nginx
nginx -t

# Configurer les permissions
log "🔐 Configuration des permissions..."
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR

# Redémarrer les services
log "🔄 Démarrage des services..."
systemctl daemon-reload
systemctl start livemanager
systemctl enable livemanager
systemctl start livemanager-celery
systemctl enable livemanager-celery
systemctl reload nginx

success "Services configurés et démarrés"

# ============================================================================
# ÉTAPE 8: CONFIGURATION SSL ET FINALISATION
# ============================================================================
step "Étape 8/8: Configuration SSL et finalisation"
log "🔒 Configuration du certificat SSL..."

# Essayer d'obtenir un certificat SSL avec Let's Encrypt
if [ "$DOMAIN" != "$(hostname -I | awk '{print $1}')" ]; then
    log "🌐 Tentative d'obtention du certificat SSL pour $DOMAIN..."
    if certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN; then
        success "Certificat SSL obtenu avec succès"
    else
        warning "Impossible d'obtenir le certificat SSL. Le site fonctionnera en HTTP."
        # Modifier la configuration Nginx pour HTTP
        sed -i 's/listen 443 ssl http2;/# listen 443 ssl http2;/' /etc/nginx/sites-available/livemanager
        sed -i 's/return 301 https:\/\/\$server_name\$request_uri;/# return 301 https:\/\/\$server_name\$request_uri;/' /etc/nginx/sites-available/livemanager
        systemctl reload nginx
    fi
else
    warning "Utilisation de l'IP du serveur - SSL non configuré"
fi

# Nettoyer les anciens backups (garder seulement les 5 plus récents)
log "🧹 Nettoyage des anciens backups..."
cd $BACKUP_DIR
ls -t | tail -n +6 | xargs -r rm

# Vérifier le statut des services
log "📊 Vérification du statut des services..."
systemctl is-active livemanager && success "Service livemanager actif" || error "Service livemanager inactif"
systemctl is-active livemanager-celery && success "Service livemanager-celery actif" || error "Service livemanager-celery inactif"
systemctl is-active nginx && success "Service nginx actif" || error "Service nginx inactif"
systemctl is-active postgresql && success "Service postgresql actif" || error "Service postgresql inactif"
systemctl is-active redis-server && success "Service redis actif" || error "Service redis inactif"

# ============================================================================
# FINALISATION
# ============================================================================
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🎉 DÉPLOIEMENT TERMINÉ !                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

success "🎉 Déploiement terminé avec succès!"

# Informations de connexion
echo -e "${CYAN}📋 Informations de connexion:${NC}"
echo -e "🌐 URL du site: ${GREEN}http://$DOMAIN${NC}"
if [ "$DOMAIN" != "$(hostname -I | awk '{print $1}')" ]; then
    echo -e "🔒 URL sécurisée: ${GREEN}https://$DOMAIN${NC}"
fi
echo -e "👤 Superuser: ${GREEN}admin${NC}"
echo -e "🔑 Mot de passe: ${GREEN}admin123${NC}"
echo -e "📁 Répertoire du projet: ${GREEN}$PROJECT_DIR${NC}"
echo -e "💾 Backups: ${GREEN}$BACKUP_DIR${NC}"

# Commandes utiles
echo -e "${YELLOW}🔧 Commandes utiles:${NC}"
echo -e "  sudo systemctl status livemanager"
echo -e "  sudo systemctl restart livemanager"
echo -e "  sudo journalctl -u livemanager -f"
echo -e "  sudo nginx -t"
echo -e "  sudo systemctl restart nginx"

# Renouvellement SSL automatique
if [ "$DOMAIN" != "$(hostname -I | awk '{print $1}')" ]; then
    echo -e "${YELLOW}🔒 Renouvellement SSL automatique configuré${NC}"
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
fi

echo -e "${GREEN}🚀 Votre site LiveManager est maintenant en ligne !${NC}" 