#!/bin/bash

# 🔧 Script de Diagnostic et Correction - Erreur 502 Bad Gateway
# Ce script diagnostique et corrige les problèmes de déploiement

set -e

# Variables
PROJECT_DIR="/var/www/livemanager"
SERVICE_NAME="livemanager"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

step() {
    echo -e "${BLUE}🔧 $1${NC}"
}

# Vérifier si on est root
if [ "$EUID" -ne 0 ]; then
    error "Ce script doit être exécuté en tant que root (sudo ./fix_502.sh)"
    exit 1
fi

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                🔧 Diagnostic 502 Bad Gateway                ║"
echo "║              Script de correction automatique                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================================
# ÉTAPE 1: DIAGNOSTIC GÉNÉRAL
# ============================================================================
step "Étape 1/6: Diagnostic général"

log "📊 Vérification de l'existence du projet..."
if [ ! -d "$PROJECT_DIR" ]; then
    error "Le répertoire $PROJECT_DIR n'existe pas"
    log "Création du répertoire..."
    mkdir -p $PROJECT_DIR
    cd $PROJECT_DIR
    git clone https://github.com/saliemmanuel/livemanager.git .
else
    success "Répertoire projet trouvé"
    cd $PROJECT_DIR
fi

log "📁 Vérification des fichiers Django..."
if [ ! -f "manage.py" ]; then
    error "Fichier manage.py manquant"
    exit 1
fi
success "Fichiers Django présents"

# ============================================================================
# ÉTAPE 2: VÉRIFICATION DE L'ENVIRONNEMENT VIRTUEL
# ============================================================================
step "Étape 2/6: Vérification de l'environnement virtuel"

if [ ! -d "venv" ]; then
    log "🐍 Création de l'environnement virtuel..."
    python3 -m venv venv
    success "Environnement virtuel créé"
else
    success "Environnement virtuel existant"
fi

# Activer l'environnement virtuel
source venv/bin/activate

log "📦 Vérification des dépendances..."
if ! pip list | grep -q "Django"; then
    log "📦 Installation des dépendances..."
    pip install --upgrade pip
    pip install -r requirements.txt
    success "Dépendances installées"
else
    success "Dépendances présentes"
fi

# ============================================================================
# ÉTAPE 3: VÉRIFICATION DE LA CONFIGURATION
# ============================================================================
step "Étape 3/6: Vérification de la configuration"

# Vérifier le fichier .env
log "⚙️ Vérification du fichier .env..."
if [ ! -f ".env" ]; then
    log "📄 Création du fichier .env..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        # Générer une clé secrète
        SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        sed -i "s/DEBUG=.*/DEBUG=False/" .env
        sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=*,localhost,127.0.0.1/" .env
        
        # Optimisations pour upload de gros fichiers
        echo "DATA_UPLOAD_MAX_MEMORY_SIZE=1073741824" >> .env
        echo "FILE_UPLOAD_MAX_MEMORY_SIZE=1073741824" >> .env
        
        success "Fichier .env créé"
    else
        error "Fichier .env.example manquant"
        exit 1
    fi
else
    success "Fichier .env présent"
fi

# ============================================================================
# ÉTAPE 4: VÉRIFICATION DE LA BASE DE DONNÉES
# ============================================================================
step "Étape 4/6: Vérification de la base de données"

log "🗄️ Vérification de PostgreSQL..."
if systemctl is-active --quiet postgresql; then
    success "PostgreSQL actif"
else
    log "🔄 Démarrage de PostgreSQL..."
    systemctl start postgresql
    systemctl enable postgresql
    success "PostgreSQL démarré"
fi

log "🔍 Vérification de la base de données..."
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw livemanager_db; then
    success "Base de données existante"
else
    log "🗄️ Création de la base de données..."
    sudo -u postgres psql -c "CREATE DATABASE livemanager_db;" || true
    sudo -u postgres psql -c "CREATE USER livemanager_user WITH PASSWORD 'livemanager_password_2024';" || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE livemanager_db TO livemanager_user;" || true
    success "Base de données créée"
fi

