#!/bin/bash

echo "🚀 Démarrage de l'application..."

# Appliquer les migrations
echo "📦 Migrations..."
python manage.py migrate --noinput

# Initialiser les banques
echo "🏦 Initialisation des banques..."
python manage.py init_banks

# Créer le superutilisateur
echo "👤 Création du superutilisateur..."
python create_superuser.py

echo "✅ Prêt! Démarrage du serveur..."

# Démarrer gunicorn
gunicorn banking_system.wsgi:application --bind 0.0.0.0:8080 --workers 2
