# image interpreteur
FROM python:3.10-slim

# Maj/Installation du système nécessaires pour spaCy/NLP
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Répertoire de travail
WORKDIR /app

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Téléchargement du modèle spaCy (ajustez le nom du modèle si nécessaire)
RUN python -m spacy download fr_core_news_sm

# Copie de tout le code source du backend
COPY . .

# Exposition du port utilisé par votre API (3000 selon votre schéma)
EXPOSE 3000

# Commande de lancement (adapter si vous utilisez uvicorn, gunicorn ou flask)
CMD ["python", "main.py"]