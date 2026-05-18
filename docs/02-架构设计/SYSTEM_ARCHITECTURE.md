# MDAMS Prototype 系统架构与功能说明

- 最后核对日期：2026-05-17
- 核对基准：稳定提交中的 `docker-compose.yml`、`backend/app/main.py`、`frontend/nginx.conf`、平台适配器与 IIIF 路由。

## 1. 系统概览

MDAMS Prototype 是面向博物馆数字资源管理的原型系统。当前稳定形态已经不只是二维图像上传工具，而是包含：

- 二维资产管理、IIIF Manifest、Mirador 预览与 BagIt 导出
- 图像记录协作工作流
- 三维对象、版本与文件包管理
- 视频资源管理与播放入口
- 统一资源目录与统一详情层
- 角色、权限、责任范围和可见范围控制

## 2. 运行组件

当前 compose 中的主要服务如下：

| 服务 | 角色 |
|---|---|
| `frontend` | React + Vite 前端，由 Nginx 提供静态站点并代理 `/api/` |
| `backend` | FastAPI 应用，注册认证、资产、IIIF、三维、视频、统一平台等路由 |
| `celery_worker` | 后台任务 Worker，负责图像处理等异步作业 |
| `redis` | Celery Broker |
| `db` | PostgreSQL 数据库 |
| `cantaloupe` | IIIF Image API 上游图像服务 |

当前稳定 compose 中没有 FileBrowser 服务；历史文档中出现的 `8081 FileBrowser` 应视为旧资料。

## 3. 架构图

```mermaid
graph TD
    User[浏览器用户] -->|http://localhost:3000| Frontend[Nginx + React 前端]
    Frontend -->|/api/*| Backend[FastAPI 后端]

    Backend --> DB[(PostgreSQL)]
    Backend --> Redis[(Redis)]
    Worker[Celery Worker] --> Redis
    Worker --> Uploads[上传与资源目录]
    Backend --> Uploads

    Backend -->|/api/iiif/{asset_id}/service/*| Cantaloupe[Cantaloupe IIIF Server]
    Cantaloupe --> Uploads

    Backend --> Platform[统一平台适配器]
    Platform --> Image2D[image_2d]
    Platform --> ThreeD[three_d]
    Platform --> Video[video]
```

## 4. 后端路由分层

当前 FastAPI 应用注册的主要能力包括：

| 能力 | 路由前缀或入口 |
|---|---|
| 健康检查 | `/health`、`/ready` |
| 认证与用户上下文 | `/api/auth/*` |
| 二维资产 | `/api/assets/*` |
| IIIF Manifest 与图像服务代理 | `/api/iiif/*` |
| 下载与 BagIt | `/api/assets/{id}/download*` |
| 图像记录工作流 | `/api/image-records/*` |
| 三维资源 | `/api/three-d/*` |
| 视频资源 | `/api/video/*` |
| 统一平台目录与详情 | `/api/platform/*` |
| Mirador AI 辅助 | `/api/ai-mirador/*` |

统一平台详情的主契约是：

```text
GET /api/platform/resources/{source_system}/{source_id}
```

历史兼容路由 `/api/platform/resources/{resource_id}` 仍保留，但已标记为 deprecated。

## 5. IIIF 链路

当前稳定链路是：

1. 浏览器访问前端或 API。
2. 前端请求 `/api/iiif/{asset_id}/manifest`。
3. 后端校验 `image.view` 权限和资源可见范围。
4. Manifest 中的图像服务入口指向后端代理：`/api/iiif/{asset_id}/service/{image_path}`。
5. 后端代理再次校验资源可见性，并把请求转发到 Cantaloupe 上游。
6. Cantaloupe 读取上传目录中的 IIIF 源文件并返回 `info.json` 或切片。

因此，当前文档不应再描述为“浏览器直接向 Cantaloupe 请求图像瓦片”的主路径。Cantaloupe 可以用于本地调试或内部上游，但生产部署应避免形成权限旁路。

## 6. 存储与数据

| 类型 | 当前用途 |
|---|---|
| PostgreSQL | 用户、资产、图像记录、三维、视频、申请与元数据 |
| Redis | Celery Broker |
| `HOST_MUSEUM_PATH` / `/app/uploads` | 上传文件、访问副本、三维包和视频文件 |
| Cantaloupe 图像目录 | 挂载同一资源目录，用作 IIIF 上游读取位置 |

## 7. 当前结论

MDAMS 当前稳定架构可以概括为：

> 前端统一进入 `/api/`，后端负责业务权限、资源契约和 IIIF 代理；Cantaloupe 是后端控制下的图像服务上游；统一平台通过 `image_2d`、`three_d`、`video` 三类适配器聚合资源。
