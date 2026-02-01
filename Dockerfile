# Dockerfile pour Fly.io
FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements et installer
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copier le projet
COPY . .

# Collecter les fichiers statiques
RUN python manage.py collectstatic --noinput

# Script de démarrage
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Exposer le port
EXPOSE 8080

# Commande de démarrage
CMD ["/start.sh"]
