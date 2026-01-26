#!/bin/bash
# Script to sync YAML catalog files and correct_matches from local machine to Synology NAS
#
# Usage:
#   ./scripts/sync-yamls-to-nas.sh [NAS_HOST] [NAS_PATH] [LOCAL_DATA_DIR]
#
# Example:
#   ./scripts/sync-yamls-to-nas.sh synology.local /volume1/sotd_data ./data

set -e

# Configuration
NAS_HOST="${1:-synology.local}"
NAS_PATH="${2:-/volume1/sotd_data}"
LOCAL_DATA_DIR="${3:-./data}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

# Check if rsync is available
if ! command -v rsync &> /dev/null; then
    error "rsync is not installed. Please install rsync first."
    exit 1
fi

# Check if local data directory exists
if [ ! -d "$LOCAL_DATA_DIR" ]; then
    error "Local data directory does not exist: $LOCAL_DATA_DIR"
    exit 1
fi

log "Starting YAML sync..."
log "Source: $LOCAL_DATA_DIR"
log "Destination: $NAS_HOST:$NAS_PATH"

# Catalog YAML files to sync
CATALOG_FILES=(
    "brushes.yaml"
    "razors.yaml"
    "blades.yaml"
    "soaps.yaml"
    "handles.yaml"
    "knots.yaml"
)

# Sync catalog files
log "Syncing catalog files..."
for file in "${CATALOG_FILES[@]}"; do
    local_path="$LOCAL_DATA_DIR/$file"
    if [ -f "$local_path" ]; then
        log "Syncing $file..."
        rsync -avz --progress "$local_path" "$NAS_HOST:$NAS_PATH/$file"
    else
        warn "File $file does not exist, skipping..."
    fi
done

# Sync correct_matches directory
log "Syncing correct_matches directory..."
if [ -d "$LOCAL_DATA_DIR/correct_matches" ]; then
    rsync -avz --progress "$LOCAL_DATA_DIR/correct_matches/" "$NAS_HOST:$NAS_PATH/correct_matches/"
else
    warn "Directory correct_matches does not exist, skipping..."
fi

log "YAML sync complete!"
