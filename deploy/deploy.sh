#!/usr/bin/env sh
# Bring a new image live. Run from the project directory on the server.
#
#   ./deploy/deploy.sh ghcr.io/owner/flowers:<sha>
#
# The order is the one section 5 asks for: migrations run to completion before
# anything is restarted, so the new code never meets an old schema. A rollback
# is the same command with the previous tag.

set -eu

IMAGE="${1:-}"
if [ -z "$IMAGE" ]; then
    echo "usage: $0 <image>" >&2
    exit 2
fi

COMPOSE="docker compose -f compose.prod.yaml"
export IMAGE

echo "==> pulling $IMAGE"
$COMPOSE pull

echo "==> waiting for the database"
$COMPOSE up -d db redis
$COMPOSE exec -T db sh -c 'until pg_isready -U "${POSTGRES_USER:-flowers}"; do sleep 1; done'

echo "==> migrating"
$COMPOSE run --rm --no-deps web python manage.py migrate --noinput

echo "==> collecting static files"
$COMPOSE run --rm --no-deps collectstatic

echo "==> restarting"
$COMPOSE up -d web celery celery-beat nginx

echo "==> smoke"
./deploy/smoke.sh "${SITE_URL:-http://localhost}"

echo "==> $IMAGE is live"
echo "    to roll back: ./deploy/deploy.sh <previous tag>"
