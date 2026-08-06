#!/bin/bash
# ============================================================================
# CNAA Server Start Script
# One-command startup for Cloud Native Agent Architecture
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration defaults
HOST="${CNAA_HOST:-localhost}"
PORT="${CNAA_PORT:-8080}"
PID_FILE="${CNAA_PID_FILE:-./cnaa.pid}"
LOG_DIR="${CNAA_LOG_DIR:-./logs}"

# ============================================================================
# Utility Functions
# ============================================================================

log_info() {
    echo -e "${GREEN}ℹ️  ${NC}$1"
}

log_warn() {
    echo -e "${YELLOW}⚠️  ${NC}$1"
}

log_error() {
    echo -e "${RED}❌ ${NC}$1"
}

log_step() {
    echo -e "${BLUE}▶️   ${NC}$1"
}

# ============================================================================
# Environment Setup
# ============================================================================

setup_environment() {
    log_step "Setting up environment..."
    
    # Create logs directory if not exists
    mkdir -p "$LOG_DIR"
    
    # Check Python version
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$MAJOR_VERSION" -lt 3 ] || ([ "$MAJOR_VERSION" -eq 3 ] && [ "$MINOR_VERSION" -lt 11 ]); then
        log_error "Python 3.11+ required, found: $PYTHON_VERSION"
        exit 1
    fi
    
    log_info "Python version: $PYTHON_VERSION ✓"
    
    # Auto-load .env file if exists
    if [ -f ".env" ]; then
        log_info "Loading configuration from .env"
        export $(grep -v '^#' .env | xargs)
        
        # Override defaults with .env values
        HOST="${CNAA_HOST:-$HOST}"
        PORT="${CNAA_PORT:-$PORT}"
    else
        log_warn ".env not found, using defaults (host=$HOST, port=$PORT)"
    fi
    
    # Install dependencies if needed
    if ! python3 -c "import cnaa" 2>/dev/null; then
        log_info "Installing CNAA package..."
        pip install -e . > /dev/null 2>&1
    fi
    
    log_info "Environment setup complete ✓"
}

# ============================================================================
# Startup Logic
# ============================================================================

start_server() {
    log_step "Starting CNAA Cloud Server..."
    
    # Check if already running
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            log_error "Server already running (PID: $OLD_PID)"
            log_info "Use './stop.sh' to stop first, or './status.sh' to check"
            exit 1
        else
            log_warn "Stale PID file found, removing..."
            rm "$PID_FILE"
        fi
    fi
    
    # Start server in background
    nohup python3 server.py \
        --host "$HOST" \
        --port "$PORT" \
        >> "$LOG_DIR/cnaa.log" 2>&1 &
    
    SERVER_PID=$!
    echo $SERVER_PID > "$PID_FILE"
    
    # Wait for server to be ready
    log_info "Waiting for server to initialize..."
    MAX_RETRIES=30
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
            break
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        sleep 0.5
    done
    
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        log_error "Server failed to start within timeout"
        cat "$LOG_DIR/cnaa.log"
        rm "$PID_FILE"
        exit 1
    fi
    
    log_info "✅ Server started successfully!"
    log_info ""
    log_info "📊 Service Information:"
    log_info "   Host:     http://$HOST:$PORT"
    log_info "   Health:   http://$HOST:$PORT/health"
    log_info "   Schemas:  http://$HOST:$PORT/schemas"
    log_info "   MCP API:  POST http://$HOST:$PORT/mcp"
    log_info ""
    log_info "📁 Log File: $LOG_DIR/cnaa.log"
    log_info "🔧 Process ID: $SERVER_PID"
    log_info ""
    log_info "💡 Tip: Use './status.sh' to check status, './stop.sh' to stop"
    log_info ""
}

# ============================================================================
# Status Display
# ============================================================================

show_status() {
    if [ ! -f "$PID_FILE" ]; then
        log_error "No PID file found - server not running?"
        exit 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ! kill -0 "$PID" 2>/dev/null; then
        log_error "Server is not running (stale PID file)"
        rm "$PID_FILE"
        exit 1
    fi
    
    log_info "CNAA Server Status:"
    log_info "   PID:         $PID"
    log_info "   Host:        $HOST:$PORT"
    log_info "   Status:      Running ✓"
    log_info "   Process:     Running"
    
    # Try to get health status
    if HEALTH=$(curl -s http://localhost:$PORT/health 2>/dev/null); then
        log_info "   Health:      Healthy"
        log_info "   Response:    $HEALTH"
    else
        log_warn "Health check failed"
    fi
    
    # Show recent logs
    echo ""
    log_info "Recent Logs (last 10 lines):"
    tail -n 10 "$LOG_DIR/cnaa.log" 2>/dev/null || log_warn "No log file available"
    echo ""
}

# ============================================================================
# Stop Logic
# ============================================================================

stop_server() {
    if [ ! -f "$PID_FILE" ]; then
        log_error "No PID file found - server not running?"
        exit 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ! kill -0 "$PID" 2>/dev/null; then
        log_error "Server is not running (stale PID file)"
        rm "$PID_FILE"
        exit 1
    fi
    
    log_step "Stopping server (PID: $PID)..."
    
    # Graceful shutdown
    kill "$PID"
    
    # Wait for process to terminate
    for i in {1..30}; do
        if ! kill -0 "$PID" 2>/dev/null; then
            log_info "✅ Server stopped gracefully"
            rm "$PID_FILE"
            exit 0
        fi
        sleep 0.5
    done
    
    # Force kill if not responsive
    log_warn "Graceful shutdown timed out, forcing termination..."
    kill -9 "$PID" 2>/dev/null
    rm "$PID_FILE"
    log_info "✅ Server forcefully stopped"
}

# ============================================================================
# Usage Help
# ============================================================================

show_help() {
    echo "CNAA Server Management Script"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  start     Start the server (default)"
    echo "  stop      Stop the server"
    echo "  restart   Restart the server"
    echo "  status    Show server status"
    echo "  logs      View last 50 lines of logs"
    echo "  help      Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  CNAA_HOST       Server host (default: localhost)"
    echo "  CNAA_PORT       Server port (default: 8080)"
    echo "  CNAA_PID_FILE   PID file path (default: ./cnaa.pid)"
    echo "  CNAA_LOG_DIR    Log directory (default: ./logs)"
    echo ""
    echo "Examples:"
    echo "  $0 start                # Start server"
    echo "  CNAA_PORT=9090 $0 start # Start on custom port"
    echo "  $0 stop                 # Stop server"
    echo "  $0 status               # Check status"
    echo ""
}

show_logs() {
    if [ ! -f "$LOG_DIR/cnaa.log" ]; then
        log_error "No log file found at $LOG_DIR/cnaa.log"
        exit 1
    fi
    
    log_info "Last 50 lines of logs:"
    echo "---"
    tail -n 50 "$LOG_DIR/cnaa.log"
    echo "---"
}

# ============================================================================
# Main Entry Point
# ============================================================================

main() {
    local command="${1:-start}"
    
    case "$command" in
        start)
            setup_environment
            start_server
            ;;
        stop)
            stop_server
            ;;
        restart)
            if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
                stop_server
            fi
            sleep 1
            setup_environment
            start_server
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
