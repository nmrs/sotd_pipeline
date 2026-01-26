# Pipeline Container - Local Testing Guide

## Quick Start

### Prerequisites

**Reddit API Credentials Required**

The fetch phase requires Reddit API credentials. You have two options:

**Option A: Environment Variables (Recommended for containers)**

1. Copy the example environment file:
   ```bash
   cd docker/pipeline
   cp .env.example .env
   ```

2. Edit `.env` and add your Reddit API credentials from your `praw.ini` file:
   ```bash
   praw_client_id=your_client_id
   praw_client_secret=your_client_secret
   praw_user_agent=SOTD Pipeline
   ```
   
   **Important:** PRAW requires lowercase `praw_` prefix for environment variables. Use lowercase in your `.env` file.
   **Note:** OAuth script-type authentication only requires `client_id`, `client_secret`, and `user_agent`. Username and password are not needed.

3. Load environment variables:
   ```bash
   export $(cat .env | xargs)
   ```

**Option B: Mount praw.ini file**

Mount your `praw.ini` file as a volume (add to docker-compose.yml):
```yaml
volumes:
  - type: bind
    source: ../../praw.ini
    target: /app/praw.ini
```

### Option 1: Build and Run with Docker Compose (Recommended)

1. **Set up Reddit credentials** (see Prerequisites above)

2. **Build and start the container:**
   ```bash
   cd docker/pipeline
   docker-compose -f docker-compose.local.yml --env-file .env up --build
   ```

3. **Run in detached mode (background):**
   ```bash
   docker-compose -f docker-compose.local.yml up -d --build
   ```

4. **View logs:**
   ```bash
   docker-compose -f docker-compose.local.yml logs -f
   ```

5. **Stop the container:**
   ```bash
   docker-compose -f docker-compose.local.yml down
   ```

### Option 2: Build Docker Image Manually

1. **Build the image:**
   ```bash
   cd /path/to/sotd_pipeline
   docker build -f docker/pipeline/Dockerfile -t sotd-pipeline:latest .
   ```

2. **Run the container manually:**
   
   **Option A: Use --env-file (Recommended)**
   ```bash
   docker run -it --rm \
     --env-file .env \
     -v $(pwd)/data:/data \
     -e SOTD_DATA_DIR=/data \
     -e LOG_DIR=/data/logs \
     sotd-pipeline:latest
   ```
   
   **Option B: Export variables first**
   ```bash
   export $(cat .env | xargs)
   docker run -it --rm \
     -v $(pwd)/data:/data \
     -e CRON_SCHEDULE="*/5 * * * *" \
     -e SOTD_DATA_DIR=/data \
     -e LOG_DIR=/data/logs \
     -e praw_client_id="${praw_client_id}" \
     -e praw_client_secret="${praw_client_secret}" \
     -e praw_user_agent="${praw_user_agent:-SOTD Pipeline}" \
     sotd-pipeline:latest
   ```
   
   **Note:** When exporting from .env, use lowercase variable names since .env should use lowercase `praw_` prefix.

3. **Run pipeline script manually (for testing without cron):**
   
   **Option A: Use --env-file (Recommended)**
   ```bash
   docker run -it --rm \
     --env-file .env \
     --entrypoint /app/run-pipeline.sh \
     -v $(pwd)/data:/data \
     -e SOTD_DATA_DIR=/data \
     -e LOG_DIR=/data/logs \
     sotd-pipeline:latest
   ```
   
   **Option B: Export variables first**
   ```bash
   export $(cat .env | xargs)
   docker run -it --rm \
     --entrypoint /app/run-pipeline.sh \
     -v $(pwd)/data:/data \
     -e SOTD_DATA_DIR=/data \
     -e LOG_DIR=/data/logs \
     -e praw_client_id="${praw_client_id}" \
     -e praw_client_secret="${praw_client_secret}" \
     -e praw_user_agent="${praw_user_agent:-SOTD Pipeline}" \
     sotd-pipeline:latest
   ```
   
   **Note:** Use `--entrypoint` to override the default entrypoint and run the script directly without cron.
   **Note:** The `--env-file` flag automatically loads all variables from `.env` file, making it much simpler than exporting individual variables.
   **Note:** When exporting from .env, use lowercase variable names since .env should use lowercase `praw_` prefix.

