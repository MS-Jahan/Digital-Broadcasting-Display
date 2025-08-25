#!/bin/bash
# Digital Broadcasting Display - Docker Management Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
ENV_FILE="${PROJECT_DIR}/.env"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

# Help function
show_help() {
    echo "Digital Broadcasting Display - Docker Management Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup           Set up the environment (copy .env.example to .env)"
    echo "  build           Build the Docker image"
    echo "  start           Start the application"
    echo "  stop            Stop the application"
    echo "  restart         Restart the application"
    echo "  logs            Show application logs"
    echo "  shell           Open a shell in the running container"
    echo "  backup          Create a manual database backup"
    echo "  restore         Restore database from backup"
    echo "  update          Pull latest images and restart"
    echo "  clean           Clean up unused Docker resources"
    echo "  status          Show container status"
    echo "  reset           Reset the entire environment (DESTRUCTIVE!)"
    echo ""
    echo "Options:"
    echo "  --env-file      Specify environment file (default: .env)"
    echo "  --compose-file  Specify compose file (default: docker-compose.yml)"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup                    # Set up environment"
    echo "  $0 start                    # Start application"
    echo "  $0 logs --follow            # Follow logs"
    echo "  $0 backup                   # Create backup"
    echo "  $0 --env-file .env.prod start    # Start with production config"
    echo ""
}

# Check if Docker is installed and running
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        error "Docker is not running. Please start Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Set up environment
setup_env() {
    log "Setting up environment..."
    
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "${PROJECT_DIR}/.env.example" ]; then
            cp "${PROJECT_DIR}/.env.example" "$ENV_FILE"
            success "Created $ENV_FILE from .env.example"
            warn "Please edit $ENV_FILE and configure your settings before starting the application."
        else
            error ".env.example file not found!"
            exit 1
        fi
    else
        warn "$ENV_FILE already exists. Skipping creation."
    fi
    
    # Generate secret key if using default
    if grep -q "your-super-secret-key-change-this-in-production" "$ENV_FILE"; then
        SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "$(date +%s)-$(whoami)-$(hostname)" | sha256sum | cut -d' ' -f1)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/your-super-secret-key-change-this-in-production/$SECRET_KEY/" "$ENV_FILE"
        else
            sed -i "s/your-super-secret-key-change-this-in-production/$SECRET_KEY/" "$ENV_FILE"
        fi
        success "Generated secure SECRET_KEY"
    fi
    
    # Set build info
    BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/BUILD_DATE=.*/BUILD_DATE=$BUILD_DATE/" "$ENV_FILE"
        sed -i '' "s/VCS_REF=.*/VCS_REF=$VCS_REF/" "$ENV_FILE"
    else
        sed -i "s/BUILD_DATE=.*/BUILD_DATE=$BUILD_DATE/" "$ENV_FILE"
        sed -i "s/VCS_REF=.*/VCS_REF=$VCS_REF/" "$ENV_FILE"
    fi
}

# Build Docker image
build_image() {
    log "Building Docker image..."
    cd "$PROJECT_DIR"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build
    else
        docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build
    fi
    
    success "Docker image built successfully"
}

# Start application
start_app() {
    log "Starting Digital Broadcasting Display..."
    cd "$PROJECT_DIR"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d
    else
        docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d
    fi
    
    success "Application started successfully"
    log "Access the application at: http://localhost:$(grep HOST_PORT $ENV_FILE | cut -d= -f2 | head -1 || echo 8082)"
}

# Stop application
stop_app() {
    log "Stopping Digital Broadcasting Display..."
    cd "$PROJECT_DIR"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" down
    else
        docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" down
    fi
    
    success "Application stopped successfully"
}

# Restart application
restart_app() {
    log "Restarting Digital Broadcasting Display..."
    stop_app
    start_app
}

# Show logs
show_logs() {
    cd "$PROJECT_DIR"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" logs "$@"
    else
        docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" logs "$@"
    fi
}

# Open shell in container
open_shell() {
    log "Opening shell in container..."
    
    CONTAINER_NAME="dbd-app"
    if docker ps --format "table {{.Names}}" | grep -q "$CONTAINER_NAME"; then
        docker exec -it "$CONTAINER_NAME" /bin/bash
    else
        error "Container $CONTAINER_NAME is not running"
        exit 1
    fi
}

# Create manual backup
create_backup() {
    log "Creating manual database backup..."
    
    CONTAINER_NAME="dbd-backup"
    if docker ps --format "table {{.Names}}" | grep -q "$CONTAINER_NAME"; then
        docker exec "$CONTAINER_NAME" /backup.sh
        success "Manual backup created"
    else
        error "Backup container $CONTAINER_NAME is not running"
        exit 1
    fi
}

# Show container status
show_status() {
    log "Container Status:"
    cd "$PROJECT_DIR"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps
    else
        docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps
    fi
    
    echo ""
    log "Volume Usage:"
    docker volume ls | grep dbd_ | while read line; do
        volume_name=$(echo $line | awk '{print $2}')
        size=$(docker system df -v | grep "$volume_name" | awk '{print $3}' || echo "Unknown")
        echo "  $volume_name: $size"
    done
}

# Clean up Docker resources
clean_docker() {
    log "Cleaning up Docker resources..."
    
    docker system prune -f
    docker volume prune -f
    
    success "Docker cleanup completed"
}

# Update application
update_app() {
    log "Updating application..."
    cd "$PROJECT_DIR"
    
    # Pull latest images
    if command -v docker-compose &> /dev/null; then
        docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" pull
    else
        docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" pull
    fi
    
    # Restart with new images
    restart_app
    
    success "Application updated successfully"
}

# Reset environment (DESTRUCTIVE!)
reset_env() {
    warn "This will DELETE ALL DATA including database, uploads, and volumes!"
    read -p "Are you sure? Type 'yes' to continue: " -r
    if [[ ! $REPLY =~ ^yes$ ]]; then
        log "Reset cancelled"
        exit 0
    fi
    
    log "Resetting environment..."
    cd "$PROJECT_DIR"
    
    # Stop and remove containers
    if command -v docker-compose &> /dev/null; then
        docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" down -v --remove-orphans
    else
        docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" down -v --remove-orphans
    fi
    
    # Remove volumes
    docker volume ls | grep dbd_ | awk '{print $2}' | xargs -r docker volume rm
    
    success "Environment reset completed"
}

# Main script logic
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --env-file)
                ENV_FILE="$2"
                shift 2
                ;;
            --compose-file)
                COMPOSE_FILE="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            setup)
                check_docker
                setup_env
                exit 0
                ;;
            build)
                check_docker
                build_image
                exit 0
                ;;
            start)
                check_docker
                start_app
                exit 0
                ;;
            stop)
                check_docker
                stop_app
                exit 0
                ;;
            restart)
                check_docker
                restart_app
                exit 0
                ;;
            logs)
                shift
                check_docker
                show_logs "$@"
                exit 0
                ;;
            shell)
                check_docker
                open_shell
                exit 0
                ;;
            backup)
                check_docker
                create_backup
                exit 0
                ;;
            status)
                check_docker
                show_status
                exit 0
                ;;
            clean)
                check_docker
                clean_docker
                exit 0
                ;;
            update)
                check_docker
                update_app
                exit 0
                ;;
            reset)
                check_docker
                reset_env
                exit 0
                ;;
            *)
                error "Unknown command: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # If no command provided, show help
    show_help
}

# Run main function
main "$@"
