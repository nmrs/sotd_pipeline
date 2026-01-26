#!/bin/bash
set -e

# Default cron schedule: hourly at minute 0
CRON_SCHEDULE="${CRON_SCHEDULE:-0 * * * *}"

# Data directory (default: /data)
DATA_DIR="${SOTD_DATA_DIR:-/data}"

# Log directory
LOG_DIR="${LOG_DIR:-/data/logs}"
mkdir -p "$LOG_DIR"

# Generate crontab
echo "Generating crontab with schedule: $CRON_SCHEDULE"
cat > /tmp/crontab <<EOF
# SOTD Pipeline Cron Schedule
# Format: minute hour day month weekday
$CRON_SCHEDULE /app/run-pipeline.sh >> $LOG_DIR/pipeline.log 2>&1

# Empty line required at end of crontab
EOF

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
