#!/bin/bash

# Script de diagnostic rapide pour LiveManager
# Usage: ./diagnostic.sh

echo "🔍 Diagnostic LiveManager - $(date)"
echo "=================================="

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Fonctions
check_service() {
    local service=$1
    local status=$(systemctl is-active $service 2>/dev/null)
    if [ "$status" = "active" ]; then
        echo -e "${GREEN}✅ $service: ACTIF${NC}"
    else
        echo -e "${RED}❌ $service: INACTIF${NC}"
        echo -e "${YELLOW}   Logs: sudo journalctl -u $service -n 10${NC}"
    fi
}

check_port() {
    local port=$1
    local service=$2
    if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        echo -e "${GREEN}✅ Port $port ($service): OUVERT${NC}"
    else
        echo -e "${RED}❌ Port $port ($service): FERMÉ${NC}"
    fi
}

echo ""
echo "📊 État des Services"
echo "-------------------"
check_service "nginx"
check_service "postgresql"
check_service "redis-server"
check_service "livemanager"

echo ""
echo "🌐 Ports Ouverts"
echo "---------------"
check_port "80" "HTTP"
check_port "443" "HTTPS"
check_port "22" "SSH"
check_port "5432" "PostgreSQL"
check_port "6379" "Redis"

echo ""
echo "📁 Vérification des Répertoires"
echo "------------------------------"
if [ -d "/var/www/livemanager" ]; then
    echo -e "${GREEN}✅ /var/www/livemanager: EXISTE${NC}"
    echo "   Contenu: $(ls -la /var/www/livemanager | wc -l) fichiers"
else
    echo -e "${RED}❌ /var/www/livemanager: MANQUANT${NC}"
fi

if [ -d "/var/log/livemanager" ]; then
    echo -e "${GREEN}✅ /var/log/livemanager: EXISTE${NC}"
else
    echo -e "${RED}❌ /var/log/livemanager: MANQUANT${NC}"
fi

echo ""
echo "🔐 Vérification des Permissions"
echo "------------------------------"
if [ -w "/var/www/livemanager" ]; then
    echo -e "${GREEN}✅ Permissions /var/www/livemanager: OK${NC}"
else
    echo -e "${RED}❌ Permissions /var/www/livemanager: PROBLÈME${NC}"
fi

echo ""
echo "🌍 Test de Connexion Locale"
echo "---------------------------"
if curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Django local (port 8000): ACCESSIBLE${NC}"
else
    echo -e "${RED}❌ Django local (port 8000): INACCESSIBLE${NC}"
fi

if curl -s http://localhost > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Nginx local (port 80): ACCESSIBLE${NC}"
else
    echo -e "${RED}❌ Nginx local (port 80): INACCESSIBLE${NC}"
fi

echo ""
echo "🔥 État du Firewall"
echo "------------------"
ufw_status=$(sudo ufw status 2>/dev/null | head -1)
if echo "$ufw_status" | grep -q "Status: active"; then
    echo -e "${GREEN}✅ UFW: ACTIF${NC}"
    echo "   Règles:"
    sudo ufw status numbered 2>/dev/null | grep -E "(80|443|22)" || echo "   Aucune règle pour HTTP/HTTPS/SSH"
else
    echo -e "${YELLOW}⚠️  UFW: INACTIF${NC}"
fi

echo ""
echo "📋 Configuration Nginx"
echo "--------------------"
if [ -f "/etc/nginx/sites-enabled/livemanager" ]; then
    echo -e "${GREEN}✅ Site livemanager: CONFIGURÉ${NC}"
else
    echo -e "${RED}❌ Site livemanager: NON CONFIGURÉ${NC}"
fi

if nginx -t > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Configuration Nginx: VALIDE${NC}"
else
    echo -e "${RED}❌ Configuration Nginx: INVALIDE${NC}"
    echo -e "${YELLOW}   Erreur: nginx -t${NC}"
fi

echo ""
echo "🗄️ Base de Données"
echo "-----------------"
if sudo -u postgres psql -c "\l" 2>/dev/null | grep -q "livemanager_db"; then
    echo -e "${GREEN}✅ Base livemanager_db: EXISTE${NC}"
else
    echo -e "${RED}❌ Base livemanager_db: MANQUANTE${NC}"
fi

echo ""
echo "🔧 Variables d'Environnement"
echo "---------------------------"
if [ -f "/var/www/livemanager/.env" ]; then
    echo -e "${GREEN}✅ Fichier .env: EXISTE${NC}"
    if grep -q "DEBUG=False" /var/www/livemanager/.env 2>/dev/null; then
        echo -e "${GREEN}✅ DEBUG: False${NC}"
    else
        echo -e "${YELLOW}⚠️  DEBUG: True (ou non défini)${NC}"
    fi
else
    echo -e "${RED}❌ Fichier .env: MANQUANT${NC}"
fi

echo ""
echo "📊 Utilisation Système"
echo "--------------------"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Mémoire: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
echo "Disque: $(df -h /var/www/livemanager | awk 'NR==2{print $5}')"

echo ""
echo "🚨 Logs Récents (dernières 5 lignes)"
echo "-----------------------------------"
echo "Nginx Error:"
sudo tail -n 5 /var/log/nginx/error.log 2>/dev/null || echo "   Aucun log d'erreur"

echo ""
echo "Django:"
sudo journalctl -u livemanager -n 5 --no-pager 2>/dev/null || echo "   Aucun log Django"

echo ""
echo "🔧 Commandes de Résolution"
echo "-------------------------"
echo "1. Redémarrer les services:"
echo "   sudo systemctl restart nginx livemanager postgresql redis-server"
echo ""
echo "2. Vérifier les logs en temps réel:"
echo "   sudo journalctl -u livemanager -f"
echo "   sudo tail -f /var/log/nginx/error.log"
echo ""
echo "3. Tester Django manuellement:"
echo "   cd /var/www/livemanager && source venv/bin/activate"
echo "   python manage.py runserver 0.0.0.0:8000"
echo ""
echo "4. Vérifier la configuration:"
echo "   nginx -t"
echo "   python manage.py check"
echo ""
echo "5. Corriger les permissions:"
echo "   sudo chown -R livemanager:livemanager /var/www/livemanager"
echo "   sudo chmod -R 755 /var/www/livemanager"

echo ""
echo "📞 Si le problème persiste, consultez TROUBLESHOOTING.md"
echo "======================================================" 