#!/bin/bash
# Script to migrate processed data (fetch through aggregate phases) from local machine to Synology NAS
#
# Usage:
#   ./scripts/migrate-data-to-nas.sh [NAS_HOST] [NAS_PATH] [LOCAL_DATA_DIR]
#
# Example:
#   ./scripts/migrate-data-to-nas.sh synology.local /volume1/sotd_data ./data

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

log "Starting data migration..."
log "Source: $LOCAL_DATA_DIR"
log "Destination: $NAS_HOST:$NAS_PATH"

# Confirm before proceeding
read -p "This will copy fetch through aggregate data to $NAS_HOST:$NAS_PATH. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "Migration cancelled."
    exit 0
fi

# Directories to migrate (fetch through aggregate phases only)
PHASE_DIRS=(
    "threads"      # fetch phase output
    "extract"      # extract phase output
    "matched"      # match phase output
    "enriched"     # enrich phase output
    "aggregated"  # aggregate phase output
)

# Files to migrate
DATA_FILES=(
    "search_index.json"
)

# Migrate phase directories
log "Migrating phase directories..."
for dir in "${PHASE_DIRS[@]}"; do
    local_path="$LOCAL_DATA_DIR/$dir"
    if [ -d "$local_path" ]; then
        log "Migrating $dir..."
        rsync -avz --progress "$local_path/" "$NAS_HOST:$NAS_PATH/$dir/"
    else
        warn "Directory $dir does not exist, skipping..."
    fi
done

# Migrate data files
log "Migrating data files..."
for file in "${DATA_FILES[@]}"; do
    local_path="$LOCAL_DATA_DIR/$file"
    if [ -f "$local_path" ]; then
        log "Migrating $file..."
        rsync -avz --progress "$local_path" "$NAS_HOST:$NAS_PATH/$file"
    else
        warn "File $file does not exist, skipping..."
    fi
done

# Verify migration (optional checksums)
log "Migration complete!"
log "To verify, you can run:"
log "  rsync -avz --dry-run $LOCAL_DATA_DIR/ $NAS_HOST:$NAS_PATH/"
