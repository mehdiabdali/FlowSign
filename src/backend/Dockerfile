FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download fr_core_news_lg

COPY . .

EXPOSE 5000

CMD ["python", "main.py"]