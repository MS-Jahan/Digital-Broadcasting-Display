# Docker Quick Reference Guide

## 🚀 Quick Start

```bash
# One-command setup
./scripts/docker-manage.sh setup && ./scripts/docker-manage.sh start

# Access application
http://localhost:8082
```

## 📋 Management Commands

| Command | Description |
|---------|-------------|
| `./scripts/docker-manage.sh setup` | Initialize environment (.env from template) |
| `./scripts/docker-manage.sh build` | Build Docker image |
| `./scripts/docker-manage.sh start` | Start all services |
| `./scripts/docker-manage.sh stop` | Stop all services |
| `./scripts/docker-manage.sh restart` | Restart all services |
| `./scripts/docker-manage.sh status` | Show container status |
| `./scripts/docker-manage.sh logs` | View logs |
| `./scripts/docker-manage.sh logs -f` | Follow logs in real-time |
| `./scripts/docker-manage.sh shell` | Open shell in app container |
| `./scripts/docker-manage.sh backup` | Create manual database backup |
| `./scripts/docker-manage.sh update` | Pull images and restart |
| `./scripts/docker-manage.sh clean` | Clean unused Docker resources |
| `./scripts/docker-manage.sh reset` | ⚠️ Delete everything and reset |

## 🔧 Advanced Docker Commands

### Direct Docker Compose
```bash
# Start with specific profile
docker-compose --profile production up -d

# View logs for specific service
docker-compose logs -f app

# Scale services (if supported)
docker-compose up -d --scale app=2

# Stop and remove volumes
docker-compose down -v
```

### Container Management
```bash
# Execute command in running container
docker exec -it dbd-app bash

# Copy files to/from container
docker cp ./local-file dbd-app:/app/data/
docker cp dbd-app:/app/logs/app.log ./local-logs/

# View container resource usage
docker stats dbd-app

# Inspect container configuration
docker inspect dbd-app
```

### Volume Management
```bash
# List application volumes
docker volume ls | grep dbd_

# Inspect volume contents
docker run --rm -v dbd_app_data:/data alpine ls -la /data

# Backup volume to archive
docker run --rm -v dbd_app_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/app_data_backup.tar.gz /data

# Restore volume from archive
docker run --rm -v dbd_app_data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/app_data_backup.tar.gz -C /
```

### Image Management
```bash
# Build with specific tag
docker build -t dbd:custom .

# View image layers
docker history digital-broadcasting-display:latest

# Remove unused images
docker image prune -f

# Export/Import images
docker save digital-broadcasting-display:latest | gzip > dbd-image.tar.gz
gunzip -c dbd-image.tar.gz | docker load
```

## 🌍 Environment Profiles

### Development
```bash
# Standard development
docker-compose up --build

# With file watching
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Production
```bash
# Basic production
docker-compose --profile production up -d

# Production with monitoring
docker-compose --profile production --profile monitoring up -d

# Production with auto-updates
docker-compose --profile production --profile auto-update up -d
```

### Testing
```bash
# Run tests in container
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 🔍 Debugging & Troubleshooting

### Container Debugging
```bash
# Check container health
docker inspect dbd-app | grep -A 5 "Health"

# View container processes
docker exec dbd-app ps aux

# Check network connectivity
docker exec dbd-app ping google.com
docker exec dbd-app curl -I localhost:8082

# View environment variables
docker exec dbd-app env | sort
```

### Log Analysis
```bash
# Follow logs with timestamps
docker-compose logs -f -t

# Filter logs by service
docker-compose logs app | grep ERROR

# Export logs to file
docker-compose logs > application.log 2>&1
```

### Performance Monitoring
```bash
# Resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Network inspection
docker network inspect dbd_network

# Volume usage
docker system df -v
```

## 📦 Data Management

