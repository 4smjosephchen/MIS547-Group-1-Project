FROM python:3.9-slim

# 1. Install System Dependencies (Chromium, Drivers, Cron, Build Tools)
RUN apt-get update && apt-get install -y     chromium     chromium-driver     fonts-liberation     fonts-ipafont-gothic     fonts-wqy-zenhei     libnss3     libxss1     libpq-dev gcc     cron     --no-install-recommends &&     rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Install Python Libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy All Scripts and Configs
COPY collect_data.py .
COPY earthquake_scraper.py .
COPY process_data.py .
COPY run_pipeline.py .
COPY biweekly_cron /etc/cron.d/biweekly_job

# 4. Configure Cron
RUN chmod 0644 /etc/cron.d/biweekly_job &&     crontab /etc/cron.d/biweekly_job &&     touch /var/log/pipeline.log

# 5. Start Cron in Foreground
CMD ["cron", "-f"]
