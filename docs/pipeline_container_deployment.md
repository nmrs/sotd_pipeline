# Pipeline Container Deployment Guide

This guide covers deploying the SOTD Pipeline container on Synology NAS for automated hourly execution.

## Overview

The pipeline container runs all pipeline phases (fetch → extract → match → enrich → aggregate → report) on a schedule via cron, generating data files and a search index for the public web application.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Synology NAS                          │
│                                                          │
│  ┌──────────────────┐                                   │
│  │  Pipeline        │                                   │
│  │  Container       │                                   │
│  │                  │                                   │
│  │  - Cron (hourly) │                                   │
│  │  - run.py        │                                   │
│  │  - All phases    │                                   │
│  │  - Search index  │                                   │
│  └────────┬─────────┘                                   │
│           │                                              │
│           └──────────┬───────────────────────────────────┘
│                      │                                   │
│              ┌───────▼────────┐                        │
│              │  Data Volume   │                        │
│              │  /data         │                        │
│              │  - JSON files  │                        │
│              │  - YAML catalogs│                        │
│              │  - search_index.json│                    │
│              └─────────────────┘                        │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

- Synology NAS with Container Manager installed
- Docker Compose support enabled
- Shared folder created for data directory (e.g., `sotd_data`)
- Network access to Synology NAS
- SSH access to Synology NAS (for command-line deployment)

## Setup Instructions

### 1. Create Shared Folder

1. Open **Control Panel** → **Shared Folder**
2. Click **Create** → **Shared Folder**
3. Name: `sotd_data`
4. Set appropriate permissions (read/write for container user)
5. Note the path (typically `/volume1/sotd_data`)

### 2. Prepare Data Directory

Copy your existing `data/` directory contents to the shared folder:

```bash
# From your local machine
rsync -avz /path/to/sotd_pipeline/data/ user@synology:/volume1/sotd_data/
```

Or use the migration script:

```bash
./scripts/migrate-data-to-nas.sh synology.local /volume1/sotd_data ./data
```

### 3. Update docker-compose.yml

Edit `docker/pipeline/docker-compose.yml` and update the volume mount path:

```yaml
volumes:
  - type: bind
    source: /volume1/sotd_data  # Update this to your Synology shared folder path
    target: /data
```

### 4. Configure Environment Variables

The container supports the following environment variables:

- `CRON_SCHEDULE`: Cron schedule for pipeline execution (default: `0 * * * *` - hourly)
- `SOTD_DATA_DIR`: Data directory path (default: `/data`)
- `LOG_DIR`: Log directory path (default: `/data/logs`)

**Cron Schedule Examples:**

- `0 * * * *` - Every hour at minute 0 (default)
- `0 */2 * * *` - Every 2 hours
- `0 0 * * *` - Daily at midnight
- `0 0 * * 0` - Weekly on Sunday at midnight
- `*/30 * * * *` - Every 30 minutes

### 5. Deploy Container

#### Option A: Using Synology Container Manager GUI

1. Open **Container Manager**
2. Click **Project** → **Create**
3. Name: `sotd-pipeline`
4. Path: Select the directory containing `docker/pipeline/docker-compose.yml`
5. Click **Next** → **Create**
6. The container will build and start automatically

#### Option B: Using SSH/Command Line

```bash
# SSH into Synology
ssh user@synology

# Navigate to project directory
cd /path/to/sotd_pipeline/docker/pipeline

# Build and start container
docker-compose up -d --build
```

### 6. Verify Deployment

1. Check container status:
   ```bash
   docker-compose ps
   ```

2. Check logs:
   ```bash
   docker-compose logs -f pipeline
   ```

3. Check pipeline execution:
   ```bash
   # View pipeline log file
   tail -f /volume1/sotd_data/logs/pipeline.log
   ```

4. Verify data files are being created:
   ```bash
   ls -la /volume1/sotd_data/aggregated/
   ls -la /volume1/sotd_data/search_index.json
   ```

## Data Directory Structure

The mounted data directory should contain:

```
/data/
├── brushes.yaml
├── razors.yaml
├── blades.yaml
├── soaps.yaml
├── handles.yaml
├── knots.yaml
├── correct_matches/
│   ├── brush.yaml
│   ├── razor.yaml
│   └── ...
├── extract/
│   ├── 2025-01.json
│   └── ...
├── matched/
│   ├── 2025-01.json
│   └── ...
├── enriched/
│   ├── 2025-01.json
│   └── ...
├── aggregated/
│   ├── 2025-01.json
│   ├── annual/
│   │   └── 2025.json
│   └── ...
├── search_index.json
└── logs/
    └── pipeline.log
```

## Pipeline Execution

The pipeline container runs automatically on the configured cron schedule. Each run:

