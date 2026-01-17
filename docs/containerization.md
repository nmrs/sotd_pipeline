# Containerization Guide for SOTD Pipeline WebUI

This guide covers deploying the SOTD Pipeline web application on Synology Container Manager.

## Overview

The application consists of two containers:
- **Frontend**: React application served via nginx (port 8080)
- **Backend**: FastAPI application (port 8000, internal only)

The data directory is mounted from a Synology shared folder, allowing the pipeline to update catalogs independently.

## Prerequisites

- Synology NAS with Container Manager installed
- Docker Compose support enabled
- Shared folder created for data directory (e.g., `sotd_data`)
- Network access to Synology NAS

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

Or use Synology Drive to sync the directory (recommended for ongoing sync).

### 3. Update docker-compose.yml

Edit `docker-compose.yml` and update the volume mount path if your shared folder path differs:

```yaml
volumes:
  - type: bind
    source: /volume1/sotd_data  # Update this if your path differs
    target: /data
```

### 4. Deploy Containers

#### Option A: Using Synology Container Manager GUI

1. Open **Container Manager**
2. Click **Project** → **Create**
3. Name: `sotd-pipeline`
4. Path: Select the directory containing `docker-compose.yml`
5. Click **Next** → **Create**
6. The containers will build and start automatically

#### Option B: Using SSH/Command Line

```bash
# SSH into Synology
ssh user@synology

# Navigate to project directory
cd /path/to/sotd_pipeline

# Build and start containers
docker-compose up -d --build
```

### 5. Configure Reverse Proxy (Optional)

To expose the application via a domain name:

1. Open **Control Panel** → **Login Portal** → **Advanced** → **Reverse Proxy**
2. Click **Create**
3. Configure:
   - **Source**: 
     - Protocol: HTTPS
     - Hostname: `sotd.yourdomain.com`
     - Port: 443
   - **Destination**:
     - Protocol: HTTP
     - Hostname: `localhost`
     - Port: `8080`
4. Enable **HSTS** and **HTTP/2** if desired
5. Assign SSL certificate (Control Panel → Security → Certificates)

### 6. Verify Deployment

1. Check container status:
   ```bash
   docker-compose ps
   ```

2. Check logs:
   ```bash
   docker-compose logs backend
   docker-compose logs frontend
   ```

3. Test health endpoints:
   - Frontend: `http://synology-ip:8080/health`
   - Backend: `http://synology-ip:8000/api/health`

4. Access application:
   - Direct: `http://synology-ip:8080`
   - Via reverse proxy: `https://sotd.yourdomain.com`

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
├── matched/
│   ├── 2025-01.json
│   └── ...
├── extract/
├── enrich/
├── overrides/
│   ├── non_matches_brands.yaml
│   └── ...
└── ...
```

## Environment Variables

### Backend Container

- `SOTD_DATA_DIR`: Path to data directory (default: `/data`)
- `ENVIRONMENT`: Environment mode (default: `production`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

### Frontend Container

- `VITE_API_URL`: Backend API URL (set at build time, default: `http://backend:8000`)

## Data Synchronization

### Using Synology Drive (Recommended)

1. Install **Synology Drive Server** on NAS (Package Center)
2. Install **Synology Drive Client** on your laptop
3. Create sync task:
   - Local folder: `/path/to/sotd_pipeline/data/`
   - Remote folder: `/volume1/sotd_data/`
4. Changes sync automatically when connected to network

**Benefits:**
- Automatic bidirectional sync
- Works with iCloud backup (local files → iCloud → Synology)
- Version history and file recovery
- Conflict resolution

### Using rsync (Manual)

```bash
# Sync from laptop to Synology
rsync -avz --delete /path/to/sotd_pipeline/data/ user@synology:/volume1/sotd_data/
```

### Using Network Mount

Mount the Synology shared folder on your laptop:

```bash
# macOS
mount_smbfs //user@synology/sotd_data /mnt/sotd_data

# Linux
mount -t cifs //synology/sotd_data /mnt/sotd_data -o username=user
```

## Pipeline Integration

The pipeline runs separately (not containerized) and updates the shared folder:

1. **Local pipeline**: Updates local `data/` directory
2. **Synology Drive**: Syncs changes to Synology shared folder
3. **Container**: Reads updated files automatically (no restart needed)

## Troubleshooting

### Containers won't start

1. Check logs: `docker-compose logs`
2. Verify shared folder path exists and has correct permissions
3. Check port conflicts (8080, 8000)
4. Verify Docker has access to shared folder

### Backend can't read data files

1. Verify `SOTD_DATA_DIR` environment variable is set correctly
2. Check file permissions on shared folder
3. Verify volume mount is working: `docker-compose exec backend ls -la /data`

### Frontend can't connect to backend

1. Verify both containers are on the same network (`sotd-network`)
2. Check backend is running: `docker-compose ps backend`
3. Verify backend health endpoint: `curl http://localhost:8000/api/health`

### Data not syncing

1. Check Synology Drive sync status
2. Verify network connectivity
3. Check shared folder permissions
4. Review Synology Drive logs

## Maintenance

### Updating Containers

```bash
# Rebuild and restart
docker-compose up -d --build

# Or restart specific service
docker-compose restart backend
docker-compose restart frontend
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stopping Containers

```bash
docker-compose down
```

### Backup Data Directory

The shared folder can be backed up using Synology's backup tools:
- **Hyper Backup**: For local/cloud backups
- **Snapshot Replication**: For point-in-time recovery

## Security Considerations

1. **Read-write data mount**: Backend container mounts data as read-write (webui writes to catalogs, correct_matches, overrides, etc.)
2. **Non-root users**: Both containers run as non-root users
3. **Network isolation**: Backend not exposed to host, only to frontend
4. **Environment variables**: Sensitive config via env vars, not hardcoded
5. **Health checks**: Monitor container health
6. **Shared folder access**: Ensure proper permissions on Synology shared folder for both container and pipeline access

## Port Configuration

- **Frontend**: Exposed on port 8080 (reverse proxy routes to this)
- **Backend**: Internal only (port 8000, frontend proxies API requests)

## Notes

- **Reverse Proxy**: Synology has built-in reverse proxy (Control Panel → Login Portal → Reverse Proxy). Configure separately to route external traffic (e.g., `https://sotd.yourdomain.com`) to container port 8080
- **Pipeline**: Runs separately (on laptop or other host), not containerized. Updates shared folder via network mount or file sync
- **Data Updates**: 
  - Pipeline updates shared folder, web app reads changes automatically (no restart needed for catalog changes)
  - WebUI writes to shared folder (correct_matches, brush_splits, non_matches, etc.)
  - Both can access shared folder simultaneously
- **Shared Folder**: Use Synology shared folder (e.g., `/volume1/sotd_data`) so it can be accessed from:
  - Container (mounted volume)
  - Pipeline (network mount/SMB/NFS)
  - Laptop (SMB/NFS share or Synology Drive)