log "🔄 Application des migrations..."
python manage.py migrate
success "Migrations appliquées"

log "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput
success "Fichiers statiques collectés"

# ============================================================================
# ÉTAPE 5: CORRECTION DU SERVICE SYSTEMD
# ============================================================================
step "Étape 5/6: Correction du service systemd"

log "⚙️ Recréation du service systemd..."
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

# Créer le répertoire pour le socket s'il n'existe pas
mkdir -p $(dirname $PROJECT_DIR/livemanager.sock)

# Configurer les permissions
log "🔐 Configuration des permissions..."
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR
chmod 664 $PROJECT_DIR/.env

# Recharger systemd
systemctl daemon-reload

# Arrêter le service s'il tourne
systemctl stop livemanager || true

# Démarrer le service
log "🚀 Démarrage du service..."
systemctl start livemanager
systemctl enable livemanager

# Vérifier le statut
sleep 3
if systemctl is-active --quiet livemanager; then
    success "Service livemanager démarré avec succès"
else
    error "Échec du démarrage du service"
    log "📋 Logs du service:"
    journalctl -u livemanager --no-pager -l
    exit 1
fi

# ============================================================================
# ÉTAPE 6: CORRECTION DE NGINX
# ============================================================================
step "Étape 6/6: Correction de Nginx"

log "🌐 Vérification de Nginx..."
if systemctl is-active --quiet nginx; then
    success "Nginx actif"
else
    log "🔄 Démarrage de Nginx..."
    systemctl start nginx
    systemctl enable nginx
    success "Nginx démarré"
fi

# Configurer Nginx
log "🌐 Configuration de Nginx..."
cat > /etc/nginx/sites-available/livemanager << EOF
server {
    listen 80;
    server_name _;
    
    # Optimisations pour upload de gros fichiers
    client_max_body_size 2G;
    client_body_timeout 600s;
    client_header_timeout 600s;
    
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
        
        # Timeouts pour upload de gros fichiers
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
EOF

# Activer le site
ln -sf /etc/nginx/sites-available/livemanager /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Tester la configuration
log "🧪 Test de la configuration Nginx..."
if nginx -t; then
    success "Configuration Nginx valide"
else
    error "Configuration Nginx invalide"
    exit 1
fi

# Recharger Nginx
systemctl reload nginx
success "Nginx rechargé"

# ============================================================================
# VÉRIFICATION FINALE
# ============================================================================
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🎉 CORRECTION TERMINÉE !                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

log "📊 Vérification finale des services..."

# Vérifier tous les services
services=("livemanager" "nginx" "postgresql" "redis-server")
all_good=true

for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        success "Service $service actif"
    else
        error "Service $service inactif"
        all_good=false
    fi
done

# Vérifier le socket
if [ -S "$PROJECT_DIR/livemanager.sock" ]; then
    success "Socket Gunicorn créé"
else
    error "Socket Gunicorn manquant"
    all_good=false
fi

# Test de connexion locale
log "🌐 Test de connexion locale..."
if curl -s http://localhost > /dev/null; then
    success "Site accessible localement"
else
    warning "Site non accessible localement"
    all_good=false
fi

if [ "$all_good" = true ]; then
    success "🎉 Tous les services fonctionnent correctement !"
    echo -e "${CYAN}📋 Informations de connexion:${NC}"
    echo -e "🌐 URL: ${GREEN}http://$(hostname -I | awk '{print $1}')${NC}"
    echo -e "👤 Admin: ${GREEN}admin${NC}"
    echo -e "🔑 Mot de passe: ${GREEN}admin123${NC}"
else
    warning "⚠️ Certains services ont des problèmes"
    echo -e "${YELLOW}🔧 Commandes de diagnostic:${NC}"
    echo -e "  sudo systemctl status livemanager"
    echo -e "  sudo journalctl -u livemanager -f"
    echo -e "  sudo nginx -t"
    echo -e "  ls -la $PROJECT_DIR/livemanager.sock"
fi

echo -e "${GREEN}🚀 Votre site devrait maintenant être accessible !${NC}" 