### Backup Everything
```bash
#!/bin/bash
# Full backup script
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/$DATE"
mkdir -p "$BACKUP_DIR"

# Export volumes
for volume in $(docker volume ls | grep dbd_ | awk '{print $2}'); do
  echo "Backing up volume: $volume"
  docker run --rm -v $volume:/data -v $(pwd)/$BACKUP_DIR:/backup alpine \
    tar czf /backup/$volume.tar.gz /data
done

# Export database
docker exec dbd-backup /backup.sh

# Export configuration
cp .env docker-compose.yml "$BACKUP_DIR/"

echo "Backup completed in $BACKUP_DIR"
```

### Restore Everything
```bash
#!/bin/bash
# Full restore script
BACKUP_DIR="$1"

if [ -z "$BACKUP_DIR" ]; then
  echo "Usage: $0 <backup_directory>"
  exit 1
fi

# Stop services
docker-compose down -v

# Restore volumes
for archive in $BACKUP_DIR/*.tar.gz; do
  volume_name=$(basename $archive .tar.gz)
  echo "Restoring volume: $volume_name"
  docker volume create $volume_name
  docker run --rm -v $volume_name:/data -v $(pwd)/$BACKUP_DIR:/backup alpine \
    tar xzf /backup/$(basename $archive) -C /
done

# Restore configuration
cp "$BACKUP_DIR/.env" "$BACKUP_DIR/docker-compose.yml" ./

# Start services
docker-compose up -d

echo "Restore completed"
```

## 🛡️ Security Commands

### Security Scanning
```bash
# Scan image for vulnerabilities (requires docker-scan or similar)
docker scan digital-broadcasting-display:latest

# Check for security updates
docker-compose pull
docker-compose up -d
```

### Access Control
```bash
# View container user
docker exec dbd-app whoami
docker exec dbd-app id

# Check file permissions
docker exec dbd-app ls -la /app

# Verify non-root execution
docker exec dbd-app ps aux | grep -v root
```

## 🔄 Maintenance Tasks

### Daily
```bash
# Check container health
./scripts/docker-manage.sh status

# View recent logs for errors
docker-compose logs --tail=50 | grep -i error
```

### Weekly
```bash
# Clean up unused resources
./scripts/docker-manage.sh clean

# Update images
./scripts/docker-manage.sh update

# Verify backups
docker exec dbd-backup ls -la /backups/
```

### Monthly
```bash
# Full backup
# (Use backup script above)

# Review log file sizes
du -h /var/lib/docker/volumes/dbd_logs/_data/

# Check volume usage
docker system df -v
```

## ⚙️ Configuration Overrides

### Custom Environment
```bash
# Use custom .env file
./scripts/docker-manage.sh --env-file .env.production start

# Use custom compose file
./scripts/docker-manage.sh --compose-file docker-compose.prod.yml start
```

### Runtime Configuration
```bash
# Override port mapping
HOST_PORT=9090 docker-compose up -d

# Override database path
DATABASE_PATH=/custom/path/db.sqlite docker-compose up -d

# Enable debug mode
DEBUG=true FLASK_ENV=development docker-compose up -d
```

## 🆘 Emergency Procedures

### Service Recovery
```bash
# Force restart unhealthy containers
docker-compose restart app

# Recreate containers from fresh images
docker-compose up -d --force-recreate

# Reset to clean state (nuclear option)
./scripts/docker-manage.sh reset
```

### Data Recovery
```bash
# Recover from backup
./scripts/docker-manage.sh stop
# Restore volumes using backup script above
./scripts/docker-manage.sh start

# Emergency database export
docker exec dbd-app sqlite3 /app/data/database.sqlite .dump > emergency_backup.sql
```

---

## 📞 Support

For issues with Docker deployment:
1. Check container logs: `./scripts/docker-manage.sh logs`
2. Verify container health: `./scripts/docker-manage.sh status`
3. Review configuration: `cat .env`
4. Check resource usage: `docker stats`
5. Create issue with logs and configuration details
