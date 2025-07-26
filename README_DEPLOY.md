# 🚀 Déploiement LiveManager - Guide Simple

## 📋 Prérequis

- Un serveur VPS Ubuntu/Debian
- Un nom de domaine (optionnel, mais recommandé)
- Accès root au serveur

## 🎯 Déploiement en 3 Étapes

### 1️⃣ **Télécharger le script**
```bash
# Se connecter au serveur
ssh root@votre-ip-serveur

# Télécharger le script
wget https://raw.githubusercontent.com/saliemmanuel/livemanager/main/deploy.sh

# Rendre le script exécutable
chmod +x deploy.sh
```

### 2️⃣ **Lancer le déploiement**
```bash
# Exécuter le script
sudo ./deploy.sh
```

### 3️⃣ **Suivre les instructions**
Le script va :
- Demander votre nom de domaine
- Installer toutes les dépendances
- Configurer la base de données
- Déployer l'application
- Configurer SSL automatiquement
- Démarrer tous les services

## 🌐 Accès au Site

Une fois le déploiement terminé :

- **URL** : `http://votre-domaine.com` ou `https://votre-domaine.com`
- **Admin** : `admin`
- **Mot de passe** : `admin123`

## 🔧 Commandes Utiles

```bash
# Vérifier le statut des services
sudo systemctl status livemanager

# Redémarrer l'application
sudo systemctl restart livemanager

# Voir les logs
sudo journalctl -u livemanager -f

# Tester la configuration Nginx
sudo nginx -t

# Redémarrer Nginx
sudo systemctl restart nginx
```

## 🛠️ Fonctionnalités Incluses

- ✅ **Base de données PostgreSQL** configurée
- ✅ **Redis** pour les tâches asynchrones
- ✅ **Nginx** comme serveur web
- ✅ **SSL automatique** avec Let's Encrypt
- ✅ **Firewall UFW** configuré
- ✅ **Fail2ban** pour la sécurité
- ✅ **Services systemd** pour la gestion
- ✅ **Backups automatiques** des données

## 🔒 Sécurité

Le script configure automatiquement :
- Firewall UFW
- Fail2ban pour la protection
- SSL/TLS avec Let's Encrypt
- Headers de sécurité Nginx
- Permissions sécurisées

## 📞 Support

En cas de problème :
1. Vérifiez les logs : `sudo journalctl -u livemanager -f`
2. Testez Nginx : `sudo nginx -t`
3. Vérifiez les services : `sudo systemctl status livemanager`

**Votre site LiveManager sera en ligne en quelques minutes ! 🚀** 