#!/bin/bash

# SOTD Pipeline WebUI Server Manager
# Manages both frontend (Vite) and backend (FastAPI) servers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_PORT=3000
BACKEND_PORT=8000
FRONTEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$FRONTEND_DIR/api"
PID_DIR="$FRONTEND_DIR/.pids"

# Create PID directory if it doesn't exist
mkdir -p "$PID_DIR"

# PID files
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
BACKEND_PID_FILE="$PID_DIR/backend.pid"

# Log files
FRONTEND_LOG_FILE="$PID_DIR/frontend.log"
BACKEND_LOG_FILE="$PID_DIR/backend.log"

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date '+%H:%M:%S')] $message${NC}"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    lsof -ti:$port >/dev/null 2>&1
}

# Function to check if a process is running
check_process() {
    local pid_file=$1
    local name=$2
    
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            # Process is dead, clean up PID file
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# Function to start frontend server
start_frontend() {
    if check_process "$FRONTEND_PID_FILE" "frontend"; then
        print_status $YELLOW "Frontend server is already running (PID: $(cat $FRONTEND_PID_FILE))"
        return 0
    fi
    
    if check_port $FRONTEND_PORT; then
        print_status $RED "Port $FRONTEND_PORT is already in use by another process"
        return 1
    fi
    
    print_status $BLUE "Starting frontend server (Vite) on port $FRONTEND_PORT..."
    
    cd "$FRONTEND_DIR"
    npm run dev > "$FRONTEND_LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$FRONTEND_PID_FILE"
    
    # Wait a moment for server to start
    sleep 2
    
    if check_process "$FRONTEND_PID_FILE" "frontend"; then
        print_status $GREEN "Frontend server started successfully (PID: $pid)"
        print_status $BLUE "Frontend URL: http://localhost:$FRONTEND_PORT"
        return 0
    else
        print_status $RED "Failed to start frontend server"
        return 1
    fi
}

# Function to start backend server
start_backend() {
    if check_process "$BACKEND_PID_FILE" "backend"; then
        print_status $YELLOW "Backend server is already running (PID: $(cat $BACKEND_PID_FILE))"
        return 0
    fi
    
    if check_port $BACKEND_PORT; then
        print_status $RED "Port $BACKEND_PORT is already in use by another process"
        return 1
    fi
    
    print_status $BLUE "Starting backend server (FastAPI) on port $BACKEND_PORT..."
    
    # Run from project root with proper PYTHONPATH
    cd "$FRONTEND_DIR/.."
    # Set test environment for CORS to allow all origins during testing
    ENVIRONMENT=test PYTHONPATH=. python -m uvicorn webui.api.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > "$BACKEND_LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$BACKEND_PID_FILE"
    
    # Wait a moment for server to start
    sleep 3
    
    if check_process "$BACKEND_PID_FILE" "backend"; then
        print_status $GREEN "Backend server started successfully (PID: $pid)"
        print_status $BLUE "Backend URL: http://localhost:$BACKEND_PORT"
        return 0
    else
        print_status $RED "Failed to start backend server"
        return 1
    fi
}

# Function to stop a server
stop_server() {
    local pid_file=$1
    local name=$2
    local port=$3
    
    if check_process "$pid_file" "$name"; then
        local pid=$(cat "$pid_file")
        print_status $BLUE "Stopping $name server (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        
        # Wait for process to stop
        local count=0
        while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
            sleep 0.5
            count=$((count + 1))
        done
        
        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            print_status $YELLOW "Force killing $name server..."
            kill -9 "$pid" 2>/dev/null || true
        fi
        
        rm -f "$pid_file"
        print_status $GREEN "$name server stopped"
    else
        print_status $YELLOW "$name server is not running"
    fi
}

# Function to check server status
check_status() {
    print_status $BLUE "=== WebUI Server Status ==="
    
    # Check frontend
    if check_process "$FRONTEND_PID_FILE" "frontend"; then
        local pid=$(cat "$FRONTEND_PID_FILE")
        print_status $GREEN "Frontend (Vite): RUNNING (PID: $pid, Port: $FRONTEND_PORT)"
    else
        print_status $RED "Frontend (Vite): STOPPED"
    fi
    
    # Check backend
    if check_process "$BACKEND_PID_FILE" "backend"; then
        local pid=$(cat "$BACKEND_PID_FILE")
        print_status $GREEN "Backend (FastAPI): RUNNING (PID: $pid, Port: $BACKEND_PORT)"
    else
        print_status $RED "Backend (FastAPI): STOPPED"
    fi
    
    # Check ports
    if check_port $FRONTEND_PORT; then
        print_status $GREEN "Port $FRONTEND_PORT: IN USE"
    else
        print_status $RED "Port $FRONTEND_PORT: AVAILABLE"
    fi
    
    if check_port $BACKEND_PORT; then
        print_status $GREEN "Port $BACKEND_PORT: IN USE"
    else
        print_status $RED "Port $BACKEND_PORT: AVAILABLE"
    fi
}

# Function to show logs
show_logs() {
    local server=$1
    
    case $server in
        frontend)
            if [[ -f "$FRONTEND_LOG_FILE" ]]; then
                print_status $BLUE "=== Frontend Server Logs ==="
                tail -f "$FRONTEND_LOG_FILE"
            else
                print_status $RED "No frontend log file found"
            fi
            ;;
        backend)
            if [[ -f "$BACKEND_LOG_FILE" ]]; then
                print_status $BLUE "=== Backend Server Logs ==="
                tail -f "$BACKEND_LOG_FILE"
            else
                print_status $RED "No backend log file found"
            fi
            ;;
        *)
            print_status $RED "Usage: $0 logs [frontend|backend]"
            exit 1
            ;;
    esac
}

