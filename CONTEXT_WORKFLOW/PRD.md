# 📺 Sarki - LiveManager (Django + FFmpeg)

## 🎯 Objectif

Créer une application web nommée **LiveManager**, développée avec **Django**, permettant à des **utilisateurs approuvés** de diffuser en direct des **vidéos préenregistrées** sur des plateformes comme **YouTube Live**, à l’aide de **FFmpeg**, depuis un **VPS Hostinger**.

Les lives peuvent être :
- programmés à l’avance pour démarrer automatiquement,
- ou lancés manuellement via l’interface utilisateur.

---

## 👥 Rôles

### 👑 Admin
- Gère les utilisateurs (`is_approved`)
- Reçoit une notification email lors du lancement d’un live
- Consulte la liste complète des utilisateurs et des lives

### 🙋‍♂️ Utilisateur
- Crée un compte
- Ne peut pas diffuser tant qu’il n’est pas approuvé
- Une fois validé :
  - Crée un live
  - Téléverse une vidéo MP4
  - Fournit une clé de diffusion
  - Choisit entre un démarrage manuel ou programmé

---

## 🔐 Authentification

- Basée sur `django.contrib.auth`
- Extension du modèle utilisateur avec :
  - `is_admin` : booléen
  - `is_approved` : booléen

---

## 🧱 Modèles de données

### `User`
- Champs : `id`, `email`, `password`, `is_admin`, `is_approved`

### `Live`
| Champ         | Type         | Description                                       |
|---------------|--------------|---------------------------------------------------|
| `user`        | ForeignKey   | Créateur du live                                 |
| `title`       | CharField    | Titre du live                                    |
| `video_file`  | FileField    | Vidéo MP4                                         |
| `stream_key`  | CharField    | Clé de stream (ex: YouTube)                      |
| `scheduled_at`| DateTime     | Heure prévue (nullable)                          |
| `is_scheduled`| Boolean      | Live automatique ou non                          |
| `status`      | ChoiceField  | `pending`, `running`, `completed`, `failed`     |
| `ffmpeg_pid`  | IntegerField | PID du processus FFmpeg                          |

---

## 🎮 Fonctionnalités principales

### ➕ Création d’un live
- Formulaire avec :
  - Titre
  - Vidéo
  - Clé de stream
  - Lancement automatique activé ou non
  - Date/heure prévue (si applicable)

### ▶️ Lancement
- Si `is_scheduled = True` : via tâche planifiée (Celery ou cron)
- Sinon : via bouton manuel

**Commande FFmpeg utilisée** :
```bash
setsid ffmpeg -re -stream_loop -1 -i "/path/to/video.mp4" \
  -c:v libx264 -preset ultrafast -b:v 500k -maxrate 800k -bufsize 1200k \
  -s 640x360 -g 60 -keyint_min 60 \
  -c:a aac -b:a 96k \
  -f flv -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 2 \
  "rtmp://a.rtmp.youtube.com/live2/clé"
```

### ⏹️ Arrêt d’un live
- Commande : `kill -9 {PID}`
- Statut mis à jour dans la base

---

## 📬 Notifications email
- À l’utilisateur : confirmation ou échec du live
- À l’admin : alerte au lancement

---

## 🖥️ Interface Utilisateur

Conçue avec **shadcn UI** (React + Tailwind CSS) intégrée à Django :

- Design moderne, responsive et thème sombre par défaut
- `django-tailwind` + `django-webpack-loader` pour intégration

### Utilisateur :
- Dashboard avec :
  - Statut de validation
  - Bouton “Créer un live”
  - Liste des lives : titre, statut, heure, actions ▶️ ⏹️

### Admin :
- Liste des utilisateurs avec validation
- Liste de tous les lives

---

## 🔄 CI/CD & Déploiement sur VPS (Hostinger)

Un pipeline **CI/CD (GitHub Actions)** sera mis en place pour :

1. **Tester** automatiquement les modèles, vues et processus de lancement
2. **Builder** le projet (collectstatic, migrate, etc.)
3. **Déployer automatiquement** sur un **VPS Hostinger (Ubuntu/Debian)** via :
   - Connexion SSH avec clé privée
   - Commandes `rsync` ou `scp` pour mise à jour du code
   - Redémarrage automatique des services (`gunicorn`, `celery`, `supervisor`, etc.)

Exemples de tâches automatisées :
- `python manage.py test`
- `python manage.py collectstatic --noinput`
- `python manage.py migrate`
- Redémarrage via : `sudo systemctl restart live-manager`

---

## 🛠️ Technologies Utilisées

- Django 5.x (Python 3.11+)
- PostgreSQL / MySQL
- FFmpeg (serveur VPS)
- Celery + Redis (tâches planifiées)
- Supervisor / Systemd (gestion des processus)
- Mailtrap / SMTP (emails)
- shadcn UI (React + Tailwind)
- GitHub Actions (CI/CD)
- VPS Hostinger (Linux)

---

## 📦 Lancement local

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## 📌 À venir

- Authentification sociale (Google, etc.)
- Page publique de visionnage live
- API publique REST (DRF)
- Intégration WebSocket pour statut en temps réel
