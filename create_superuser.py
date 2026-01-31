#!/usr/bin/env python
"""
Script pour créer le superutilisateur au déploiement
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'banking_system.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Créer admin2 si n'existe pas
if not User.objects.filter(username='admin2').exists():
    User.objects.create_superuser('admin2', 'admin@flash-compte.com', '14217816A')
    print('✅ Superutilisateur admin2 créé avec mot de passe 14217816A')
else:
    print('ℹ️ Superutilisateur admin2 existe déjà')
