#!/bin/bash

# MDAMS Prototype Deployment Script
# MDAMS 原型部署脚本

set -e

echo "=== MDAMS Deployment ==="

# 1. Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
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
    local state
    state=$(docker compose ps --format "table {{.Service}}\t{{.Status}}" 2>/dev/null | grep "^${service}\s" | awk '{print $2}')
    echo "$state" | grep -q "(healthy)" && return 0
    return 1
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

echo ""
echo "=== Deployment Complete ==="
echo "Frontend:      http://localhost:3000"
echo "Backend API:   http://localhost:8000"
echo "API Docs:      http://localhost:8000/docs"
echo "Cantaloupe:    http://localhost:8182"
