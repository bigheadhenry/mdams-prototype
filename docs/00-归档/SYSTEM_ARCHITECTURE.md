# MEAM Prototype 系统架构与功能说明文档

本文档详细描述了 MEAM (Museum Enterprise Asset Management) 原型系统的技术架构、核心功能及设计理念。该系统专为实验室环境（N100 服务器 + QNAP NAS）设计，旨在验证混合存储架构下的数字资产管理与 IIIF 高清图像服务能力。

## 1. 系统概览 (System Overview)

MEAM Prototype 是一个轻量级的数字资产管理系统，核心能力在于对高分辨率文物图像的存储、管理与 IIIF 标准化展示。系统采用微服务架构，前后端分离，针对低功耗服务器（Intel N100）进行了专门的性能优化。

### 1.1 核心价值
*   **IIIF 原生支持**: 遵循 IIIF Presentation API 3.0 标准，支持跨机构图像互操作。
*   **混合存储架构**: 结合本地 SSD 的高性能与 NAS 的大容量，实现成本与性能的平衡。
*   **深度缩放预览**: 集成 Mirador 查看器，支持 GB 级超大图像的流畅缩放与平移。

---

## 2. 技术架构 (Technical Architecture)

系统由四个核心容器化服务组成，通过 Docker Compose 进行编排。

### 2.1 架构图示

```mermaid
graph TD
    User[用户 (Browser)] --> |HTTP/80| Nginx[前端反向代理]
    Nginx --> |/| Frontend[React + AntD]
    Nginx --> |/api| Backend[FastAPI]
    
    Backend --> |读写| DB[(PostgreSQL)]
    Backend --> |写入流| NAS[QNAP NAS (NFS)]
    
    User --> |IIIF 图像请求| Cantaloupe[Cantaloupe Image Server]
    Cantaloupe --> |读取| NAS
    Cantaloupe --> |缓存| SSD[本地 NVMe SSD]
```

### 2.2 组件详解

#### A. 前端服务 (Frontend)
*   **技术栈**: React 18, Vite, TypeScript, Ant Design
*   **核心组件**:
    *   **Dashboard**: 资产统计与系统状态监控。
    *   **Asset Table**: 资产列表管理，支持元数据查看与状态追踪。
    *   **Mirador Viewer**: 集成 Mirador 3，提供专业的 IIIF 图像深度交互体验（缩放、多窗口对比）。
*   **构建优化**: 针对 N100 内存限制，调整了 Node 构建时的内存堆栈上限。

#### B. 后端服务 (Backend)
*   **技术栈**: Python 3.12, FastAPI, SQLAlchemy
*   **核心职责**:
    *   **REST API**: 提供资产增删改查接口。
    *   **IIIF Manifest Generator**: 动态生成符合 IIIF Presentation 3.0 标准的 JSON 描述文件。
    *   **流式上传**: 采用 64KB 分块流式写入策略，确保上传大文件时内存占用极低。
*   **数据模型**:
    *   `Asset`: 存储文件名、路径、MIME类型、文件大小及扩展元数据 (Exif/IPTC)。

#### C. 图像服务 (Image Server)
*   **组件**: Cantaloupe IIIF Image Server 5.0.6
*   **配置优化**:
    *   **处理器**: 强制使用 `Java2dProcessor` 以获得比 TurboJpeg 更稳定的内存控制。
    *   **缓存策略**: 禁用堆内存缓存 (`heap cache`)，完全依赖文件系统缓存 (`FilesystemCache`)，以适应 16GB 总内存限制。
    *   **源数据**: 直接通过 NFS 挂载读取 NAS 上的原始图像文件。

#### D. 数据存储 (Storage Layer)
*   **数据库**: PostgreSQL 16 (Alpine版)
    *   存储位置: 本地 NVMe SSD (`./db_data`)，确保查询高性能。
*   **文件存储**:
    *   **热数据 (Hot)**: 缩略图、图像瓦片缓存 -> 本地 SSD。
    *   **冷数据 (Cold)**: 原始 TIFF/PSB 大图 -> QNAP NAS。

---

## 3. 核心功能流程 (Core Workflows)

### 3.1 资产上传与处理
1.  用户通过前端拖拽上传文件。
2.  前端将文件流发送至 `/api/upload`。
3.  后端以 **64KB Chunk** 为单位接收数据，并实时写入 NAS 挂载目录 (`/app/uploads`)，避免内存缓冲。
4.  写入完成后，后端提取文件元数据（大小、类型）并存入 PostgreSQL。
5.  资产状态标记为 `ready`，即刻可被访问。

### 3.2 IIIF 图像预览
1.  用户点击“View in Mirador”按钮。
2.  前端请求后端生成的 Manifest URL: `/iiif/{id}/manifest`。
3.  后端动态构建 IIIF Manifest JSON，包含：
    *   Canvas 定义（画布尺寸）。
    *   Image Service 定义（指向 Cantaloupe 的服务地址）。
4.  Mirador 解析 Manifest，向 Cantaloupe 请求具体的图像瓦片 (Tiles)。
5.  Cantaloupe 从 NAS 读取原图，按需裁剪缩放，将生成的瓦片缓存至 SSD 并返回给浏览器。

---

## 4. 部署与环境 (Deployment)

### 4.1 硬件要求
*   **应用服务器**: Ubuntu 24.04 (Docker Rootless), Intel N100, 16GB RAM.
*   **存储服务器**: 支持 NFS v4 的 NAS 设备。

### 4.2 目录结构
```text
/meam-prototype
├── backend/            # Python API 服务代码
├── frontend/           # React 前端代码
├── cantaloupe/         # 图像服务器配置与构建文件
├── docker-compose.yml  # 容器编排定义
├── deploy.sh           # 一键部署脚本
└── DEPLOYMENT.md       # 部署操作手册
```

### 4.3 端口映射
*   **3000**: Web 前端访问入口。
*   **8000**: 后端 API 文档 (Swagger UI)。
*   **8081**: FileBrowser (文件系统直接管理)。
*   **8182**: Cantaloupe 管理控制台。

## 5. 扩展性设计 (Future Roadmap)

*   **元数据提取**: 集成 `libvips` 或 `ExifTool`，在上传后自动提取图像的物理尺寸、色彩空间等深度信息。
*   **OCR 集成**: 利用 IIIF Annotation 机制，叠加 Tesseract OCR 识别的文字层。
*   **权限控制**: 基于 JWT 的用户认证与基于 IP 的图像访问授权。
