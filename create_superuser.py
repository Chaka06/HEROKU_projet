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

# Créer admin si n'existe pas
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('✅ Superutilisateur admin créé')
else:
    print('ℹ️ Superutilisateur existe déjà')
