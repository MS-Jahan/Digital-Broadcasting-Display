#!/bin/sh
# Digital Broadcasting Display - Database Backup Script

set -e

# Configuration
DATA_DIR="/data"
BACKUP_DIR="/backups"
DATABASE_FILE="database.sqlite"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILE="database_backup_${TIMESTAMP}.sqlite"
LOG_FILE="/backups/backup.log"

# Default values
BACKUP_RETENTION=${BACKUP_RETENTION:-7}

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

log "Starting database backup process..."

# Check if database exists
if [ ! -f "$DATA_DIR/$DATABASE_FILE" ]; then
    log "WARNING: Database file not found at $DATA_DIR/$DATABASE_FILE"
    exit 0
fi

# Create backup
log "Creating backup: $BACKUP_FILE"
if cp "$DATA_DIR/$DATABASE_FILE" "$BACKUP_DIR/$BACKUP_FILE"; then
    log "Backup created successfully: $BACKUP_DIR/$BACKUP_FILE"
    
    # Compress backup to save space
    if gzip "$BACKUP_DIR/$BACKUP_FILE"; then
        BACKUP_FILE="${BACKUP_FILE}.gz"
        log "Backup compressed: $BACKUP_DIR/$BACKUP_FILE"
    fi
    
    # Get backup size
    BACKUP_SIZE=$(ls -lh "$BACKUP_DIR/$BACKUP_FILE" | awk '{print $5}')
    log "Backup size: $BACKUP_SIZE"
else
    log "ERROR: Failed to create backup"
    exit 1
fi

# Clean up old backups (keep only the most recent N backups)
log "Cleaning up old backups (retention: $BACKUP_RETENTION days)..."

# Remove backups older than retention period
find "$BACKUP_DIR" -name "database_backup_*.sqlite.gz" -mtime +$BACKUP_RETENTION -type f -delete

# Count remaining backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "database_backup_*.sqlite.gz" -type f | wc -l)
log "Total backups after cleanup: $BACKUP_COUNT"

# Verify backup integrity
log "Verifying backup integrity..."
if gunzip -t "$BACKUP_DIR/$BACKUP_FILE" 2>/dev/null; then
    log "Backup integrity check passed"
else
    log "WARNING: Backup integrity check failed"
fi

log "Backup process completed successfully"

# Optional: Send notification (if configured)
if [ -n "$NOTIFICATION_WEBHOOK" ]; then
    PAYLOAD="{\"text\":\"Digital Broadcasting Display: Database backup completed successfully. Size: $BACKUP_SIZE\"}"
    curl -X POST -H 'Content-type: application/json' --data "$PAYLOAD" "$NOTIFICATION_WEBHOOK" || true
fi
