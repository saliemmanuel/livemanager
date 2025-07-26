#!/bin/bash

# Script de diagnostic et correction du service LiveManager
# Usage: ./fix_service.sh

echo "🔧 Diagnostic du service LiveManager"
echo "==================================="

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "📋 Vérification des prérequis"
echo "---------------------------"

# Vérifier si le répertoire existe
if [ -d "/var/www/livemanager" ]; then
    echo -e "${GREEN}✅ Répertoire /var/www/livemanager: EXISTE${NC}"
else
    echo -e "${RED}❌ Répertoire /var/www/livemanager: MANQUANT${NC}"
    echo "   Création du répertoire..."
    sudo mkdir -p /var/www/livemanager
    sudo chown livemanager:livemanager /var/www/livemanager
fi

# Vérifier si le code est présent
if [ -f "/var/www/livemanager/manage.py" ]; then
    echo -e "${GREEN}✅ Code Django: PRÉSENT${NC}"
else
    echo -e "${RED}❌ Code Django: MANQUANT${NC}"
    echo "   Clonage du repository..."
    cd /var/www/livemanager
    git clone https://github.com/votre-username/livemanager.git .
    sudo chown -R livemanager:livemanager /var/www/livemanager
fi

# Vérifier l'environnement virtuel
if [ -d "/var/www/livemanager/venv" ]; then
    echo -e "${GREEN}✅ Environnement virtuel: EXISTE${NC}"
else
    echo -e "${RED}❌ Environnement virtuel: MANQUANT${NC}"
    echo "   Création de l'environnement virtuel..."
    cd /var/www/livemanager
    python3 -m venv venv
    sudo chown -R livemanager:livemanager venv
fi

# Vérifier les dépendances
if [ -f "/var/www/livemanager/venv/bin/gunicorn" ]; then
    echo -e "${GREEN}✅ Gunicorn: INSTALLÉ${NC}"
else
    echo -e "${RED}❌ Gunicorn: MANQUANT${NC}"
    echo "   Installation des dépendances..."
    cd /var/www/livemanager
    source venv/bin/activate
    pip install -r requirements.txt
fi

echo ""
echo "🔧 Configuration du service"
echo "-------------------------"

# Créer le service systemd
echo "Création du service systemd..."
sudo tee /etc/systemd/system/livemanager.service > /dev/null <<EOF
[Unit]
Description=LiveManager Django Application
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=livemanager
Group=livemanager
WorkingDirectory=/var/www/livemanager
Environment=PATH=/var/www/livemanager/venv/bin
ExecStart=/var/www/livemanager/venv/bin/gunicorn --workers 3 --bind unix:/var/www/livemanager/livemanager.sock livemanager.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Corriger les permissions
echo "Correction des permissions..."
sudo chown -R livemanager:livemanager /var/www/livemanager
sudo chmod -R 755 /var/www/livemanager

# Créer le répertoire de logs
sudo mkdir -p /var/log/livemanager
sudo chown livemanager:livemanager /var/log/livemanager

echo ""
echo "📋 Configuration des variables d'environnement"
echo "--------------------------------------------"

# Créer le fichier .env s'il n'existe pas
if [ ! -f "/var/www/livemanager/.env" ]; then
    echo "Création du fichier .env..."
    cd /var/www/livemanager
    cp env.example .env
    
    # Générer une clé secrète
    SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    
    # Mettre à jour le fichier .env
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    sed -i "s/DEBUG=.*/DEBUG=False/" .env
    sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=91.108.112.77/" .env
    
    sudo chown livemanager:livemanager .env
    echo -e "${GREEN}✅ Fichier .env créé${NC}"
else
    echo -e "${GREEN}✅ Fichier .env: EXISTE${NC}"
fi

echo ""
echo "🗄️ Configuration de la base de données"
echo "------------------------------------"

# Vérifier si PostgreSQL est configuré
if sudo -u postgres psql -c "\l" 2>/dev/null | grep -q "livemanager_db"; then
    echo -e "${GREEN}✅ Base de données: EXISTE${NC}"
else
    echo -e "${RED}❌ Base de données: MANQUANTE${NC}"
    echo "   Configuration de PostgreSQL..."
    sudo -u postgres psql -c "CREATE DATABASE livemanager_db;"
    sudo -u postgres psql -c "CREATE USER livemanager WITH PASSWORD 'motdepasse_securise';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE livemanager_db TO livemanager;"
    sudo -u postgres psql -c "ALTER USER livemanager CREATEDB;"
fi

echo ""
echo "🚀 Test de démarrage"
echo "------------------"

# Tester Django manuellement
echo "Test de Django..."
cd /var/www/livemanager
source venv/bin/activate

# Vérifier la configuration Django
if python manage.py check --deploy; then
    echo -e "${GREEN}✅ Configuration Django: OK${NC}"
else
    echo -e "${RED}❌ Configuration Django: ERREUR${NC}"
    echo "   Logs:"
    python manage.py check --deploy
fi

# Appliquer les migrations
echo "Application des migrations..."
python manage.py migrate

# Collecter les fichiers statiques
echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo ""
echo "🔄 Redémarrage des services"
echo "-------------------------"

# Recharger systemd
sudo systemctl daemon-reload

# Redémarrer le service
sudo systemctl restart livemanager

# Vérifier l'état
echo "État du service:"
sudo systemctl status livemanager --no-pager

echo ""
echo "📊 Logs du service"
echo "----------------"
echo "Dernières lignes des logs:"
sudo journalctl -u livemanager -n 20 --no-pager

echo ""
echo "🔧 Commandes utiles"
echo "-----------------"
echo "1. Voir les logs en temps réel:"
echo "   sudo journalctl -u livemanager -f"
echo ""
echo "2. Redémarrer le service:"
echo "   sudo systemctl restart livemanager"
echo ""
echo "3. Tester manuellement:"
echo "   cd /var/www/livemanager && source venv/bin/activate"
echo "   gunicorn --bind 0.0.0.0:8000 livemanager.wsgi:application"
echo ""
echo "4. Vérifier les permissions:"
echo "   ls -la /var/www/livemanager/"
echo "   ls -la /var/www/livemanager/livemanager.sock"

echo ""
echo "✅ Diagnostic terminé!" 