# 🚀 Guide Rapide - Compression Vidéo LiveManager

## 📋 Installation Rapide

### 1️⃣ Installer FFmpeg sur le VPS
```bash
# Télécharger et exécuter le script d'installation
wget https://raw.githubusercontent.com/saliemmanuel/livemanager/main/install_ffmpeg.sh
chmod +x install_ffmpeg.sh
sudo ./install_ffmpeg.sh
```

### 2️⃣ Tester l'installation
```bash
# Vérifier que tout fonctionne
python3 test_compression.py
```

### 3️⃣ Redémarrer les services
```bash
sudo systemctl restart livemanager
sudo systemctl restart nginx
```

---

## 🎯 Utilisation

### Upload avec Compression
1. **Connectez-vous** à votre compte LiveManager
2. **Allez sur** "Créer un Live"
3. **Sélectionnez** votre fichier vidéo (MP4 recommandé)
4. **La compression démarre automatiquement** dans votre navigateur
5. **Suivez la progression** avec les barres de progression
6. **L'upload commence** une fois la compression terminée

### Fonctionnalités
- ✅ **Compression automatique** : Réduction de 50-70% de la taille
- ✅ **Interface moderne** : Drag & drop, barres de progression
- ✅ **Mode sombre** : Compatible avec le thème de l'app
- ✅ **Optimisation web** : Format compatible avec tous les navigateurs

---

## 🔧 Dépannage

### Problème : "FFmpeg non trouvé"
```bash
# Solution
sudo ./install_ffmpeg.sh
```

### Problème : "Erreur de compression"
```bash
# Vérifier les permissions
sudo chown -R www-data:www-data /var/www/livemanager/media
sudo chmod -R 755 /var/www/livemanager/media
```

### Problème : "Upload échoue"
```bash
# Vérifier les logs
sudo journalctl -u livemanager -f
```

---

## 📊 Statistiques

### Performances Typiques
- **Vidéo HD (1080p)** : 50-60% de réduction
- **Vidéo 4K** : 60-80% de réduction
- **Temps de compression** : 1-3 minutes
- **Temps d'upload** : Réduit de 50-70%

### Formats Supportés
- ✅ **Entrée** : MP4, AVI, MOV, MKV, WMV
- ✅ **Sortie** : MP4 optimisé pour le web
- ✅ **Codecs** : H.264 vidéo, AAC audio

---

## 🎛️ Configuration Avancée

### Paramètres de Qualité
```python
# Dans streams/views.py - Ajuster la qualité
'-crf': '23'  # 18-28 (plus bas = meilleure qualité)
'-preset': 'medium'  # ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
```

### Limites
- **Taille max** : 500MB par fichier
- **Durée max** : Pas de limite (selon la taille)
- **Formats** : Tous les formats vidéo courants

---

## 🔍 Monitoring

### Vérifier les Logs
```bash
# Logs Django
sudo journalctl -u livemanager -f

# Logs Nginx
sudo tail -f /var/log/nginx/error.log

# Logs FFmpeg
sudo journalctl -u livemanager | grep ffmpeg
```

### Statistiques d'Utilisation
```bash
# Espace disque utilisé
du -sh /var/www/livemanager/media/

# Nombre de fichiers
find /var/www/livemanager/media/ -name "*.mp4" | wc -l
```

---

## 🆘 Support

### Commandes Utiles
```bash
# Test complet du système
python3 test_compression.py

# Vérifier FFmpeg
ffmpeg -version

# Vérifier les codecs
ffmpeg -codecs | grep -E "(libx264|aac)"

# Redémarrer tout
sudo systemctl restart livemanager nginx postgresql redis-server
```

### En Cas de Problème
1. **Vérifiez les logs** : `sudo journalctl -u livemanager -f`
2. **Testez FFmpeg** : `ffmpeg -version`
3. **Vérifiez les permissions** : `ls -la /var/www/livemanager/media/`
4. **Redémarrez les services** : `sudo systemctl restart livemanager`

---

## 🎉 Résultat

Après l'installation, vous aurez :
- ✅ **Compression automatique** des vidéos
- ✅ **Upload plus rapide** (50-70% moins de données)
- ✅ **Économies de bande passante**
- ✅ **Meilleure compatibilité** web
- ✅ **Interface utilisateur moderne**

**Votre site est maintenant prêt pour la compression vidéo !** 🚀 