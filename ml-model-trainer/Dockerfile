FROM python:3.9-slim

# Install system utilities (Cron + Build tools)
RUN apt-get update && apt-get install -y --no-install-recommends     cron     gcc     python3-dev     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Scripts and Configs
COPY train.py .
COPY biweekly_cron /etc/cron.d/biweekly_training
COPY entrypoint.sh .

# Setup Permissions
RUN chmod 0644 /etc/cron.d/biweekly_training &&     crontab /etc/cron.d/biweekly_training &&     chmod +x entrypoint.sh &&     touch /var/log/training.log

# Use the custom entrypoint
CMD ["/app/entrypoint.sh"]
