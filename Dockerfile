# Use a slim Python image
FROM python:3.12-slim

# Set environment variables to ensure Python output is sent to logs
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all engine code
COPY . .

# Expose the port Cloud Run uses
EXPOSE 8080

# Start the web server wrapper
CMD ["python", "main.py"]
