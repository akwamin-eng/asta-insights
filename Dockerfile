FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scrape_youtube.py .

CMD ["python", "scrape_youtube.py"]