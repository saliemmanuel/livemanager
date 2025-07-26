#!/bin/bash

# Script de pré-commit pour formater automatiquement le code
# Usage: ./pre-commit.sh

echo "🔧 Formatage automatique du code..."

# Vérifier si black est installé
if ! command -v black &> /dev/null; then
    echo "❌ Black n'est pas installé. Installation..."
    pip install black
fi

# Vérifier si flake8 est installé
if ! command -v flake8 &> /dev/null; then
    echo "❌ Flake8 n'est pas installé. Installation..."
    pip install flake8
fi

# Formater le code avec Black
echo "🎨 Formatage avec Black..."
black .

# Vérifier le style avec Flake8
echo "🔍 Vérification du style avec Flake8..."
flake8 .

if [ $? -eq 0 ]; then
    echo "✅ Code formaté et validé avec succès!"
    echo "🚀 Prêt pour le commit!"
else
    echo "❌ Erreurs de style détectées. Veuillez les corriger avant de commiter."
    exit 1
fi 