## Testing the Container

### 1. Test Container Build

```bash
cd docker/pipeline
docker-compose -f docker-compose.local.yml build
```

This will:
- Build the Docker image with Python 3.11
- Install all dependencies from `requirements.txt`
- Copy pipeline code and scripts
- Set up cron

### 2. Test Entrypoint Script

```bash
# Start container and check cron is configured
docker-compose -f docker-compose.local.yml up

# In another terminal, check cron schedule
docker exec sotd-pipeline-local crontab -l
```

### 3. Test Pipeline Script Manually

```bash
# Run pipeline script directly (bypasses cron)
docker exec sotd-pipeline-local /app/run-pipeline.sh
```

### 4. Test Lock File Mechanism

```bash
# Create lock file manually
docker exec sotd-pipeline-local touch /tmp/sotd_pipeline.lock

# Try to run pipeline (should skip due to lock file)
docker exec sotd-pipeline-local /app/run-pipeline.sh

# Remove lock file
docker exec sotd-pipeline-local rm /tmp/sotd_pipeline.lock
```

### 5. Check Logs

```bash
# View pipeline logs
docker exec sotd-pipeline-local cat /data/logs/pipeline.log

# Or tail logs in real-time
docker exec sotd-pipeline-local tail -f /data/logs/pipeline.log
```

## Environment Variables for Testing

You can override environment variables for testing:

```bash
# Test with faster schedule (every 2 minutes)
CRON_SCHEDULE="*/2 * * * *" docker-compose -f docker-compose.local.yml up

# Test with custom data directory
SOTD_DATA_DIR=/custom/path docker-compose -f docker-compose.local.yml up
```

## Troubleshooting

### Container won't start

1. **Check build logs:**
   ```bash
   docker-compose -f docker-compose.local.yml build --no-cache
   ```

2. **Check if data directory exists:**
   ```bash
   ls -la ../../data
   ```

3. **Check container logs:**
   ```bash
   docker-compose -f docker-compose.local.yml logs
   ```

### Pipeline not running

1. **Check cron is running:**
   ```bash
   docker exec sotd-pipeline-local ps aux | grep cron
   ```

2. **Check cron schedule:**
   ```bash
   docker exec sotd-pipeline-local crontab -l
   ```

3. **Check for lock file:**
   ```bash
   docker exec sotd-pipeline-local ls -la /tmp/sotd_pipeline.lock
   ```

### Permission issues

If you see permission errors, you may need to adjust file permissions:

```bash
# Make sure data directory is readable/writable
chmod -R 755 ../../data
```

## Testing Without Cron

To test the pipeline script without waiting for cron:

**Option 1: Override entrypoint (Recommended)**
```bash
docker run -it --rm \
  --env-file .env \
  --entrypoint /app/run-pipeline.sh \
  -v $(pwd)/data:/data \
  -e SOTD_DATA_DIR=/data \
  -e LOG_DIR=/data/logs \
  sotd-pipeline:latest
```

**Note:** The `--env-file .env` flag loads all environment variables from the `.env` file, including Reddit API credentials.

**Option 2: Use bash and run script manually**
```bash
# Start container with bash instead of entrypoint
docker run -it --rm \
  --env-file .env \
  --entrypoint /bin/bash \
  -v $(pwd)/data:/data \
  -e SOTD_DATA_DIR=/data \
  -e LOG_DIR=/data/logs \
  sotd-pipeline:latest

# Inside container, run pipeline manually
/app/run-pipeline.sh
```

**Note:** The `--env-file .env` flag loads all environment variables from the `.env` file into the container.

## Next Steps

Once local testing is successful:

1. Update `docker-compose.yml` with your Synology NAS path
2. Deploy to Synology NAS
3. Run migration script to copy historical data
4. Monitor logs and verify pipeline execution
