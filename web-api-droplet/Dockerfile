FROM python:3.9-slim

# Install system dependencies needed for psycopg2 (PostgreSQL)
# and GCC needed for TensorFlow dependencies
RUN apt-get update && apt-get install -y     gcc     python3-dev     libpq-dev     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files (including app.py and gunicorn.conf.py)
COPY app.py .
COPY gunicorn.conf.py .

# Command to run the application using Gunicorn and the new config file
CMD ["gunicorn", "-c", "gunicorn.conf.py", "--bind", "0.0.0.0:5000", "app:app"]
