#!/bin/bash
# Simple daily backup script for CNAA databases

set -e

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

echo "📦 Creating database backup..."

# Backup all SQLite databases
for db_file in *.db *.sqlite; do
    if [ -f "$db_file" ]; then
        cp "$db_file" "$BACKUP_DIR/"
        echo "  ✓ Backed up: $db_file"
    fi
done

# Compress older backups (keep last 7 days)
find "$BACKUP_DIR" -name "*.db.gz" -mtime +7 -delete 2>/dev/null || true

echo "✅ Backup created: $BACKUP_DIR/"
ls -lh "$BACKUP_DIR"/*.db* 2>/dev/null | tail -5
