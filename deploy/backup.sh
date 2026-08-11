#!/usr/bin/env sh
# Daily backup (section 14.3). Run from the project directory by cron:
#
#   15 3 * * * cd /srv/flowers && ./deploy/backup.sh >> /var/log/flowers-backup.log 2>&1
#
# A backup nobody restored is a rumour, so deploy/README.md carries the restore
# procedure and the date it was last carried out.

set -eu

BACKUP_DIR="${BACKUP_DIR:-/srv/backups}"
KEEP_DAYS="${KEEP_DAYS:-14}"
COMPOSE="docker compose -f compose.prod.yaml"
STAMP=$(date -u +%Y%m%d-%H%M%S)

# The owner hears about a failed backup the same way they hear about an
# enquiry: in Telegram. Silence is what makes a broken backup expensive.
notify_failure() {
    step="$1"
    [ -n "${TELEGRAM_BOT_TOKEN:-}" ] || return 0
    [ -n "${TELEGRAM_CHAT_ID:-}" ] || return 0
    curl -sS --max-time 10 \
        "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d "chat_id=${TELEGRAM_CHAT_ID}" \
        -d "text=Backup failed at step: ${step} ($(hostname))" >/dev/null || true
}

trap 'notify_failure "${STEP:-unknown}"' EXIT

# .env holds the credentials and the Telegram token; it is never in the repo.
if [ -f .env ]; then
    set -a
    . ./.env
    set +a
fi

mkdir -p "$BACKUP_DIR/db" "$BACKUP_DIR/media"

STEP="pg_dump"
echo "==> dumping the database"
$COMPOSE exec -T db pg_dump \
    --username "${POSTGRES_USER:-flowers}" \
    --dbname "${POSTGRES_DB:-flowers}" \
    --format custom \
    | gzip > "$BACKUP_DIR/db/flowers-$STAMP.dump.gz"

# A dump that gzip could not finish is worse than no dump: it looks like one.
gzip -t "$BACKUP_DIR/db/flowers-$STAMP.dump.gz"

STEP="media"
echo "==> syncing the media volumes"
for volume in media_public media_private; do
    docker run --rm \
        -v "flowers_${volume}:/data:ro" \
        -v "$BACKUP_DIR/media:/backup" \
        alpine:3 \
        tar czf "/backup/${volume}-$STAMP.tar.gz" -C /data .
done

STEP="rotation"
echo "==> rotating anything older than $KEEP_DAYS days"
find "$BACKUP_DIR/db" -type f -name '*.dump.gz' -mtime "+$KEEP_DAYS" -delete
find "$BACKUP_DIR/media" -type f -name '*.tar.gz' -mtime "+$KEEP_DAYS" -delete

trap - EXIT
echo "==> done: $STAMP"
du -sh "$BACKUP_DIR"/db "$BACKUP_DIR"/media
