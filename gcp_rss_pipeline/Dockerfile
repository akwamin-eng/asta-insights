# gcp_rss_pipeline/Dockerfile
# Use the official Python image from the Docker Hub
# https://hub.docker.com/_/python
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies specified in requirements.txt
# Using --no-cache-dir reduces image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set the command to run when the container starts
# This executes the rss_fetcher.py script
CMD ["python", "rss_fetcher.py"]
