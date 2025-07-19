# WebUI Server Management

This directory contains scripts for managing the SOTD Pipeline WebUI servers.

## Quick Start

From the project root directory:

```bash
# Start both servers
./manage-webui.sh start

# Stop both servers  
./manage-webui.sh stop

# Check server status
./manage-webui.sh status

# Restart both servers
./manage-webui.sh restart
```

## Available Commands

### `start`
Starts both the frontend (Vite) and backend (FastAPI) servers:
- **Frontend**: React app on http://localhost:3000
- **Backend**: FastAPI API on http://localhost:8000

### `stop`
Stops both servers gracefully, with force kill if needed.

### `restart`
Stops both servers and then starts them again.

### `status`
Shows the current status of both servers and port availability.

### `logs [server]`
Shows real-time logs for the specified server:
```bash
./manage-webui.sh logs frontend  # Frontend server logs
./manage-webui.sh logs backend   # Backend server logs
```

### `clean`
Removes PID files and log files (useful if servers get stuck).

### `help`
Shows the help message with all available commands.

## Server Architecture

The WebUI consists of two servers:

1. **Frontend Server (Vite)**
   - **Port**: 3000
   - **Purpose**: Serves the React application
   - **Command**: `npm run dev`
   - **Features**: Hot reloading, development server

2. **Backend Server (FastAPI)**
   - **Port**: 8000
   - **Purpose**: Provides API endpoints
   - **Command**: `python main.py`
   - **Features**: Data analysis, file operations, catalog management

## File Structure

```
webui/
├── scripts/
│   ├── manage-servers.sh    # Main server management script
│   └── README.md           # This file
├── api/
│   └── main.py             # FastAPI backend server
├── package.json            # Frontend dependencies
└── vite.config.ts          # Vite configuration
```

## Troubleshooting

### Port Already in Use
If you get "port already in use" errors:
```bash
# Check what's using the port
lsof -i :3000  # Frontend port
lsof -i :8000  # Backend port

# Kill the process if needed
kill -9 <PID>
```

### Servers Won't Start
If servers fail to start:
```bash
# Clean up and try again
./manage-webui.sh clean
./manage-webui.sh start
```

### Servers Get Stuck
If servers become unresponsive:
```bash
# Force stop and restart
./manage-webui.sh stop
./manage-webui.sh clean
./manage-webui.sh start
```

## Development Workflow

1. **Start servers for development:**
   ```bash
   ./manage-webui.sh start
   ```

2. **Check status:**
   ```bash
   ./manage-webui.sh status
   ```

3. **View logs if needed:**
   ```bash
   ./manage-webui.sh logs frontend
   ./manage-webui.sh logs backend
   ```

4. **Stop servers when done:**
   ```bash
   ./manage-webui.sh stop
   ```

## Integration with Development

- **Frontend**: http://localhost:3000 - React app for data analysis
- **Backend**: http://localhost:8000 - API for pipeline data operations
- **API Documentation**: http://localhost:8000/docs - FastAPI auto-generated docs

The frontend makes API calls to the backend to analyze SOTD pipeline data, manage catalogs, and perform data operations. 