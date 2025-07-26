# 📺 LiveManager - Plateforme de Diffusion en Direct

[![Django](https://img.shields.io/badge/Django-5.0.2-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue.svg)](.github/workflows/deploy.yml)

> **LiveManager** est une plateforme moderne de diffusion en direct pour YouTube Live, permettant de créer, programmer et gérer des lives avec facilité. Idéal pour les créateurs de contenu, streamers et entreprises.

## 🌟 Fonctionnalités

### 🎬 **Diffusion en Direct**
- **Upload de vidéos** : Support des formats MP4, AVI, MOV
- **Diffusion automatique** : Intégration FFmpeg pour YouTube Live
- **Clés de stream** : Gestion sécurisée des clés YouTube
- **Statut en temps réel** : Monitoring des lives actifs

### ⏰ **Programmation Avancée**
- **Lives programmés** : Planification à l'avance
- **Démarrage automatique** : Exécution selon planning
- **Gestion des fuseaux horaires** : Support international
- **Notifications** : Alertes avant démarrage

### 👥 **Gestion des Utilisateurs**
- **Système d'approbation** : Contrôle admin des comptes
- **Rôles utilisateurs** : Admin, Utilisateur approuvé, En attente
- **Interface d'administration** : Gestion complète des comptes
- **Statistiques** : Dashboard avec métriques

### 🎨 **Interface Moderne**
- **Design responsive** : Compatible mobile et desktop
- **Thème clair/sombre** : Changement dynamique
- **Tailwind CSS** : Interface moderne et élégante
- **UX optimisée** : Navigation intuitive

### 🔒 **Sécurité**
- **Authentification Django** : Système robuste
- **CSRF Protection** : Sécurité renforcée
- **Permissions granulaires** : Contrôle d'accès
- **Validation des données** : Intégrité garantie

## 🚀 Démarrage Rapide

### Prérequis

- **Python** 3.11+
- **FFmpeg** (pour la diffusion)
- **Git**

### Installation

```bash
# Cloner le repository
git clone https://github.com/votre-username/livemanager.git
cd livemanager

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp env.example .env
# Éditer .env avec vos configurations

# Appliquer les migrations
python manage.py migrate

# Créer un superuser
python manage.py createsuperuser

# Collecter les fichiers statiques
python manage.py collectstatic

# Lancer le serveur
python manage.py runserver
```

### Configuration FFmpeg

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Télécharger depuis https://ffmpeg.org/download.html
```

## 🏗️ Architecture

### Structure du Projet

```
livemanager/
├── livemanager/          # Configuration Django
│   ├── settings.py      # Paramètres de l'application
│   ├── urls.py          # URLs principales
│   └── wsgi.py          # Configuration WSGI
├── streams/             # Application principale
│   ├── models.py        # Modèles de données
│   ├── views.py         # Logique métier
│   ├── forms.py         # Formulaires
│   ├── admin.py         # Interface d'administration
│   └── tasks.py         # Tâches asynchrones
├── templates/           # Templates HTML
│   ├── base.html        # Template de base
│   └── streams/         # Templates spécifiques
├── static/              # Fichiers statiques
├── media/               # Fichiers uploadés
└── requirements.txt     # Dépendances Python
```

### Modèles de Données

#### User (Utilisateur)
- `username` : Nom d'utilisateur unique
- `email` : Adresse email
- `is_admin` : Statut administrateur
- `is_approved` : Statut d'approbation
- `date_joined` : Date d'inscription

#### Live (Diffusion)
- `user` : Utilisateur propriétaire
- `title` : Titre du live
- `video_file` : Fichier vidéo
- `stream_key` : Clé de diffusion YouTube
- `scheduled_at` : Date de programmation
- `status` : Statut (pending, running, completed, error)
- `ffmpeg_pid` : PID du processus FFmpeg

## 🎯 Utilisation

### Pour les Utilisateurs

1. **Inscription** : Créer un compte sur la plateforme
2. **Attente d'approbation** : Validation par l'administrateur
3. **Création de live** : Upload vidéo + configuration
4. **Programmation** : Choix entre démarrage manuel ou programmé
5. **Diffusion** : Démarrage automatique sur YouTube Live

### Pour les Administrateurs

1. **Dashboard admin** : Vue d'ensemble de la plateforme
2. **Gestion utilisateurs** : Approbation, rejet, promotion admin
3. **Monitoring lives** : Suivi des diffusions actives
4. **Statistiques** : Métriques d'utilisation

## 🔧 Configuration

### Variables d'Environnement

```bash
# Configuration Django
DEBUG=False
SECRET_KEY=votre-clé-secrète
ALLOWED_HOSTS=votre-domaine.com

# Base de données
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True

# FFmpeg
FFMPEG_PATH=/usr/bin/ffmpeg

# Sécurité
CSRF_TRUSTED_ORIGINS=https://votre-domaine.com
```

### Base de Données

```bash
# PostgreSQL (recommandé)
sudo -u postgres createdb livemanager_db
sudo -u postgres createuser livemanager
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE livemanager_db TO livemanager;"

# SQLite (développement)
# Aucune configuration supplémentaire requise
```

## 🚀 Déploiement

### Déploiement Automatique (CI/CD)

Le projet inclut un système CI/CD complet avec GitHub Actions :

```bash
# 1. Configurer les secrets GitHub
VPS_HOST=votre-ip-vps
VPS_USERNAME=livemanager
VPS_SSH_KEY=votre-clé-ssh

# 2. Pousser sur main → Déploiement automatique !
git push origin main
```

### Déploiement Manuel

```bash
# Script de déploiement
chmod +x deploy.sh
./deploy.sh
```

📖 **Guide complet** : [README_DEPLOYMENT.md](README_DEPLOYMENT.md)

## 🧪 Tests

```bash
# Exécuter tous les tests
python manage.py test

# Tests avec couverture
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 📊 API Endpoints

### Authentification
- `POST /login/` - Connexion utilisateur
- `POST /logout/` - Déconnexion
- `POST /register/` - Inscription

### Dashboard
- `GET /dashboard/` - Dashboard utilisateur
- `GET /admin-dashboard/` - Dashboard administrateur
- `GET /admin-users/` - Gestion utilisateurs

### Lives
- `GET /create-live/` - Formulaire création live
- `POST /create-live/` - Créer un live
- `POST /live/{id}/start/` - Démarrer un live
- `POST /live/{id}/stop/` - Arrêter un live

### Administration
- `POST /approve-user/{id}/` - Approuver utilisateur
- `POST /reject-user/{id}/` - Rejeter utilisateur
- `POST /toggle-admin/{id}/` - Changer statut admin
- `POST /delete-user/{id}/` - Supprimer utilisateur

## 🔒 Sécurité

### Mesures Implémentées

- ✅ **CSRF Protection** : Protection contre les attaques CSRF
- ✅ **Validation des données** : Validation côté serveur
- ✅ **Permissions granulaires** : Contrôle d'accès par rôle
- ✅ **Authentification sécurisée** : Sessions Django sécurisées
- ✅ **Validation des fichiers** : Vérification des uploads
- ✅ **Logs de sécurité** : Traçabilité des actions

### Bonnes Pratiques

```python
# Exemple de validation de fichier
def validate_video_file(file):
    if file.size > 500 * 1024 * 1024:  # 500MB max
        raise ValidationError("Fichier trop volumineux")
    
    if not file.name.endswith('.mp4'):
        raise ValidationError("Format non supporté")
```

## 🤝 Contribution

### Comment Contribuer

1. **Fork** le projet
2. **Créer** une branche feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** vos changements (`git commit -m 'Add AmazingFeature'`)
4. **Push** vers la branche (`git push origin feature/AmazingFeature`)
5. **Ouvrir** une Pull Request

### Standards de Code

```bash
# Formatage automatique
pip install black flake8
black .
flake8 .

# Tests avant commit
python manage.py test
```

## 📈 Roadmap

### Version 1.1
- [ ] Support multi-plateformes (Twitch, Facebook Live)
- [ ] API REST complète
- [ ] Notifications push
- [ ] Analytics avancées

### Version 1.2
- [ ] Interface mobile native
- [ ] Intégration OAuth
- [ ] Système de plugins
- [ ] Support multi-langues

### Version 2.0
- [ ] Architecture microservices
- [ ] Support Kubernetes
- [ ] IA pour optimisation
- [ ] Marketplace d'extensions

## 🐛 Dépannage

### Problèmes Courants

#### FFmpeg non trouvé
```bash
# Vérifier l'installation
ffmpeg -version

# Ajouter au PATH si nécessaire
export PATH=$PATH:/usr/local/bin/ffmpeg
```

#### Erreur de permissions
```bash
# Corriger les permissions
sudo chown -R www-data:www-data /var/www/livemanager
sudo chmod -R 755 /var/www/livemanager
```

#### Problème de base de données
```bash
# Vérifier les migrations
python manage.py showmigrations
python manage.py migrate --fake-initial
```

## 📞 Support

### Ressources

- 📖 **Documentation** : [Wiki du projet](https://github.com/votre-username/livemanager/wiki)
- 🐛 **Issues** : [GitHub Issues](https://github.com/votre-username/livemanager/issues)
- 💬 **Discussions** : [GitHub Discussions](https://github.com/votre-username/livemanager/discussions)
- 📧 **Email** : support@livemanager.com

### Communauté

- **Discord** : [Serveur LiveManager](https://discord.gg/livemanager)
- **Twitter** : [@LiveManagerApp](https://twitter.com/LiveManagerApp)
- **Blog** : [Blog officiel](https://blog.livemanager.com)

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- **Django** : Framework web puissant
- **FFmpeg** : Traitement vidéo
- **Tailwind CSS** : Framework CSS
- **YouTube Live API** : Intégration streaming
- **Communauté open source** : Contributions et feedback

---

<div align="center">

**🌟 Si ce projet vous plaît, n'oubliez pas de le ⭐ star sur GitHub !**

**📺 LiveManager** - Simplifiez vos diffusions en direct

[![GitHub stars](https://img.shields.io/github/stars/votre-username/livemanager?style=social)](https://github.com/votre-username/livemanager)
[![GitHub forks](https://img.shields.io/github/forks/votre-username/livemanager?style=social)](https://github.com/votre-username/livemanager)

</div> 