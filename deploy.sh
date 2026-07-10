#!/bin/bash

# MEAM Prototype Deployment Script for N100 Lab Server
# MDAMS Prototype Deployment Script for N100 Lab Server

set -e

echo "=== MDAMS Deployment ==="

# 1. Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    exit 1
fi

# 1b. Check for docker compose plugin
if ! docker compose version &> /dev/null; then
    echo "Error: docker compose plugin is not available."
    exit 1
fi

# 2. Ensure directories exist
echo "Creating local data directories..."
mkdir -p db_data

# 3. Build and Start Services
echo "Building and starting containers..."
docker compose up -d --build

# 4. Wait for services to be healthy
echo "Waiting for services to become healthy..."
MAX_RETRIES=30  # 30 retries × 3s = 90s max wait
RETRY_COUNT=0

check_health() {
    local service="$1"
    local container_id
    local state

    container_id=$(docker compose ps -q "$service" 2>/dev/null)
    [ -n "$container_id" ] || return 1

    state=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id" 2>/dev/null || true)
    [ "$state" = "healthy" ]
}

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    ALL_HEALTHY=true
    for svc in db redis backend; do
        if ! check_health "$svc"; then
            ALL_HEALTHY=false
            break
        fi
    done
    if $ALL_HEALTHY; then
        echo "All services healthy."
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "Warning: Some services may not be fully ready yet."
        docker compose ps
    else
        sleep 3
    fi
done

# 5. Show final status
echo ""
echo "=== Service Status ==="
docker compose ps

# Resolve the actual published ports from Compose so the summary stays
# correct when .env overrides the default port mappings.
published_port() {
    local service="$1"
    local container_port="$2"
    local fallback_port="$3"
    local binding

    binding=$(docker compose port "$service" "$container_port" 2>/dev/null | head -n 1 || true)
    if [ -n "$binding" ]; then
        printf '%s\n' "${binding##*:}"
    else
        printf '%s\n' "$fallback_port"
    fi
}

DEPLOY_HOST=${DEPLOY_HOST:-$(hostname -I 2>/dev/null | awk '{print $1}')}
DEPLOY_HOST=${DEPLOY_HOST:-localhost}
FRONTEND_PUBLISHED_PORT=$(published_port frontend 80 "${FRONTEND_PORT:-3000}")
BACKEND_PUBLISHED_PORT=$(published_port backend 8000 "${BACKEND_PORT:-8000}")

echo ""
echo "=== Deployment Complete ==="
echo "Frontend:      http://${DEPLOY_HOST}:${FRONTEND_PUBLISHED_PORT}"
echo "Backend API:   http://${DEPLOY_HOST}:${BACKEND_PUBLISHED_PORT}"
echo "API Docs:      http://${DEPLOY_HOST}:${BACKEND_PUBLISHED_PORT}/docs"
echo "Cantaloupe:    internal only; access images through the frontend/backend IIIF proxy"
