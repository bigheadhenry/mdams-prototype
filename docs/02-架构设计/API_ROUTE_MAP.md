# API 路由总览

- 最后核对日期：2026-04-06
- 核对范围：`backend/app/main.py`、`backend/app/routers/`

## 1. 目标

本文件用于总结当前后端 API 的主路由分区、核心职责和典型接口，帮助开发和文档编写快速定位功能入口。

## 2. 路由分区

当前 `backend/app/main.py` 已注册以下路由：

| 路由模块 | 前缀 | 主要职责 |
| :--- | :--- | :--- |
| `health` | 无显式前缀 | 健康检查、就绪检查 |
| `auth` | `/auth` | 登录、退出、用户列表、上下文 |
| `assets` | `/assets` 等 | 二维资产上传、列表、详情、预览、下载 |
| `applications` | `/applications` | 申请单创建、列表、审批、导出 |
| `ai_mirador` | `/ai` | Mirador AI 相关接口 |
| `iiif` | `/iiif` | Manifest 与 IIIF 代理访问 |
| `downloads` | 无显式前缀 | 下载相关扩展接口 |
| `ingest` | `/ingest` | SIP 风格入库流程 |
| `image_records` | `/image-records` | 图像记录工作流 |
| `three_d` | `/three-d` | 三维对象、版本、文件与查看 |
| `platform` | `/platform` | 统一来源、统一目录、统一详情 |

## 3. 模块说明

### 3.1 `health`

主要用于运行状态检查：

- `/health`
- `/ready`

适合部署脚本、容器监测和故障排查使用。

### 3.2 `auth`

当前认证骨架的主入口：

- `GET /api/auth/users`
- `POST /api/auth/login`
- `GET /api/auth/context`
- `POST /api/auth/logout`

### 3.3 `assets`

二维资产主入口，覆盖：

- 列表
- 上传
- 详情
- 删除
- 预览图
- 下载
- BagIt 下载

典型接口：

- `GET /api/assets`
- `POST /api/upload`
- `GET /api/assets/{asset_id}`
- `DELETE /api/assets/{asset_id}`
- `GET /api/assets/{asset_id}/preview`

### 3.4 `applications`

利用申请工作流入口：

- `POST /api/applications`
- `GET /api/applications`
- `GET /api/applications/{application_id}`
- `POST /api/applications/{application_id}/approve`
- `POST /api/applications/{application_id}/reject`
- `GET /api/applications/{application_id}/export`

### 3.5 `iiif`

负责二维图像预览相关 API：

- `GET /api/iiif/{asset_id}/manifest`
- `GET /api/iiif/{asset_id}/service/{image_path:path}`

当前 Manifest 已经受权限与可见范围控制。

### 3.6 `ingest`

负责 SIP 风格导入链路，主要服务二维入库。

它与 `assets` 的简单上传不同，更偏结构化入库。

### 3.7 `image_records`

负责图像记录拆分工作流：

- 图像记录创建
- 编辑
- 提交 / 退回
- 待上传池
- 文件上传分析
- 明确绑定 / 替换

### 3.8 `three_d`

负责三维子系统：

- 对象与版本
- 资源包上传
- 文件角色识别
- 查看摘要
- 明细与下载

### 3.9 `platform`

负责统一平台聚合：

- `GET /api/platform/sources`
- `GET /api/platform/resources`
- `GET /api/platform/resources/{resource_id}`

### 3.10 `ai_mirador`

负责 Mirador AI 辅助功能，服务于前端 AI 面板。

## 4. 当前接口边界

当前接口设计已经形成三层边界：

- 资源来源接口：`assets`、`three_d`
- 平台聚合接口：`platform`
- 工作流接口：`auth`、`applications`、`image_records`

这意味着当前系统已经不是单一 CRUD，而是开始形成子系统 + 聚合层 + 工作流层的结构。

## 5. 关联文档

- `ARCHITECTURE.md`
- `PLATFORM_SOURCE_ADAPTERS.md`
- `THREE_D_SUBSYSTEM_ARCHITECTURE.md`
- `../03-产品与流程/WORKFLOW_GUIDE.md`
