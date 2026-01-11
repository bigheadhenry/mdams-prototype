# AI 辅助开发与部署指南 (AI Development & Deployment Guide)

本指南旨在帮助 AI 编码助手（如 Vibe Coding IDE）或新加入的开发者快速理解项目的技术栈、依赖关系及部署要求。

## 1. 项目概览 (Project Overview)

*   **项目名称**: MEAM Prototype (Museum Exhibition Asset Management)
*   **核心功能**: 超大分辨率图像 (BigTIFF/PSB) 存储、IIIF 预览、数字资产录入与利用。
*   **架构模式**: 前后端分离 + 容器化部署 (Docker Compose)。

## 2. 技术栈清单 (Tech Stack)

### 2.1 前端 (Frontend)
*   **框架**: React 18 + TypeScript + Vite 5
*   **UI 库**: Ant Design 5.x
*   **关键组件**:
    *   `mirador`: IIIF 图像查看器 (v3.3.0)
    *   `exifr`: 前端元数据提取
    *   `axios`: HTTP 请求
*   **运行环境**: Node.js 18+ (推荐 20 LTS)

### 2.2 后端 (Backend)
*   **框架**: FastAPI (Python 3.12)
*   **数据库**: PostgreSQL 16 (通过 SQLAlchemy ORM 访问)
*   **核心库**:
    *   `libvips`: 高性能图像处理 (必须在 OS 层安装)
    *   `python-multipart`: 处理大文件上传
    *   `aiofiles`: 异步文件操作
*   **运行环境**: Python 3.12 (推荐使用 Docker 隔离)

### 2.3 图像服务 (Image Server)
*   **服务**: Cantaloupe IIIF Server v5.0.6
*   **依赖**: OpenJDK 11
*   **底层处理器**:
    *   `GraphicsMagick`: 处理 Raw/JPEG/TIFF
    *   `FFmpeg`: 处理视频缩略图
    *   `Java2D`: 处理普通图片 (作为备选)

## 3. 环境与依赖要求 (Environment Requirements)

### 3.1 操作系统
*   **推荐**: Linux (Ubuntu 22.04 LTS / Debian 11+)
*   **支持**: Windows 10/11 (必须启用 WSL2 + Docker Desktop)
*   **不支持**: 纯 Windows CMD/PowerShell 环境 (由于 libvips 和 Docker 路径映射问题，不建议直接运行后端)

### 3.2 必须安装的系统级依赖 (System Dependencies)

如果不在 Docker 中运行，必须手动安装以下库：

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y libvips libvips-dev libvips-tools ffmpeg graphicsmagick build-essential
```

**Windows (仅开发前端时):**
*   Node.js 18+
*   Git

### 3.3 Docker 环境
*   Docker Engine 24.0+
*   Docker Compose v2.0+

## 4. 配置说明 (Configuration)

### 4.1 环境变量 (.env)
项目依赖环境变量来配置数据库连接和公共 IP。在 `docker-compose.yml` 中定义了默认值，生产环境建议使用 `.env` 文件覆盖。

关键变量说明：

| 变量名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `API_PUBLIC_URL` | `http://192.168.5.13:3000/api` | **必须修改**为部署机器的实际 IP。前端 Mirador 使用此地址获取 Manifest。 |
| `CANTALOUPE_PUBLIC_URL` | `http://192.168.5.13:3000/iiif/2` | **必须修改**为部署机器的实际 IP。Nginx 反向代理地址。 |
| `DATABASE_URL` | `postgresql://meam:meam_secret@db:5432/meam_db` | 数据库连接串。 |
| `VIPS_DISC_THRESHOLD` | `100m` | libvips 内存阈值，超过此值使用磁盘缓存，防 OOM。 |

### 4.2 配置文件映射
*   **Nginx**: `./frontend/nginx.conf` -> 容器内 `/etc/nginx/conf.d/default.conf`
*   **Cantaloupe**: `./cantaloupe/cantaloupe.properties` -> 容器内 `/etc/cantaloupe.properties`

**注意**: 修改 `cantaloupe.properties` 后必须重启容器才能生效。

## 5. 快速启动 (Quick Start)

### 步骤 1: 克隆代码
```bash
git clone <repository_url>
cd meam-prototype
```

### 步骤 2: 修改 IP 配置
打开 `docker-compose.yml`，找到 `backend` 服务下的 `environment` 区域，将 `API_PUBLIC_URL` 和 `CANTALOUPE_PUBLIC_URL` 中的 IP 地址（默认 192.168.5.13）修改为您当前机器的局域网 IP。

### 步骤 3: 启动服务
```bash
docker-compose up -d --build
```
首次启动需要构建 backend 和 frontend 镜像，如下载依赖较慢请配置 Docker 镜像加速。

### 步骤 4: 访问系统
*   **Web 界面**: `http://localhost:3000` (或 `http://<您的IP>:3000`)
*   **API 文档**: `http://localhost:8000/docs`
*   **Cantaloupe 控制台**: `http://localhost:8182` (默认用户/密码在 properties 文件中定义，通常为 admin/admin)

## 6. 常见问题排查 (Troubleshooting)

### Q1: 图片上传成功但无法预览 (404/500/501)
*   **检查 404**: 确认 `docker-compose.yml` 中的卷挂载路径是否正确。Linux 下路径区分大小写。
*   **检查 501**: 通常是 Cantaloupe 处理器配置问题。检查 `cantaloupe.properties` 中 `processor.jpg` 是否指定为 `GraphicsMagickProcessor`。
*   **检查 500**: 查看容器日志 `docker logs meam-cantaloupe`。

### Q2: 跨域错误 (CORS)
*   确保前端通过 Nginx 代理访问后端 (`/api/...`) 和图像服务 (`/iiif/...`)，而不是直接访问 8000 或 8182 端口。
*   检查 `API_PUBLIC_URL` 是否配置为 Nginx 的地址。

### Q3: 数据库连接失败
*   确认 `db` 容器是否健康 (`docker ps`)。
*   确认 `backend` 容器是否在同一个 Docker 网络中。
