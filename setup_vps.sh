#!/bin/bash

# Script de configuration initiale du VPS Hostinger pour LiveManager
# Usage: ./setup_vps.sh

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
if [[ $EUID -ne 0 ]]; then
   error "Ce script doit être exécuté en tant que root (sudo)"
fi

log "🚀 Configuration initiale du VPS pour LiveManager"

# Mettre à jour le système
log "📦 Mise à jour du système..."
apt update && apt upgrade -y

# Installer les paquets nécessaires
log "📦 Installation des paquets requis..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    nginx \
    postgresql \
    postgresql-contrib \
    redis-server \
    git \
    curl \
    wget \
    unzip \
    ffmpeg \
    certbot \
    python3-certbot-nginx \
    ufw \
    fail2ban \
    htop \
    nano \
    tree

# Configurer le firewall
log "🔥 Configuration du firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80
ufw allow 443
ufw allow 22
success "Firewall configuré"

# Configurer PostgreSQL
log "🗄️ Configuration de PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE livemanager_db;"
sudo -u postgres psql -c "CREATE USER livemanager WITH PASSWORD 'motdepasse_securise';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE livemanager_db TO livemanager;"
sudo -u postgres psql -c "ALTER USER livemanager CREATEDB;"

# Configurer Redis
log "🔴 Configuration de Redis..."
systemctl enable redis-server
systemctl start redis-server

# Créer l'utilisateur pour l'application
log "👤 Création de l'utilisateur application..."
useradd -m -s /bin/bash livemanager
usermod -aG sudo livemanager
echo "livemanager:motdepasse_securise" | chpasswd

# Créer les répertoires nécessaires
log "📁 Création des répertoires..."
mkdir -p /var/www/livemanager
mkdir -p /var/backups/livemanager
mkdir -p /var/log/livemanager
chown -R livemanager:livemanager /var/www/livemanager
chown -R livemanager:livemanager /var/backups/livemanager
chown -R livemanager:livemanager /var/log/livemanager

# Configurer Nginx
log "🌐 Configuration de Nginx..."
rm -f /etc/nginx/sites-enabled/default
systemctl enable nginx
systemctl start nginx

# Configurer Fail2ban
log "🛡️ Configuration de Fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# Créer le fichier de configuration Fail2ban pour Nginx
cat > /etc/fail2ban/jail.local <<EOF
[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/access.log

[nginx-botsearch]
enabled = true
filter = nginx-botsearch
port = http,https
logpath = /var/log/nginx/access.log
EOF

# Configurer les logs
log "📋 Configuration des logs..."
cat > /etc/logrotate.d/livemanager <<EOF
/var/log/livemanager/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 livemanager livemanager
    postrotate
        systemctl reload livemanager
    endscript
}
EOF

# Optimiser PostgreSQL
log "⚡ Optimisation de PostgreSQL..."
cat >> /etc/postgresql/*/main/postgresql.conf <<EOF

# Optimisations pour LiveManager
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
EOF

# Redémarrer PostgreSQL
systemctl restart postgresql

# Configurer les limites système
log "⚙️ Configuration des limites système..."
cat >> /etc/security/limits.conf <<EOF

# Limites pour livemanager
livemanager soft nofile 65536
livemanager hard nofile 65536
www-data soft nofile 65536
www-data hard nofile 65536
EOF

# Optimiser le kernel
log "🔧 Optimisation du kernel..."
cat >> /etc/sysctl.conf <<EOF

# Optimisations réseau
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_max_tw_buckets = 2000000
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_tw_recycle = 1
net.ipv4.ip_local_port_range = 1024 65535
EOF

# Appliquer les changements du kernel
sysctl -p

# Créer un script de maintenance
log "🔧 Création du script de maintenance..."
cat > /usr/local/bin/livemanager-maintenance.sh <<'EOF'
#!/bin/bash

# Script de maintenance pour LiveManager
PROJECT_DIR="/var/www/livemanager"
BACKUP_DIR="/var/backups/livemanager"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🧹 Début de la maintenance LiveManager..."

# Sauvegarder la base de données
sudo -u postgres pg_dump livemanager_db > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
gzip "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"

# Nettoyer les anciens backups (garder 7 jours)
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

# Nettoyer les logs
find /var/log/livemanager -name "*.log" -mtime +30 -delete

# Redémarrer les services
systemctl restart livemanager
systemctl restart nginx

echo "✅ Maintenance terminée!"
EOF

chmod +x /usr/local/bin/livemanager-maintenance.sh

# Configurer la tâche cron pour la maintenance
log "⏰ Configuration de la maintenance automatique..."
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/livemanager-maintenance.sh") | crontab -

# Créer un script de monitoring
log "📊 Création du script de monitoring..."
cat > /usr/local/bin/livemanager-status.sh <<'EOF'
#!/bin/bash

echo "=== Status LiveManager ==="
echo "Django: $(systemctl is-active livemanager)"
echo "Nginx: $(systemctl is-active nginx)"
echo "PostgreSQL: $(systemctl is-active postgresql)"
echo "Redis: $(systemctl is-active redis-server)"
echo ""
echo "=== Utilisation disque ==="
df -h /var/www/livemanager
echo ""
echo "=== Utilisation mémoire ==="
free -h
echo ""
echo "=== Logs récents ==="
tail -n 10 /var/log/livemanager/django.log 2>/dev/null || echo "Aucun log Django"
EOF

chmod +x /usr/local/bin/livemanager-status.sh

# Créer un alias pour faciliter l'accès
echo 'alias livemanager-status="/usr/local/bin/livemanager-status.sh"' >> /home/livemanager/.bashrc

# Configurer les permissions
log "🔐 Configuration des permissions..."
chown -R livemanager:livemanager /home/livemanager
chmod 755 /home/livemanager

success "🎉 Configuration initiale terminée!"

echo ""
echo "📋 Prochaines étapes:"
echo "1. Connectez-vous en tant que livemanager:"
echo "   ssh livemanager@votre-ip"
echo ""
echo "2. Clonez votre repository:"
echo "   cd /var/www/livemanager"
echo "   git clone https://github.com/votre-username/livemanager.git ."
echo ""
echo "3. Configurez le fichier .env:"
echo "   cp env.example .env"
echo "   nano .env"
echo ""
echo "4. Lancez le déploiement:"
echo "   chmod +x deploy.sh"
echo "   ./deploy.sh"
echo ""
echo "5. Configurez SSL avec Let's Encrypt:"
echo "   certbot --nginx -d votre-domaine.com"
echo ""
echo "🔧 Commandes utiles:"
echo "  livemanager-status"
echo "  sudo systemctl status livemanager"
echo "  sudo journalctl -u livemanager -f"
echo "  sudo ufw status"
echo "  sudo fail2ban-client status" 