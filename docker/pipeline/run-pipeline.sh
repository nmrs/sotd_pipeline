#!/bin/bash
set -e

# Configuration
LOCK_FILE="/tmp/sotd_pipeline.lock"
DATA_DIR="${SOTD_DATA_DIR:-/data}"
LOG_DIR="${LOG_DIR:-/data/logs}"
PYTHON_CMD="python3"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_DIR/pipeline.log"
}

# Check for lock file
if [ -f "$LOCK_FILE" ]; then
    log "WARNING: Lock file exists at $LOCK_FILE. Previous pipeline run may still be in progress."
    log "Skipping this run to prevent overlap."
    exit 0
fi

# Create lock file
touch "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

log "Starting pipeline run..."

# Get current and previous month
CURRENT_MONTH=$(date +%Y-%m)
# Calculate previous month using Python (works on all platforms)
PREVIOUS_MONTH=$(python3 -c "from datetime import datetime, timedelta; d = datetime.now(); prev = d.replace(day=1) - timedelta(days=1); print(prev.strftime('%Y-%m'))")

log "Processing months: $CURRENT_MONTH and $PREVIOUS_MONTH"

# Function to run pipeline for a month
run_pipeline_for_month() {
    local month=$1
    log "Processing month: $month"
    
    # Change to app directory
    cd /app
    
    # Run all phases with --force to ensure fresh processing
    log "Running fetch phase for $month..."
    if ! $PYTHON_CMD /app/run.py fetch --month "$month" --force >> "$LOG_DIR/pipeline.log" 2>&1; then
        log "ERROR: Fetch phase failed for $month"
        return 1
    fi
    
    log "Running extract phase for $month..."
    if ! $PYTHON_CMD /app/run.py extract --month "$month" --force >> "$LOG_DIR/pipeline.log" 2>&1; then
        log "ERROR: Extract phase failed for $month"
        return 1
    fi
    
    log "Running match phase for $month..."
    if ! $PYTHON_CMD /app/run.py match --month "$month" --force >> "$LOG_DIR/pipeline.log" 2>&1; then
        log "ERROR: Match phase failed for $month"
        return 1
    fi
    
    log "Running enrich phase for $month..."
    if ! $PYTHON_CMD /app/run.py enrich --month "$month" --force >> "$LOG_DIR/pipeline.log" 2>&1; then
        log "ERROR: Enrich phase failed for $month"
        return 1
    fi
    
    log "Running aggregate phase for $month..."
    if ! $PYTHON_CMD /app/run.py aggregate --month "$month" --force >> "$LOG_DIR/pipeline.log" 2>&1; then
        log "ERROR: Aggregate phase failed for $month"
        return 1
    fi
    
    log "Running report phase for $month..."
    if ! $PYTHON_CMD /app/run.py report --month "$month" --force >> "$LOG_DIR/pipeline.log" 2>&1; then
        log "ERROR: Report phase failed for $month"
        return 1
    fi
    
    log "Completed all phases for $month"
    return 0
}

# Process both months
ERRORS=0

if ! run_pipeline_for_month "$CURRENT_MONTH"; then
    ERRORS=$((ERRORS + 1))
fi

if ! run_pipeline_for_month "$PREVIOUS_MONTH"; then
    ERRORS=$((ERRORS + 1))
fi

# Generate search index after aggregate phase completes
log "Generating search index..."
if ! $PYTHON_CMD /app/scripts/generate_search_index.py --data-dir "$DATA_DIR" --output "$DATA_DIR/search_index.json" >> "$LOG_DIR/pipeline.log" 2>&1; then
    log "WARNING: Search index generation failed (non-fatal)"
    # Don't fail the pipeline if search index generation fails
fi

# Summary
if [ $ERRORS -eq 0 ]; then
    log "Pipeline run completed successfully"
else
    log "Pipeline run completed with $ERRORS error(s)"
fi

# Remove lock file
rm -f "$LOCK_FILE"

exit $ERRORS
