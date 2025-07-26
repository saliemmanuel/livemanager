#!/bin/bash

# 🔧 Script de Correction Rapide - Problèmes d'Upload LiveManager
# Ce script corrige automatiquement les problèmes d'upload les plus courants

set -e

# Variables
PROJECT_DIR="/var/www/livemanager"

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
    error "Ce script doit être exécuté en tant que root (sudo ./fix_upload.sh)"
    exit 1
fi

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                🔧 Correction Problèmes d'Upload             ║"
echo "║              Correction automatique des erreurs              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================================
# ÉTAPE 1: VÉRIFICATION DES SERVICES
# ============================================================================
step "Étape 1/6: Vérification des services"

# Vérifier Django
if systemctl is-active --quiet livemanager; then
    success "Service livemanager actif"
else
    error "Service livemanager inactif"
    log "Démarrage du service..."
    systemctl start livemanager
    systemctl enable livemanager
    success "Service livemanager démarré"
fi

# Vérifier Nginx
if systemctl is-active --quiet nginx; then
    success "Service nginx actif"
else
    error "Service nginx inactif"
    log "Démarrage du service..."
    systemctl start nginx
    systemctl enable nginx
    success "Service nginx démarré"
fi

# Vérifier PostgreSQL
if systemctl is-active --quiet postgresql; then
    success "Service postgresql actif"
else
    error "Service postgresql inactif"
    log "Démarrage du service..."
    systemctl start postgresql
    systemctl enable postgresql
    success "Service postgresql démarré"
fi

# ============================================================================
# ÉTAPE 2: CORRECTION DES PERMISSIONS
# ============================================================================
step "Étape 2/6: Correction des permissions"

log "Configuration des permissions pour le projet..."
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR

log "Configuration des permissions pour les médias..."
mkdir -p $PROJECT_DIR/media/videos
chown -R www-data:www-data $PROJECT_DIR/media
chmod -R 775 $PROJECT_DIR/media

log "Configuration des permissions pour les logs..."
mkdir -p /var/log/livemanager
chown -R www-data:www-data /var/log/livemanager
chmod -R 755 /var/log/livemanager

success "Permissions configurées"

# ============================================================================
# ÉTAPE 3: VÉRIFICATION DE FFMPEG
# ============================================================================
step "Étape 3/6: Vérification de FFmpeg"

if command -v ffmpeg &> /dev/null; then
    ffmpeg_version=$(ffmpeg -version | head -n1 | cut -d' ' -f3)
    success "FFmpeg installé (version: $ffmpeg_version)"
else
    warning "FFmpeg non installé"
    log "Installation de FFmpeg..."
    
    # Installation rapide de FFmpeg
    apt update -qq
    apt install -y ffmpeg libavcodec-extra
    
    if command -v ffmpeg &> /dev/null; then
        success "FFmpeg installé avec succès"
    else
        error "Échec de l'installation de FFmpeg"
    fi
fi

# ============================================================================
# ÉTAPE 4: CONFIGURATION NGINX
# ============================================================================
step "Étape 4/6: Configuration Nginx"

log "Mise à jour de la configuration Nginx pour les uploads..."

# Créer une configuration Nginx optimisée pour les uploads
cat > /etc/nginx/sites-available/livemanager << 'EOF'
server {
    listen 80;
    server_name _;
    
    # Configuration pour les uploads volumineux
    client_max_body_size 500M;
    client_body_timeout 300s;
    client_header_timeout 300s;
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    
    # Fichiers statiques
    location /static/ {
        alias /var/www/livemanager/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Fichiers média
    location /media/ {
        alias /var/www/livemanager/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Proxy vers Gunicorn
    location / {
        proxy_pass http://unix:/var/www/livemanager/livemanager.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts pour éviter les erreurs 502
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Activer le site
ln -sf /etc/nginx/sites-available/livemanager /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Tester la configuration
if nginx -t; then
    success "Configuration Nginx valide"
    systemctl reload nginx
    success "Nginx rechargé"
else
    error "Configuration Nginx invalide"
    exit 1
fi

# ============================================================================
# ÉTAPE 5: VÉRIFICATION DE LA BASE DE DONNÉES
# ============================================================================
step "Étape 5/6: Vérification de la base de données"

log "Vérification de la base de données..."
cd $PROJECT_DIR

# Activer l'environnement virtuel
source venv/bin/activate

# Appliquer les migrations
log "Application des migrations..."
python manage.py migrate --noinput
success "Migrations appliquées"

# Collecter les fichiers statiques
log "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput
success "Fichiers statiques collectés"

# Vérifier la configuration Django
log "Vérification de la configuration Django..."
if python manage.py check; then
    success "Configuration Django valide"
else
    error "Problème de configuration Django"
    exit 1
fi

# ============================================================================
# ÉTAPE 6: NETTOYAGE ET REDÉMARRAGE
# ============================================================================
step "Étape 6/6: Nettoyage et redémarrage"

# Nettoyer les fichiers temporaires
log "Nettoyage des fichiers temporaires..."
find /tmp -name "*livemanager*" -delete 2>/dev/null || true
find $PROJECT_DIR/media -name "*.tmp" -delete 2>/dev/null || true
success "Fichiers temporaires nettoyés"

# Redémarrer les services
log "Redémarrage des services..."
systemctl restart livemanager
systemctl restart nginx
success "Services redémarrés"

# Vérifier l'espace disque
log "Vérification de l'espace disque..."
disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$disk_usage" -gt 90 ]; then
    warning "Espace disque faible: ${disk_usage}% utilisé"
else
    success "Espace disque OK: ${disk_usage}% utilisé"
fi

# ============================================================================
# VÉRIFICATION FINALE
# ============================================================================
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🎉 CORRECTION TERMINÉE !                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

log "Vérification finale des services..."

# Vérifier tous les services
services=("livemanager" "nginx" "postgresql")
all_good=true

for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        success "Service $service actif"
    else
        error "Service $service inactif"
        all_good=false
    fi
done

# Vérifier le socket Gunicorn
if [ -S "$PROJECT_DIR/livemanager.sock" ]; then
    success "Socket Gunicorn créé"
else
    error "Socket Gunicorn manquant"
    all_good=false
fi

# Test de connexion locale
log "Test de connexion locale..."
if curl -s http://localhost > /dev/null; then
    success "Site accessible localement"
else
    warning "Site non accessible localement"
    all_good=false
fi

if [ "$all_good" = true ]; then
    success "🎉 Tous les problèmes d'upload ont été corrigés !"
    echo -e "${CYAN}📋 Prochaines étapes:${NC}"
    echo -e "🌐 Testez l'upload sur votre site"
    echo -e "📱 Vérifiez la console du navigateur (F12) si problème persiste"
    echo -e "📋 Consultez TROUBLESHOOTING_UPLOAD.md pour plus d'aide"
else
    warning "⚠️ Certains problèmes persistent"
    echo -e "${YELLOW}🔧 Commandes de diagnostic:${NC}"
    echo -e "  sudo journalctl -u livemanager -f"
    echo -e "  sudo tail -f /var/log/nginx/error.log"
    echo -e "  python3 debug_upload.py"
fi

echo -e "${GREEN}🚀 Votre système d'upload devrait maintenant fonctionner !${NC}" 