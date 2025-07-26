# 🔧 Diagnostic et Résolution - LiveManager

## 🚨 Problème : Site non accessible après déploiement

### 📋 Diagnostic Rapide

#### **1. Vérifier l'état des services**
```bash
# Se connecter au VPS
ssh livemanager@91.108.112.77

# Vérifier les services
sudo systemctl status nginx
sudo systemctl status livemanager
sudo systemctl status postgresql
sudo systemctl status redis-server
```

#### **2. Vérifier les logs**
```bash
# Logs Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Logs Django
sudo tail -f /var/log/livemanager/django.log

# Logs système
sudo journalctl -u livemanager -f
```

#### **3. Vérifier le firewall**
```bash
sudo ufw status
sudo iptables -L
```

### 🔧 Solutions par Étape

#### **Étape 1 : Configuration Initiale du VPS**

Si le script `setup_vps.sh` n'a pas été exécuté :

```bash
# Se connecter en root
ssh root@91.108.112.77

# Télécharger et exécuter le script de configuration
wget https://raw.githubusercontent.com/votre-username/livemanager/main/setup_vps.sh
chmod +x setup_vps.sh
./setup_vps.sh
```

#### **Étape 2 : Configuration Manuelle (si nécessaire)**

```bash
# Installer les paquets essentiels
sudo apt update
sudo apt install -y nginx python3 python3-pip python3-venv postgresql redis-server

# Créer l'utilisateur application
sudo useradd -m -s /bin/bash livemanager
sudo usermod -aG sudo livemanager

# Créer les répertoires
sudo mkdir -p /var/www/livemanager
sudo mkdir -p /var/log/livemanager
sudo chown -R livemanager:livemanager /var/www/livemanager
sudo chown -R livemanager:livemanager /var/log/livemanager
```

#### **Étape 3 : Configuration Nginx**

```bash
# Créer la configuration Nginx
sudo nano /etc/nginx/sites-available/livemanager
```

Contenu :
```nginx
server {
    listen 80;
    server_name 91.108.112.77;

    # Redirection HTTP vers HTTPS (optionnel)
    # return 301 https://$server_name$request_uri;

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
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

```bash
# Activer le site
sudo ln -s /etc/nginx/sites-available/livemanager /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

#### **Étape 4 : Configuration Django**

```bash
# Se connecter en tant qu'utilisateur application
ssh livemanager@91.108.112.77

# Aller dans le répertoire du projet
cd /var/www/livemanager

# Vérifier que le code est présent
ls -la

# Si le code n'est pas présent, le cloner
git clone https://github.com/votre-username/livemanager.git .

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp env.example .env
nano .env
```

Configuration `.env` minimale :
```bash
DEBUG=False
SECRET_KEY=votre-clé-secrète-très-longue
ALLOWED_HOSTS=91.108.112.77,votre-domaine.com
DATABASE_URL=postgresql://livemanager:motdepasse_securise@localhost:5432/livemanager_db
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
FFMPEG_PATH=/usr/bin/ffmpeg
```

#### **Étape 5 : Configuration Base de Données**

```bash
# Configurer PostgreSQL
sudo -u postgres psql -c "CREATE DATABASE livemanager_db;"
sudo -u postgres psql -c "CREATE USER livemanager WITH PASSWORD 'motdepasse_securise';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE livemanager_db TO livemanager;"

# Appliquer les migrations
python manage.py migrate

# Créer un superuser
python manage.py createsuperuser

# Collecter les fichiers statiques
python manage.py collectstatic --noinput
```

#### **Étape 6 : Configuration Systemd**

```bash
# Créer le service Django
sudo nano /etc/systemd/system/livemanager.service
```

Contenu :
```ini
[Unit]
Description=LiveManager Django Application
After=network.target postgresql.service redis-server.service

[Service]
Type=notify
User=livemanager
Group=livemanager
WorkingDirectory=/var/www/livemanager
Environment=PATH=/var/www/livemanager/venv/bin
ExecStart=/var/www/livemanager/venv/bin/gunicorn --workers 3 --bind unix:/var/www/livemanager/livemanager.sock livemanager.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Activer et démarrer le service
sudo systemctl daemon-reload
sudo systemctl enable livemanager
sudo systemctl start livemanager
```

#### **Étape 7 : Configuration Firewall**

```bash
# Configurer UFW
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw status
```

### 🔍 Diagnostic Avancé

#### **Vérifier les ports ouverts**
```bash
sudo netstat -tlnp
sudo ss -tlnp
```

#### **Vérifier les permissions**
```bash
ls -la /var/www/livemanager/
ls -la /var/log/livemanager/
```

#### **Tester la connexion locale**
```bash
# Tester Django directement
cd /var/www/livemanager
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000

# Dans un autre terminal
curl http://localhost:8000
```

#### **Vérifier les logs en temps réel**
```bash
# Logs Nginx
sudo tail -f /var/log/nginx/error.log

# Logs Django
sudo journalctl -u livemanager -f

# Logs système
sudo dmesg | tail
```

### 🚨 Problèmes Courants

#### **1. Permission Denied**
```bash
# Corriger les permissions
sudo chown -R livemanager:livemanager /var/www/livemanager
sudo chmod -R 755 /var/www/livemanager
sudo chown -R livemanager:livemanager /var/log/livemanager
```

#### **2. Port 80 bloqué**
```bash
# Vérifier le firewall
sudo ufw status
sudo iptables -L

# Autoriser le port 80
sudo ufw allow 80
```

#### **3. Service Django ne démarre pas**
```bash
# Vérifier les logs
sudo journalctl -u livemanager -n 50

# Tester manuellement
cd /var/www/livemanager
source venv/bin/activate
gunicorn --bind 0.0.0.0:8000 livemanager.wsgi:application
```

#### **4. Base de données non accessible**
```bash
# Tester la connexion PostgreSQL
sudo -u postgres psql -c "\l"
psql -h localhost -U livemanager -d livemanager_db
```

### 📞 Support

Si les problèmes persistent :

1. **Collecter les logs** :
```bash
sudo journalctl -u livemanager --no-pager > livemanager.log
sudo tail -n 100 /var/log/nginx/error.log > nginx_error.log
```

2. **Vérifier la configuration** :
```bash
nginx -t
python manage.py check
```

3. **Redémarrer tous les services** :
```bash
sudo systemctl restart nginx
sudo systemctl restart livemanager
sudo systemctl restart postgresql
sudo systemctl restart redis-server
```

### ✅ Checklist de Vérification

- [ ] Services démarrés (nginx, livemanager, postgresql, redis)
- [ ] Firewall configuré (ports 80, 443, 22)
- [ ] Nginx configuration valide
- [ ] Django accessible localement
- [ ] Base de données connectée
- [ ] Fichiers statiques collectés
- [ ] Permissions correctes
- [ ] Variables d'environnement configurées

**Une fois ces étapes terminées, votre site devrait être accessible sur http://91.108.112.77** 🚀 