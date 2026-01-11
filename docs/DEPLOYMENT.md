# MDAMS 部署指南 (Deployment Guide)

本指南专门针对 **N100 实验室服务器 (192.168.5.13)** 与 **QNAP NAS (192.168.5.16)** 的混合架构环境。

## 1. 基础设施要求 (Infrastructure)

| 节点 | 角色 | IP 地址 | 关键配置 |
| :--- | :--- | :--- | :--- |
| **Compute Node** | 应用服务/数据库 | `192.168.5.13` | Ubuntu 24.04, Docker (Rootless), 16GB RAM, NVMe SSD |
| **Storage Node** | 原始文件存储 | `192.168.5.16` | QNAP NAS, NFS v4 (No Root Squash) |

### 关键路径映射
*   **NAS 挂载点 (Host)**: `/sunjing/project`
*   **文物库路径 (Host)**: `/sunjing/project/文物库`
*   **容器内映射**: `/app/uploads` (Backend), `/var/lib/cantaloupe/images` (Cantaloupe)

## 2. 部署步骤 (Deployment Steps)

### 2.1 代码传输
在开发机上将代码传输至服务器：
```powershell
scp -r d:\Coding\meam-prototype bigheadhenry@192.168.5.13:/home/bigheadhenry/
```

### 2.2 服务器环境检查
登录服务器并确认 NAS 挂载状态：
```bash
ssh bigheadhenry@192.168.5.13
ls -ld /sunjing/project/文物库
# 确认输出显示目录存在且可访问
```

### 2.3 启动服务
进入项目目录并运行部署脚本：
```bash
cd meam-prototype
chmod +x deploy.sh
./deploy.sh
```

脚本会自动执行以下操作：
1.  检查 Docker 环境。
2.  创建本地数据目录 (`db_data`) 以利用 SSD 性能。
3.  构建并启动所有容器。

## 3. 服务访问 (Service Access)

| 服务名称 | 端口 | URL | 账号/说明 |
| :--- | :--- | :--- | :--- |
| **Web 前端** | 3000 | `http://192.168.5.13:3000` | 主界面，资产管理与预览 |
| **后端 API** | 8000 | `http://192.168.5.13:8000/docs` | Swagger API 文档 |
| **FileBrowser** | 8081 | `http://192.168.5.13:8081` | 文件直接管理 (无验证模式) |
| **Cantaloupe** | 8182 | `http://192.168.5.13:8182` | IIIF 图像服务控制台 |

## 4. 性能优化说明 (Performance Optimization)

针对 N100 (16GB RAM) 的特别配置：

### 内存控制 (Memory)
*   **Backend (libvips)**: 
    *   `VIPS_DISC_THRESHOLD=100m`: 大于 100MB 的图像处理强制使用磁盘缓存，防止 OOM。
    *   上传采用 64KB 分块流式写入，避免内存峰值。
*   **Cantaloupe (IIIF)**:
    *   `JAVA_OPTS=-Xmx4g`: 限制 Java 堆内存为 4GB。
    *   `cache.server.memory.enabled=false`: 禁用内存缓存，完全依赖 SSD 文件缓存。
*   **PostgreSQL**:
    *   Docker 资源限制 `memory: 2G`。

### 存储 I/O (Storage)
*   **热数据 (Hot)**: 数据库、缩略图缓存 -> **本地 NVMe SSD**。
*   **冷数据 (Cold)**: 原始 PSB/TIFF 大图 -> **NAS (NFS)**。

## 5. 故障排查 (Troubleshooting)

*   **权限错误 (Permission Denied)**:
    检查 NAS 挂载点的权限。确保当前用户 (`bigheadhenry`) 对 `/sunjing/project` 有读写权限。
    ```bash
    ls -l /sunjing/project
    ```

*   **服务启动失败**:
    查看容器日志：
    ```bash
    docker compose logs -f backend
    docker compose logs -f cantaloupe
    ```

*   **大图预览卡顿**:
    检查 Cantaloupe 日志，确认是否正在生成缓存（首次访问较慢是正常的）。
