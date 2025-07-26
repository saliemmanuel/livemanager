#!/bin/bash

# Script pour corriger le problème de répertoire LiveManager
# Usage: ./fix_directory.sh

echo "🔧 Correction du répertoire LiveManager"
echo "====================================="

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "📁 Vérification de la structure actuelle"
echo "--------------------------------------"

# Vérifier le contenu de /var/www
echo "Contenu de /var/www:"
ls -la /var/www/

echo ""
echo "Contenu de /var/www/html:"
ls -la /var/www/html/

echo ""
echo "🔧 Correction de la structure"
echo "---------------------------"

# Créer le répertoire livemanager
echo "Création du répertoire /var/www/livemanager..."
sudo mkdir -p /var/www/livemanager

# Vérifier si le code est dans /var/www/html
if [ -f "/var/www/html/manage.py" ]; then
    echo -e "${GREEN}✅ Code Django trouvé dans /var/www/html${NC}"
    echo "Déplacement vers /var/www/livemanager..."
    
    # Déplacer le code
    sudo mv /var/www/html/* /var/www/livemanager/
    sudo mv /var/www/html/.* /var/www/livemanager/ 2>/dev/null || true
    
    # Supprimer le répertoire html vide
    sudo rmdir /var/www/html
    
    echo -e "${GREEN}✅ Code déplacé avec succès${NC}"
else
    echo -e "${YELLOW}⚠️  Code Django non trouvé dans /var/www/html${NC}"
    echo "Clonage du repository..."
    
    # Cloner le repository
    cd /var/www/livemanager
    sudo git clone https://github.com/votre-username/livemanager.git .
fi

# Corriger les permissions
echo "Correction des permissions..."
sudo chown -R livemanager:livemanager /var/www/livemanager
sudo chmod -R 755 /var/www/livemanager

echo ""
echo "📋 Vérification de la nouvelle structure"
echo "-------------------------------------"

echo "Contenu de /var/www:"
ls -la /var/www/

echo ""
echo "Contenu de /var/www/livemanager:"
ls -la /var/www/livemanager/

echo ""
echo "🔧 Configuration de l'environnement"
echo "--------------------------------"

# Aller dans le répertoire du projet
cd /var/www/livemanager

# Vérifier l'environnement virtuel
if [ ! -d "venv" ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv venv
    sudo chown -R livemanager:livemanager venv
fi

# Activer l'environnement virtuel et installer les dépendances
echo "Installation des dépendances..."
source venv/bin/activate
pip install -r requirements.txt

# Configurer les variables d'environnement
if [ ! -f ".env" ]; then
    echo "Création du fichier .env..."
    cp env.example .env
    
    # Générer une clé secrète
    SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    
    # Mettre à jour le fichier .env
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    sed -i "s/DEBUG=.*/DEBUG=False/" .env
    sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=91.108.112.77/" .env
    
    sudo chown livemanager:livemanager .env
    echo -e "${GREEN}✅ Fichier .env créé${NC}"
fi

echo ""
echo "🗄️ Configuration de la base de données"
echo "------------------------------------"

# Configurer PostgreSQL
if ! sudo -u postgres psql -c "\l" 2>/dev/null | grep -q "livemanager_db"; then
    echo "Configuration de PostgreSQL..."
    sudo -u postgres psql -c "CREATE DATABASE livemanager_db;"
    sudo -u postgres psql -c "CREATE USER livemanager WITH PASSWORD 'motdepasse_securise';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE livemanager_db TO livemanager;"
    sudo -u postgres psql -c "ALTER USER livemanager CREATEDB;"
fi

# Appliquer les migrations
echo "Application des migrations..."
python manage.py migrate

# Collecter les fichiers statiques
echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo ""
echo "🔧 Configuration du service systemd"
echo "--------------------------------"

# Créer le service systemd
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

# Créer le répertoire de logs
sudo mkdir -p /var/log/livemanager
sudo chown livemanager:livemanager /var/log/livemanager

echo ""
echo "🌐 Configuration Nginx"
echo "-------------------"

# Créer la configuration Nginx
sudo tee /etc/nginx/sites-available/livemanager > /dev/null <<EOF
server {
    listen 80;
    server_name 91.108.112.77;

    # Fichiers statiques
    location /static/ {
        alias /var/www/livemanager/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Fichiers media
    location /media/ {
        alias /var/www/livemanager/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy vers Django
    location / {
        proxy_pass http://unix:/var/www/livemanager/livemanager.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Activer le site
sudo ln -sf /etc/nginx/sites-available/livemanager /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Tester la configuration Nginx
if sudo nginx -t; then
    echo -e "${GREEN}✅ Configuration Nginx: VALIDE${NC}"
else
    echo -e "${RED}❌ Configuration Nginx: INVALIDE${NC}"
fi

echo ""
echo "🚀 Démarrage des services"
echo "----------------------"

# Recharger systemd
sudo systemctl daemon-reload

# Démarrer et activer les services
sudo systemctl enable livemanager
sudo systemctl start livemanager
sudo systemctl restart nginx

# Vérifier l'état des services
echo "État du service LiveManager:"
sudo systemctl status livemanager --no-pager

echo ""
echo "📊 Test de l'application"
echo "---------------------"

# Tester Django
echo "Test de Django..."
cd /var/www/livemanager
source venv/bin/activate
if python manage.py check --deploy; then
    echo -e "${GREEN}✅ Django: OK${NC}"
else
    echo -e "${RED}❌ Django: ERREUR${NC}"
fi

# Tester la connexion locale
echo "Test de la connexion locale..."
if curl -s http://localhost > /dev/null; then
    echo -e "${GREEN}✅ Nginx: ACCESSIBLE${NC}"
else
    echo -e "${RED}❌ Nginx: INACCESSIBLE${NC}"
fi

echo ""
echo "🔧 Commandes utiles"
echo "-----------------"
echo "1. Voir les logs du service:"
echo "   sudo journalctl -u livemanager -f"
echo ""
echo "2. Redémarrer les services:"
echo "   sudo systemctl restart livemanager nginx"
echo ""
echo "3. Vérifier l'état:"
echo "   sudo systemctl status livemanager nginx"
echo ""
echo "4. Tester manuellement:"
echo "   cd /var/www/livemanager && source venv/bin/activate"
echo "   gunicorn --bind 0.0.0.0:8000 livemanager.wsgi:application"

echo ""
echo "✅ Correction terminée!"
echo "Votre site devrait maintenant être accessible sur http://91.108.112.77" 