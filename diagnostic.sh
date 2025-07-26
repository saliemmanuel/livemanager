#!/bin/bash

# 🔍 Script de Diagnostic Rapide - LiveManager
# Ce script diagnostique rapidement les problèmes de déploiement

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

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                🔍 Diagnostic Rapide LiveManager              ║"
echo "║              Identification des problèmes                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================================
# DIAGNOSTIC DES SERVICES
# ============================================================================
log "📊 Diagnostic des services..."

# Vérifier les services principaux
services=("nginx" "postgresql" "redis-server" "livemanager")
for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        success "Service $service: ACTIF"
    else
        error "Service $service: INACTIF"
    fi
done

# ============================================================================
# DIAGNOSTIC DU PROJET
# ============================================================================
log "📁 Diagnostic du projet..."

if [ -d "$PROJECT_DIR" ]; then
    success "Répertoire projet: EXISTE"
    cd $PROJECT_DIR
    
    if [ -f "manage.py" ]; then
        success "Fichier manage.py: PRÉSENT"
    else
        error "Fichier manage.py: MANQUANT"
    fi
    
    if [ -d "venv" ]; then
        success "Environnement virtuel: PRÉSENT"
    else
        error "Environnement virtuel: MANQUANT"
    fi
    
    if [ -f ".env" ]; then
        success "Fichier .env: PRÉSENT"
    else
        error "Fichier .env: MANQUANT"
    fi
else
    error "Répertoire projet: MANQUANT"
fi

# ============================================================================
# DIAGNOSTIC DU SOCKET GUNICORN
# ============================================================================
log "🔌 Diagnostic du socket Gunicorn..."

if [ -S "$PROJECT_DIR/livemanager.sock" ]; then
    success "Socket Gunicorn: PRÉSENT"
    ls -la $PROJECT_DIR/livemanager.sock
else
    error "Socket Gunicorn: MANQUANT"
fi

# ============================================================================
# DIAGNOSTIC DES PORTS
# ============================================================================
log "🌐 Diagnostic des ports..."

# Vérifier les ports ouverts
if netstat -tlnp | grep -q ":80 "; then
    success "Port 80: OUVERT"
else
    error "Port 80: FERMÉ"
fi

if netstat -tlnp | grep -q ":443 "; then
    success "Port 443: OUVERT"
else
    warning "Port 443: FERMÉ (normal si pas de SSL)"
fi

# ============================================================================
# DIAGNOSTIC DE LA BASE DE DONNÉES
# ============================================================================
log "🗄️ Diagnostic de la base de données..."

if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw livemanager_db; then
    success "Base de données livemanager_db: EXISTE"
else
    error "Base de données livemanager_db: MANQUANTE"
fi

# ============================================================================
# DIAGNOSTIC DES LOGS
# ============================================================================
log "📋 Diagnostic des logs..."

echo -e "${YELLOW}📄 Logs récents du service livemanager:${NC}"
journalctl -u livemanager --no-pager -l -n 10

echo -e "${YELLOW}📄 Logs récents de Nginx:${NC}"
tail -n 10 /var/log/nginx/error.log 2>/dev/null || echo "Fichier de log Nginx non trouvé"

# ============================================================================
# TEST DE CONNEXION
# ============================================================================
log "🌐 Test de connexion..."

# Test local
if curl -s http://localhost > /dev/null; then
    success "Connexion locale: RÉUSSIE"
else
    error "Connexion locale: ÉCHEC"
fi

# Test avec l'IP du serveur
SERVER_IP=$(hostname -I | awk '{print $1}')
if curl -s http://$SERVER_IP > /dev/null; then
    success "Connexion via IP ($SERVER_IP): RÉUSSIE"
else
    error "Connexion via IP ($SERVER_IP): ÉCHEC"
fi

# ============================================================================
# RÉSUMÉ ET RECOMMANDATIONS
# ============================================================================
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    📋 RÉSUMÉ DU DIAGNOSTIC                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}🔧 Commandes utiles pour résoudre les problèmes:${NC}"
echo -e "  sudo systemctl status livemanager"
echo -e "  sudo systemctl restart livemanager"
echo -e "  sudo journalctl -u livemanager -f"
echo -e "  sudo nginx -t"
echo -e "  sudo systemctl restart nginx"
echo -e "  sudo ./fix_502.sh"

echo -e "${YELLOW}📁 Vérifications manuelles:${NC}"
echo -e "  ls -la $PROJECT_DIR/"
echo -e "  ls -la $PROJECT_DIR/livemanager.sock"
echo -e "  sudo -u www-data python $PROJECT_DIR/manage.py check"

echo -e "${GREEN}🚀 Si des problèmes persistent, exécutez: sudo ./fix_502.sh${NC}" 