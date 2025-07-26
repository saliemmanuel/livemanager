# 🔧 Dépannage - Erreur d'Upload LiveManager

## 🚨 Erreur : "Erreur de connexion lors de l'upload"

Cette erreur peut avoir plusieurs causes. Suivez ce guide étape par étape.

---

## 🔍 Diagnostic Rapide

### 1️⃣ **Vérifier les logs Django**
```bash
# Sur le VPS
sudo journalctl -u livemanager -f

# Ou voir les derniers logs
sudo journalctl -u livemanager --no-pager -n 20
```

### 2️⃣ **Vérifier les logs Nginx**
```bash
# Logs d'erreur Nginx
sudo tail -f /var/log/nginx/error.log

# Logs d'accès
sudo tail -f /var/log/nginx/access.log
```

### 3️⃣ **Vérifier le statut des services**
```bash
# Statut des services
sudo systemctl status livemanager
sudo systemctl status nginx
sudo systemctl status postgresql
```

---

## 🛠️ Solutions par Cause

### ❌ **Problème 1 : Permissions insuffisantes**

**Symptômes :**
- Erreur 403 ou 500
- Fichiers non créés dans `/media/`

**Solution :**
```bash
# Corriger les permissions
sudo chown -R www-data:www-data /var/www/livemanager
sudo chmod -R 755 /var/www/livemanager
sudo chmod -R 775 /var/www/livemanager/media

# Créer le répertoire videos s'il n'existe pas
sudo mkdir -p /var/www/livemanager/media/videos
sudo chown -R www-data:www-data /var/www/livemanager/media
```

### ❌ **Problème 2 : FFmpeg non installé**

**Symptômes :**
- Erreur "FFmpeg not found"
- Compression échoue

**Solution :**
```bash
# Installer FFmpeg
sudo ./install_ffmpeg.sh

# Ou manuellement
sudo apt update
sudo apt install -y ffmpeg libavcodec-extra
```

### ❌ **Problème 3 : Espace disque insuffisant**

**Symptômes :**
- Erreur "No space left on device"
- Upload s'arrête en cours

**Solution :**
```bash
# Vérifier l'espace disque
df -h

# Nettoyer les fichiers temporaires
sudo find /tmp -type f -mtime +1 -delete
sudo find /var/www/livemanager/media -name "*.tmp" -delete
```

### ❌ **Problème 4 : Taille de fichier trop grande**

**Symptômes :**
- Upload échoue après un certain temps
- Erreur de timeout

**Solution :**
```bash
# Augmenter les limites dans Django
# Dans livemanager/settings.py, ajouter :
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB

# Redémarrer Django
sudo systemctl restart livemanager
```

### ❌ **Problème 5 : Configuration Nginx incorrecte**

**Symptômes :**
- Erreur 413 (Request Entity Too Large)
- Upload échoue immédiatement

**Solution :**
```bash
# Modifier la configuration Nginx
sudo nano /etc/nginx/sites-available/livemanager

# Ajouter ces lignes dans le bloc server :
client_max_body_size 500M;
client_body_timeout 300s;
client_header_timeout 300s;

# Tester et recharger
sudo nginx -t
sudo systemctl reload nginx
```

### ❌ **Problème 6 : Base de données**

**Symptômes :**
- Erreur de base de données
- Upload échoue après traitement

**Solution :**
```bash
# Vérifier PostgreSQL
sudo systemctl status postgresql

# Appliquer les migrations
cd /var/www/livemanager
source venv/bin/activate
python manage.py migrate

# Vérifier la base de données
python manage.py check
```

---

## 🔧 Script de Diagnostic Automatique

Exécutez le script de diagnostic pour identifier automatiquement le problème :

```bash
# Télécharger et exécuter
wget https://raw.githubusercontent.com/saliemmanuel/livemanager/main/debug_upload.py
python3 debug_upload.py
```

---

## 📱 Diagnostic Côté Client

### 1️⃣ **Vérifier la console du navigateur**
1. Ouvrir les outils de développement (F12)
2. Aller dans l'onglet "Console"
3. Reproduire l'erreur
4. Noter les messages d'erreur

### 2️⃣ **Tester avec un fichier plus petit**
- Essayer avec un fichier < 10MB
- Vérifier si le problème persiste

### 3️⃣ **Vérifier la connexion internet**
- Tester la vitesse de connexion
- Vérifier la stabilité de la connexion

---

## 🚀 Solutions Avancées

### **Redémarrage complet**
```bash
# Redémarrer tous les services
sudo systemctl restart postgresql
sudo systemctl restart redis-server
sudo systemctl restart livemanager
sudo systemctl restart nginx

# Vérifier les statuts
sudo systemctl status postgresql redis-server livemanager nginx
```

### **Réinstallation FFmpeg**
```bash
# Désinstaller et réinstaller FFmpeg
sudo apt remove --purge ffmpeg
sudo apt autoremove
sudo ./install_ffmpeg.sh
```

### **Nettoyage complet**
```bash
# Nettoyer les fichiers temporaires
sudo find /var/www/livemanager/media -name "*.tmp" -delete
sudo find /tmp -name "*livemanager*" -delete

# Redémarrer les services
sudo systemctl restart livemanager nginx
```

---

## 📞 Support

Si le problème persiste après avoir essayé toutes ces solutions :

1. **Collecter les informations :**
   ```bash
   # Logs complets
   sudo journalctl -u livemanager --no-pager -n 50 > livemanager_logs.txt
   sudo tail -n 50 /var/log/nginx/error.log > nginx_errors.txt
   
   # Configuration
   sudo cat /etc/nginx/sites-available/livemanager > nginx_config.txt
   ```

2. **Fournir :**
   - Les fichiers de logs collectés
   - Le message d'erreur exact
   - La taille du fichier testé
   - Le navigateur utilisé

---

## ✅ Checklist de Vérification

- [ ] Service livemanager actif
- [ ] Service nginx actif
- [ ] Service postgresql actif
- [ ] Permissions correctes sur /media/
- [ ] FFmpeg installé et fonctionnel
- [ ] Espace disque suffisant
- [ ] Configuration Nginx correcte
- [ ] Migrations Django appliquées
- [ ] Pas d'erreurs dans les logs
- [ ] Fichier de test < 10MB

**Si tous les points sont cochés et que le problème persiste, le problème vient probablement de la configuration réseau ou du navigateur.** 