# Function to show help
show_help() {
    echo "SOTD Pipeline WebUI Server Manager"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start       Start both frontend and backend servers"
    echo "  stop        Stop both frontend and backend servers"
    echo "  restart     Restart both servers"
    echo "  status      Show status of both servers"
    echo "  logs [server] Show logs for specified server (frontend|backend)"
    echo "  clean       Clean up PID files and logs"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start          # Start both servers"
    echo "  $0 stop           # Stop both servers"
    echo "  $0 status         # Check server status"
    echo "  $0 logs frontend  # Show frontend logs"
    echo "  $0 logs backend   # Show backend logs"
    echo ""
    echo "Server URLs:"
    echo "  Frontend: http://localhost:$FRONTEND_PORT"
    echo "  Backend:  http://localhost:$BACKEND_PORT"
}

# Function to clean up
cleanup() {
    print_status $BLUE "Cleaning up PID files and logs..."
    rm -f "$FRONTEND_PID_FILE" "$BACKEND_PID_FILE"
    rm -f "$FRONTEND_LOG_FILE" "$BACKEND_LOG_FILE"
    print_status $GREEN "Cleanup complete"
}

# Main script logic
case "${1:-help}" in
    start)
        print_status $BLUE "Starting SOTD Pipeline WebUI servers..."
        start_frontend
        start_backend
        print_status $GREEN "All servers started!"
        print_status $BLUE "Frontend: http://localhost:$FRONTEND_PORT"
        print_status $BLUE "Backend:  http://localhost:$BACKEND_PORT"
        ;;
    stop)
        print_status $BLUE "Stopping SOTD Pipeline WebUI servers..."
        stop_server "$FRONTEND_PID_FILE" "frontend" $FRONTEND_PORT
        stop_server "$BACKEND_PID_FILE" "backend" $BACKEND_PORT
        print_status $GREEN "All servers stopped!"
        ;;
    restart)
        print_status $BLUE "Restarting SOTD Pipeline WebUI servers..."
        stop_server "$FRONTEND_PID_FILE" "frontend" $FRONTEND_PORT
        stop_server "$BACKEND_PID_FILE" "backend" $BACKEND_PORT
        sleep 2
        start_frontend
        start_backend
        print_status $GREEN "All servers restarted!"
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs "${2:-}"
        ;;
    clean)
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_status $RED "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac 