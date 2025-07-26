#!/bin/bash

# Script de déploiement LiveManager
# Ce script déploie l'application en préservant les fichiers existants

set -e  # Arrêter en cas d'erreur

# Variables
PROJECT_DIR="/var/www/livemanager"
BACKUP_DIR="/var/backups/livemanager"
REPO_URL="https://github.com/saliemmanuel/livemanager.git"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

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

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérifier si on est root
if [ "$EUID" -ne 0 ]; then
    error "Ce script doit être exécuté en tant que root"
    exit 1
fi

log "🚀 Démarrage du déploiement LiveManager..."

# Créer les répertoires si ils n'existent pas
log "📁 Création des répertoires..."
mkdir -p $PROJECT_DIR
mkdir -p $BACKUP_DIR

# Aller dans le répertoire du projet
cd $PROJECT_DIR

# Arrêter les services
log "🛑 Arrêt des services..."
systemctl stop livemanager || true
systemctl stop livemanager-celery || true

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
    
    # Sauvegarder la base de données si elle existe
    if [ -f "db.sqlite3" ]; then
        cp db.sqlite3 "$BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3"
        log "🗄️ Base de données sauvegardée"
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
    
    # Restaurer la base de données si nécessaire
    if [ -f "$BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3" ] && [ ! -f "db.sqlite3" ]; then
        cp "$BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3" db.sqlite3
        log "🗄️ Base de données restaurée"
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

# Configurer les variables d'environnement si le fichier n'existe pas
if [ ! -f ".env" ]; then
    log "⚙️ Configuration des variables d'environnement..."
    cp .env.example .env
    
    # Générer une clé secrète
    SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    
    log "🔑 Clé secrète générée et configurée"
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
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR

# Créer/Configurer le service systemd
log "⚙️ Configuration du service systemd..."
cat > /etc/systemd/system/livemanager.service << EOF
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
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Créer/Configurer le service Celery
log "⚙️ Configuration du service Celery..."
cat > /etc/systemd/system/livemanager-celery.service << EOF
[Unit]
Description=LiveManager Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
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
    server_name _;
    
    # Redirection HTTP vers HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;
    
    # Configuration SSL (à configurer avec Let's Encrypt)
    # ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;
    
    # Configuration temporaire pour le développement
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

# Redémarrer les services
log "🔄 Redémarrage des services..."
systemctl daemon-reload
systemctl start livemanager
systemctl enable livemanager
systemctl start livemanager-celery
systemctl enable livemanager-celery
systemctl reload nginx

# Nettoyer les anciens backups (garder seulement les 5 plus récents)
log "🧹 Nettoyage des anciens backups..."
cd $BACKUP_DIR
ls -t | tail -n +6 | xargs -r rm

# Vérifier le statut des services
log "📊 Vérification du statut des services..."
systemctl is-active livemanager && success "Service livemanager actif" || error "Service livemanager inactif"
systemctl is-active livemanager-celery && success "Service livemanager-celery actif" || error "Service livemanager-celery inactif"
systemctl is-active nginx && success "Service nginx actif" || error "Service nginx inactif"

success "🎉 Déploiement terminé avec succès!"
log "🌐 L'application est accessible sur: https://$(hostname -I | awk '{print $1}')"
log "👤 Superuser: admin / admin123"
log "📁 Répertoire du projet: $PROJECT_DIR"
log "💾 Backups: $BACKUP_DIR" 