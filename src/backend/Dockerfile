FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download fr_core_news_sm

COPY . .

EXPOSE 5000

# Gunicorn remplace le serveur de dev Flask — 2 workers, adapté pour une petite instance
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "main:app"]