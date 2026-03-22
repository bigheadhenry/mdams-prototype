#!/bin/bash

# MEAM Prototype Deployment Script for N100 Lab Server
# MEAM 原型部署脚本 (适用于 N100 实验室服务器)

echo "Starting MEAM Prototype Deployment..."

# 1. Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    exit 1
fi

# 2. Ensure directories exist
echo "Creating local data directories..."
mkdir -p db_data
# Note: /sunjing/project is expected to be mounted via NFS
# 注意: /sunjing/project 应已通过 NFS 挂载

# 3. Build and Start Services
echo "Building and starting containers..."
docker compose up -d --build

# 4. Wait for services to be ready
echo "Waiting for services to initialize..."
sleep 10

# 5. Check status
echo "Service Status:"
docker compose ps

echo ""
echo "Deployment Complete!"
echo "Frontend: http://192.168.5.13:3000"
echo "Backend API: http://192.168.5.13:8000"
echo "FileBrowser: http://192.168.5.13:8081"
echo "Cantaloupe: http://192.168.5.13:8182"
