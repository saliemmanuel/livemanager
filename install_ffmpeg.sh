#!/bin/bash

# 🔧 Script d'Installation FFmpeg pour LiveManager
# Ce script installe FFmpeg sur le serveur VPS

set -e

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
    error "Ce script doit être exécuté en tant que root (sudo ./install_ffmpeg.sh)"
    exit 1
fi

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                🔧 Installation FFmpeg                       ║"
echo "║              Pour la compression vidéo                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================================
# ÉTAPE 1: VÉRIFICATION DE L'EXISTENCE
# ============================================================================
step "Étape 1/4: Vérification de FFmpeg"

if command -v ffmpeg &> /dev/null; then
    ffmpeg_version=$(ffmpeg -version | head -n1 | cut -d' ' -f3)
    success "FFmpeg est déjà installé (version: $ffmpeg_version)"
    log "Vérification des codecs..."
    
    # Vérifier les codecs nécessaires
    if ffmpeg -codecs 2>/dev/null | grep -q "libx264"; then
        success "Codec H.264 (libx264) disponible"
    else
        warning "Codec H.264 manquant, installation des codecs..."
    fi
    
    if ffmpeg -codecs 2>/dev/null | grep -q "aac"; then
        success "Codec AAC disponible"
    else
        warning "Codec AAC manquant, installation des codecs..."
    fi
else
    log "FFmpeg n'est pas installé, installation en cours..."
fi

# ============================================================================
# ÉTAPE 2: MISE À JOUR DU SYSTÈME
# ============================================================================
step "Étape 2/4: Mise à jour du système"

log "Mise à jour des paquets..."
apt update -qq

# ============================================================================
# ÉTAPE 3: INSTALLATION DE FFMPEG
# ============================================================================
step "Étape 3/4: Installation de FFmpeg"

# Détecter la distribution
if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu
    log "Distribution Debian/Ubuntu détectée"
    
    # Ajouter le dépôt FFmpeg officiel pour les versions récentes
    log "Ajout du dépôt FFmpeg officiel..."
    apt install -y software-properties-common
    add-apt-repository ppa:jonathonf/ffmpeg-4 -y
    apt update -qq
    
    # Installer FFmpeg avec tous les codecs
    log "Installation de FFmpeg et des codecs..."
    apt install -y ffmpeg \
                   libavcodec-extra \
                   libavformat-dev \
                   libavutil-dev \
                   libswscale-dev \
                   libavfilter-dev \
                   libx264-dev \
                   libx265-dev \
                   libfdk-aac-dev \
                   libmp3lame-dev \
                   libopus-dev \
                   libvpx-dev \
                   libwebp-dev \
                   libass-dev \
                   libfreetype6-dev \
                   libfontconfig1-dev \
                   libfribidi-dev \
                   libharfbuzz-dev \
                   libtheora-dev \
                   libvorbis-dev \
                   libxvidcore-dev \
                   libx264-dev \
                   libx265-dev \
                   libnuma-dev \
                   libvdpau-dev \
                   libva-dev \
                   libxcb1-dev \
                   libxcb-shm0-dev \
                   libxcb-xfixes0-dev \
                   pkg-config \
                   yasm \
                   cmake \
                   build-essential
    
elif [ -f /etc/redhat-release ]; then
    # CentOS/RHEL/Fedora
    log "Distribution CentOS/RHEL/Fedora détectée"
    
    # Installer les dépendances EPEL
    if command -v yum &> /dev/null; then
        yum install -y epel-release
        yum install -y ffmpeg ffmpeg-devel
    elif command -v dnf &> /dev/null; then
        dnf install -y epel-release
        dnf install -y ffmpeg ffmpeg-devel
    fi
    
else
    # Autres distributions
    log "Distribution non reconnue, tentative d'installation générique..."
    apt install -y ffmpeg || yum install -y ffmpeg || dnf install -y ffmpeg
fi

# ============================================================================
# ÉTAPE 4: VÉRIFICATION ET CONFIGURATION
# ============================================================================
step "Étape 4/4: Vérification et configuration"

# Vérifier l'installation
if command -v ffmpeg &> /dev/null; then
    ffmpeg_version=$(ffmpeg -version | head -n1 | cut -d' ' -f3)
    success "FFmpeg installé avec succès (version: $ffmpeg_version)"
    
    # Afficher les informations de configuration
    log "Configuration FFmpeg:"
    ffmpeg -version | head -n5
    
    # Vérifier les codecs
    log "Codecs disponibles:"
    if ffmpeg -codecs 2>/dev/null | grep -q "libx264"; then
        success "✓ H.264 (libx264) - Compression vidéo"
    else
        warning "✗ H.264 (libx264) - Manquant"
    fi
    
    if ffmpeg -codecs 2>/dev/null | grep -q "aac"; then
        success "✓ AAC - Compression audio"
    else
        warning "✗ AAC - Manquant"
    fi
    
    if ffmpeg -codecs 2>/dev/null | grep -q "libmp3lame"; then
        success "✓ MP3 (libmp3lame) - Audio alternatif"
    else
        warning "✗ MP3 (libmp3lame) - Manquant"
    fi
    
    # Test de compression
    log "Test de compression..."
    if [ -d "/tmp" ]; then
        # Créer un fichier de test (1 seconde de silence)
        ffmpeg -f lavfi -i anullsrc=r=44100:cl=stereo -t 1 -c:a aac /tmp/test_audio.aac -y -loglevel error
        if [ $? -eq 0 ]; then
            success "Test de compression audio réussi"
            rm -f /tmp/test_audio.aac
        else
            warning "Test de compression audio échoué"
        fi
    fi
    
    # Configuration des permissions
    log "Configuration des permissions..."
    chmod +x $(which ffmpeg)
    
    # Créer un lien symbolique si nécessaire
    if [ ! -L /usr/local/bin/ffmpeg ] && [ -f /usr/bin/ffmpeg ]; then
        ln -sf /usr/bin/ffmpeg /usr/local/bin/ffmpeg
        success "Lien symbolique créé"
    fi
    
else
    error "Échec de l'installation de FFmpeg"
    exit 1
fi

# ============================================================================
# CONFIGURATION POUR LIVEMANAGER
# ============================================================================
log "Configuration pour LiveManager..."

# Vérifier que le répertoire media existe
PROJECT_DIR="/var/www/livemanager"
if [ -d "$PROJECT_DIR" ]; then
    log "Configuration des permissions pour LiveManager..."
    chown -R www-data:www-data "$PROJECT_DIR/media"
    chmod -R 755 "$PROJECT_DIR/media"
    success "Permissions configurées"
fi

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🎉 INSTALLATION TERMINÉE !                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

success "FFmpeg est maintenant prêt pour la compression vidéo"
echo -e "${BLUE}📋 Informations:${NC}"
echo -e "🎬 FFmpeg version: ${GREEN}$ffmpeg_version${NC}"
echo -e "🔧 Codecs: H.264, AAC, MP3"
echo -e "📁 Répertoire: ${GREEN}/usr/bin/ffmpeg${NC}"
echo -e "👤 Permissions: ${GREEN}www-data${NC}"

echo -e "${YELLOW}🔧 Commandes utiles:${NC}"
echo -e "  ffmpeg -version"
echo -e "  ffmpeg -codecs | grep -E '(libx264|aac|libmp3lame)'"
echo -e "  ffmpeg -i input.mp4 -c:v libx264 -c:a aac output.mp4"

echo -e "${GREEN}🚀 La compression vidéo est maintenant disponible dans LiveManager !${NC}" 