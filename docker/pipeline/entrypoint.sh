#!/bin/bash
set -e

# Default cron schedule: hourly at minute 0
CRON_SCHEDULE="${CRON_SCHEDULE:-0 * * * *}"

# Data directory (default: /data)
DATA_DIR="${SOTD_DATA_DIR:-/data}"

# Log directory
LOG_DIR="${LOG_DIR:-/data/logs}"
mkdir -p "$LOG_DIR"

# Generate crontab with environment variables
echo "Generating crontab with schedule: $CRON_SCHEDULE"
{
    echo "# SOTD Pipeline Cron Schedule"
    echo "# Set PATH to include common binary locations (cron has minimal PATH)"
    echo "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    echo "# Set environment variables (cron doesn't inherit shell environment)"
    [ -n "$praw_client_id" ] && echo "praw_client_id=$praw_client_id"
    [ -n "$praw_client_secret" ] && echo "praw_client_secret=$praw_client_secret"
    [ -n "$praw_user_agent" ] && echo "praw_user_agent=$praw_user_agent"
    [ -n "$SOTD_DATA_DIR" ] && echo "SOTD_DATA_DIR=$SOTD_DATA_DIR"
    [ -n "$LOG_DIR" ] && echo "LOG_DIR=$LOG_DIR"
    echo "# Format: minute hour day month weekday"
    echo "$CRON_SCHEDULE /app/run-pipeline.sh >> $LOG_DIR/pipeline.log 2>&1"
    echo ""
} > /tmp/crontab

# Install crontab
crontab /tmp/crontab
rm /tmp/crontab

# Start cron daemon in foreground
echo "Starting cron daemon..."
echo "Pipeline will run on schedule: $CRON_SCHEDULE"
echo "Logs will be written to: $LOG_DIR/pipeline.log"
echo "Data directory: $DATA_DIR"

# Start cron
exec cron -f
