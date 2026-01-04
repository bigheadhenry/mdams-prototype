#!/bin/bash

# Docker Registry Mirror Configuration Script
# Docker 镜像加速器配置脚本

echo "Configuring Docker registry mirrors..."

# 1. Determine Docker config path (Rootless vs Root)
# 1. 确定 Docker 配置路径（Rootless 与 Root）
if systemctl --user is-active docker &>/dev/null; then
    echo "Detected Rootless Docker."
    DOCKER_CONFIG_DIR="$HOME/.config/docker"
    SERVICE_RESTART_CMD="systemctl --user restart docker"
else
    echo "Detected Root Docker (or Rootless not active)."
    DOCKER_CONFIG_DIR="/etc/docker"
    SERVICE_RESTART_CMD="sudo systemctl restart docker"
    
    # Check for sudo access
    if [ "$EUID" -ne 0 ] && ! command -v sudo &> /dev/null; then
        echo "Error: Root access required for /etc/docker. Please run with sudo."
        exit 1
    fi
fi

# 2. Create directory if not exists
# 2. 如果不存在则创建目录
mkdir -p "$DOCKER_CONFIG_DIR"

# 3. Write daemon.json with multiple mirrors
# 3. 写入包含多个镜像源的 daemon.json
# Using known working mirrors (Nanjing Univ, DaoCloud, Aliyun public, etc.)
# 使用已知可用的镜像源（南京大学、DaoCloud、阿里云公共等）
# Use sudo tee to handle permissions
sudo tee "$DOCKER_CONFIG_DIR/daemon.json" > /dev/null <<EOF
{
  "registry-mirrors": [
    "https://docker.nju.edu.cn",
    "https://docker.m.daocloud.io",
    "https://dockerproxy.com",
    "https://mirror.baidubce.com",
    "https://docker.mirrors.sjtug.sjtu.edu.cn"
  ]
}
EOF

echo "Configuration written to $DOCKER_CONFIG_DIR/daemon.json"

# 4. Restart Docker
# 4. 重启 Docker
echo "Restarting Docker service..."
$SERVICE_RESTART_CMD

echo "Done! Verifying configuration..."
docker info | grep "Registry Mirrors" -A 5

echo ""
echo "Now you can try running './deploy.sh' again."
