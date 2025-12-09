#!/bin/bash
# Save Docker environment variables so Cron can see them
printenv | grep -v "no_proxy" >> /etc/environment

# Start Cron in the foreground
cron -f