1. Processes current month and previous month (to catch any delays)
2. Runs all phases: fetch → extract → match → enrich → aggregate → report
3. Generates search index after aggregate phase completes
4. Logs all operations to `/data/logs/pipeline.log`

### Lock File Protection

The pipeline uses a lock file (`/tmp/sotd_pipeline.lock`) to prevent overlapping runs. If a previous run is still in progress, the new run will skip execution.

### Error Handling

- Phase failures are logged but don't stop the pipeline
- Search index generation failures are logged but don't fail the pipeline
- Next cron run will retry failed operations
- All errors are logged to `/data/logs/pipeline.log`

## YAML Catalog Synchronization

When catalog files are updated on your laptop, sync them to the NAS:

```bash
./scripts/sync-yamls-to-nas.sh synology.local /volume1/sotd_data ./data
```

This syncs:
- Catalog files: `brushes.yaml`, `razors.yaml`, `blades.yaml`, `soaps.yaml`, `handles.yaml`, `knots.yaml`
- `correct_matches/` directory

## Troubleshooting

### Container won't start

1. Check logs: `docker-compose logs pipeline`
2. Verify shared folder path exists and has correct permissions
3. Check Docker has access to shared folder
4. Verify `docker-compose.yml` volume mount path is correct

### Pipeline not running

1. Check cron is running: `docker-compose exec pipeline ps aux | grep cron`
2. Check cron schedule: `docker-compose exec pipeline crontab -l`
3. Check pipeline log: `tail -f /volume1/sotd_data/logs/pipeline.log`
4. Verify lock file isn't stuck: `docker-compose exec pipeline ls -la /tmp/sotd_pipeline.lock`

### Pipeline failing

1. Check pipeline log: `tail -f /volume1/sotd_data/logs/pipeline.log`
2. Check for specific phase errors in log
3. Verify data directory permissions
4. Check Reddit API access (for fetch phase)
5. Verify YAML catalog files are present and valid

### Search index not generated

1. Check if aggregate phase completed successfully
2. Check pipeline log for search index generation errors
3. Verify `scripts/generate_search_index.py` is present in container
4. Check data directory permissions

### Lock file stuck

If a lock file is stuck (previous run crashed):

```bash
docker-compose exec pipeline rm /tmp/sotd_pipeline.lock
```

## Maintenance

### Updating Container

```bash
# Rebuild and restart
cd docker/pipeline
docker-compose up -d --build

# Or restart specific service
docker-compose restart pipeline
```

### Viewing Logs

```bash
# All logs
docker-compose logs -f pipeline

# Pipeline execution log
tail -f /volume1/sotd_data/logs/pipeline.log
```

### Stopping Container

```bash
docker-compose down
```

### Changing Cron Schedule

1. Edit `docker-compose.yml` and update `CRON_SCHEDULE` environment variable
2. Restart container: `docker-compose restart pipeline`
3. Verify new schedule: `docker-compose exec pipeline crontab -l`

### Manual Pipeline Execution

To run the pipeline manually (for testing):

```bash
docker-compose exec pipeline /app/run-pipeline.sh
```

## Performance Considerations

1. **Lock File**: Prevents resource contention from overlapping runs
2. **Error Recovery**: Next cron run handles failures automatically
3. **Search Index**: Lightweight file (<1MB expected) for fast autocomplete queries
4. **Log Rotation**: Consider setting up log rotation for `/data/logs/pipeline.log`

## Security Considerations

1. **File Permissions**: Ensure proper read/write permissions for data volume
2. **Error Messages**: Don't expose sensitive paths in error logs
3. **Lock File**: Secure location (`/tmp/`) with proper permissions
4. **Network Access**: Container needs network access for Reddit API (fetch phase)

## Integration with WebUI

The pipeline container writes data to the same shared folder that the WebUI container reads from:

1. **Pipeline Container**: Writes processed data to `/volume1/sotd_data/`
2. **WebUI Container**: Reads data from `/volume1/sotd_data/`
3. **Search Index**: Generated by pipeline, consumed by WebUI for autocomplete
4. **Catalog Updates**: Synced from laptop to NAS, available to both containers

## Backup Strategy

The shared folder can be backed up using Synology's backup tools:

- **Hyper Backup**: For local/cloud backups
- **Snapshot Replication**: For point-in-time recovery
- **rsync**: For manual backups to external storage

## Notes

- **Pipeline Independence**: Pipeline runs independently of WebUI container
- **Data Updates**: Pipeline updates shared folder, WebUI reads changes automatically
- **Catalog Sync**: Manual sync required when catalogs are updated on laptop
- **Cron Schedule**: Configurable via environment variable for flexibility
- **Lock File**: Prevents overlapping runs but can be manually removed if stuck
