#!/bin/bash

echo "=== Diagnostic de l'erreur 500 lors du login ==="
echo

echo "1. Vérification du service Django..."
systemctl status livemanager --no-pager
echo

echo "2. Vérification de la configuration Nginx..."
nginx -t
echo

echo "3. Configuration Nginx pour livemanager:"
cat /etc/nginx/sites-available/livemanager
echo

echo "4. Test de l'accès local:"
curl -I http://localhost/login/ 
echo

echo "5. Test direct avec le socket Unix:"
curl -I --unix-socket /var/www/livemanager/livemanager.sock http://localhost/login/
echo

echo "6. Logs Django récents:"
journalctl -u livemanager -n 10 --no-pager
echo

echo "7. Logs Nginx récents:"
tail -10 /var/log/nginx/error.log
echo

echo "8. Test Django en direct:"
cd /var/www/livemanager
source venv/bin/activate
python3 manage.py shell -c "from django.test import Client; c = Client(); r = c.get('/login/'); print(f'Status: {r.status_code}')"
echo

echo "=== Diagnostic terminé ===" 