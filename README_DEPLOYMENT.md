# 🚀 Guide de Déploiement LiveManager sur VPS Hostinger

Ce guide vous accompagne pour déployer LiveManager sur un VPS Hostinger avec un système CI/CD complet.

## 📋 Prérequis

- Un VPS Hostinger avec Ubuntu 20.04+ ou Debian 11+
- Un domaine configuré pointant vers votre VPS
- Un compte GitHub avec votre repository
- Accès SSH à votre VPS

## 🔧 Configuration Initiale du VPS

### 1. Connexion au VPS

```bash
ssh root@votre-ip-vps
```

### 2. Exécution du script de configuration

```bash
# Télécharger le script
wget https://raw.githubusercontent.com/votre-username/livemanager/main/setup_vps.sh
chmod +x setup_vps.sh

# Exécuter le script
./setup_vps.sh
```

Ce script va :
- ✅ Mettre à jour le système
- ✅ Installer tous les paquets nécessaires (Python, Nginx, PostgreSQL, Redis, FFmpeg)
- ✅ Configurer le firewall (UFW)
- ✅ Configurer PostgreSQL et Redis
- ✅ Créer l'utilisateur `livemanager`
- ✅ Configurer Nginx et Fail2ban
- ✅ Optimiser les performances
- ✅ Créer les scripts de maintenance

### 3. Connexion en tant qu'utilisateur application

```bash
ssh livemanager@votre-ip-vps
```

## 🔑 Configuration GitHub Actions

### 1. Secrets GitHub

Dans votre repository GitHub, allez dans **Settings > Secrets and variables > Actions** et ajoutez :

```
VPS_HOST=votre-ip-vps
VPS_USERNAME=livemanager
VPS_SSH_KEY=votre-clé-ssh-privée
VPS_PORT=22
```

### 2. Génération de clé SSH

```bash
# Sur votre machine locale
ssh-keygen -t rsa -b 4096 -C "github-actions"
# Copier la clé publique sur le VPS
ssh-copy-id -i ~/.ssh/id_rsa.pub livemanager@votre-ip-vps
# Ajouter la clé privée dans GitHub Secrets
```

## 🌐 Configuration du Domaine

### 1. DNS

Configurez vos DNS pour pointer vers votre VPS :
```
A    votre-domaine.com    votre-ip-vps
A    www.votre-domaine.com    votre-ip-vps
```

### 2. SSL avec Let's Encrypt

```bash
# Installer le certificat SSL
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com

# Renouvellement automatique
sudo crontab -e
# Ajouter : 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📦 Déploiement Manuel

### 1. Cloner le repository

```bash
cd /var/www/livemanager
git clone https://github.com/votre-username/livemanager.git .
```

### 2. Configuration des variables d'environnement

```bash
cp env.example .env
nano .env
```

**Variables importantes à configurer :**
```bash
DEBUG=False
SECRET_KEY=votre-clé-secrète-très-longue
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
DATABASE_URL=postgresql://livemanager:motdepasse_securise@localhost:5432/livemanager_db
```

### 3. Déploiement

```bash
chmod +x deploy.sh
./deploy.sh
```

## 🔄 Déploiement Automatique (CI/CD)

### 1. Workflow GitHub Actions

Le fichier `.github/workflows/deploy.yml` est configuré pour :

- ✅ Exécuter les tests automatiquement
- ✅ Vérifier le formatage du code
- ✅ Déployer automatiquement sur push vers `main`
- ✅ Créer des backups avant déploiement
- ✅ Redémarrer les services

### 2. Déclenchement

Le déploiement se déclenche automatiquement quand vous :
- Poussez sur la branche `main`
- Créez une Pull Request vers `main`

## 🛠️ Gestion des Services

### Commandes utiles

```bash
# Status des services
livemanager-status

# Redémarrer Django
sudo systemctl restart livemanager

# Redémarrer Nginx
sudo systemctl restart nginx

# Voir les logs Django
sudo journalctl -u livemanager -f

# Voir les logs Nginx
sudo tail -f /var/log/nginx/livemanager_error.log

# Status du firewall
sudo ufw status

# Status Fail2ban
sudo fail2ban-client status
```

### Maintenance

```bash
# Maintenance manuelle
sudo /usr/local/bin/livemanager-maintenance.sh

