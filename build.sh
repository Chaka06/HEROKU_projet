#!/bin/bash

echo "🔧 Installation des dépendances..."
pip install -r requirements.txt

echo "📦 Compilation des fichiers statiques..."
python manage.py collectstatic --noinput

echo "🗄️ Migration de la base de données..."
python manage.py migrate

echo "🏦 Initialisation des banques..."
python manage.py init_banks

echo "👤 Création du superutilisateur..."
python create_superuser.py

echo "✅ Build terminé!"
