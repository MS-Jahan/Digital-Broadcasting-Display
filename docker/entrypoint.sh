#!/bin/bash
# Digital Broadcasting Display - Docker Entrypoint Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

# Print startup banner
echo "
╔══════════════════════════════════════════════════════════════╗
║                 Digital Broadcasting Display                 ║
║              Flask-based Digital Signage System              ║
║                     Starting Container...                    ║
╚══════════════════════════════════════════════════════════════╝
"

# Environment variables with defaults
export FLASK_ENV=${FLASK_ENV:-production}
export SECRET_KEY=${SECRET_KEY:-secret!}
export ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
export ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin}
export DATABASE_PATH=${DATABASE_PATH:-/app/data/database.sqlite}
export UPLOAD_FOLDER=${UPLOAD_FOLDER:-videos}
export PORT=${PORT:-8082}

# Check if running as root (should not in production)
if [ "$(id -u)" = "0" ]; then
    warn "Running as root user. This is not recommended for production."
fi

# Create necessary directories
log "Creating necessary directories..."
mkdir -p /app/data /app/logs

# Set up database path
DB_DIR=$(dirname "$DATABASE_PATH")
if [ ! -d "$DB_DIR" ]; then
    log "Creating database directory: $DB_DIR"
    mkdir -p "$DB_DIR"
fi

# Initialize database if it doesn't exist
if [ ! -f "$DATABASE_PATH" ]; then
    log "Database not found. It will be created on first run."
else
    log "Using existing database at: $DATABASE_PATH"
fi

# Backup existing database if it exists
if [ -f "$DATABASE_PATH" ] && [ "${BACKUP_ON_START:-true}" = "true" ]; then
    BACKUP_FILE="${DATABASE_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
    log "Creating backup: $BACKUP_FILE"
    cp "$DATABASE_PATH" "$BACKUP_FILE"
fi

# Set up logging
LOG_FILE="/app/logs/app.log"
log "Setting up logging to: $LOG_FILE"

# Update main.py to use environment variables for database path
if [ -n "$DATABASE_PATH" ] && [ "$DATABASE_PATH" != "/app/database.sqlite" ]; then
    log "Configuring custom database path: $DATABASE_PATH"
    # This will be handled by the application code
fi

# Health check function
health_check() {
    log "Performing health check..."
    if curl -f http://localhost:${PORT}/login >/dev/null 2>&1; then
        success "Health check passed"
        return 0
    else
        error "Health check failed"
        return 1
    fi
}

# Signal handlers
shutdown_handler() {
    log "Received shutdown signal. Gracefully shutting down..."
    if [ -n "$APP_PID" ]; then
        kill -TERM "$APP_PID" 2>/dev/null || true
        wait "$APP_PID"
    fi
    log "Application shutdown complete"
    exit 0
}

# Set up signal handlers
trap shutdown_handler SIGTERM SIGINT

# Pre-flight checks
log "Running pre-flight checks..."

# Check Python version
PYTHON_VERSION=$(python --version 2>&1)
log "Python version: $PYTHON_VERSION"

# Check required directories
for dir in videos uploads static/logos static/token_backgrounds; do
    if [ ! -d "/app/$dir" ]; then
        log "Creating directory: /app/$dir"
        mkdir -p "/app/$dir"
    fi
done

# Validate environment
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "secret!" ]; then
    warn "Using default SECRET_KEY. Please set a secure SECRET_KEY for production."
fi

if [ "$ADMIN_USERNAME" = "admin" ] && [ "$ADMIN_PASSWORD" = "admin" ]; then
    warn "Using default admin credentials. Please change them for production."
fi

# Print configuration
log "Application Configuration:"
log "  - Flask Environment: $FLASK_ENV"
log "  - Port: $PORT"
log "  - Database Path: $DATABASE_PATH"
log "  - Upload Folder: $UPLOAD_FOLDER"
log "  - Admin Username: $ADMIN_USERNAME"

# If no arguments or if first argument starts with -, run the application
if [ $# -eq 0 ] || [ "${1#-}" != "$1" ]; then
    log "Starting Digital Broadcasting Display application..."
    
    # Start the application in background
    exec python main.py 2>&1 | tee -a "$LOG_FILE" &
    APP_PID=$!
    
    # Wait a moment for the application to start
    sleep 5
    
    # Perform initial health check
    if health_check; then
        success "Application started successfully (PID: $APP_PID)"
    else
        error "Application failed to start properly"
        exit 1
    fi
    
    # Keep the container running
    wait "$APP_PID"
else
    # Execute the given command
    log "Executing custom command: $*"
    exec "$@"
fi