# Maintenance automatique (tous les jours à 2h du matin)
# Configurée automatiquement par setup_vps.sh
```

## 📊 Monitoring

### 1. Logs

- **Django** : `/var/log/livemanager/django.log`
- **Nginx** : `/var/log/nginx/livemanager_*.log`
- **Systemd** : `sudo journalctl -u livemanager`

### 2. Métriques

```bash
# Utilisation disque
df -h /var/www/livemanager

# Utilisation mémoire
free -h

# Processus
htop

# Connexions PostgreSQL
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
```

## 🔒 Sécurité

### 1. Firewall (UFW)

```bash
# Status
sudo ufw status

# Ajouter une règle
sudo ufw allow 8080

# Supprimer une règle
sudo ufw delete allow 8080
```

### 2. Fail2ban

```bash
# Status
sudo fail2ban-client status

# Voir les IP bannies
sudo fail2ban-client status nginx-http-auth

# Débannir une IP
sudo fail2ban-client set nginx-http-auth unbanip IP_ADDRESS
```

### 3. Mises à jour

```bash
# Mise à jour automatique
sudo apt update && sudo apt upgrade -y

# Mise à jour de sécurité uniquement
sudo unattended-upgrades
```

## 🚨 Dépannage

### Problèmes courants

#### 1. Service Django ne démarre pas

```bash
# Vérifier les logs
sudo journalctl -u livemanager -f

# Vérifier les permissions
sudo chown -R www-data:www-data /var/www/livemanager

# Vérifier le fichier .env
sudo -u www-data cat /var/www/livemanager/.env
```

#### 2. Erreur 502 Bad Gateway

```bash
# Vérifier que Django tourne
sudo systemctl status livemanager

# Vérifier le socket
ls -la /var/www/livemanager/livemanager.sock

# Redémarrer les services
sudo systemctl restart livemanager nginx
```

#### 3. Problème de base de données

```bash
# Vérifier PostgreSQL
sudo systemctl status postgresql

# Se connecter à la base
sudo -u postgres psql -d livemanager_db

# Vérifier les migrations
cd /var/www/livemanager
source venv/bin/activate
python manage.py showmigrations
```

#### 4. Problème de fichiers statiques

```bash
# Recollecter les fichiers statiques
cd /var/www/livemanager
source venv/bin/activate
python manage.py collectstatic --noinput

# Vérifier les permissions
sudo chown -R www-data:www-data /var/www/livemanager/staticfiles
```

## 📈 Optimisation

### 1. Performance Nginx

```bash
# Activer la compression
sudo nano /etc/nginx/nginx.conf
# Ajouter dans http {} :
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
```

### 2. Cache Redis

```bash
# Vérifier Redis
redis-cli ping

# Statistiques Redis
redis-cli info memory
```

### 3. Base de données

```bash
# Analyser les requêtes lentes
sudo -u postgres psql -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

## 🔄 Rollback

### 1. Restaurer depuis un backup

```bash
# Lister les backups
ls -la /var/backups/livemanager/

# Restaurer un backup
cd /var/www/livemanager
sudo tar -xzf /var/backups/livemanager/backup_YYYYMMDD_HHMMSS.tar.gz

# Redémarrer les services
sudo systemctl restart livemanager nginx
```

### 2. Restaurer la base de données

```bash
# Restaurer depuis un dump
sudo -u postgres psql livemanager_db < /var/backups/livemanager/db_backup_YYYYMMDD_HHMMSS.sql
```

## 📞 Support

En cas de problème :

1. ✅ Vérifiez les logs : `sudo journalctl -u livemanager -f`
2. ✅ Vérifiez le status : `livemanager-status`
3. ✅ Redémarrez les services : `sudo systemctl restart livemanager nginx`
4. ✅ Consultez ce guide de dépannage

## 🎯 Checklist de Déploiement

- [ ] VPS configuré avec `setup_vps.sh`
- [ ] Domaine configuré et SSL installé
- [ ] Repository GitHub configuré avec les secrets
- [ ] Variables d'environnement configurées
- [ ] Premier déploiement réussi
- [ ] Tests fonctionnels passés
- [ ] Monitoring configuré
- [ ] Backups automatiques actifs
- [ ] Maintenance automatique configurée

---

**🎉 Félicitations ! Votre application LiveManager est maintenant déployée et opérationnelle !** 