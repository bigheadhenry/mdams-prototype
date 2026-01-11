# MEAM 系统需求规划说明书 (MEAM System Requirements Specification)

## 1. 项目背景与目标 (Background & Objectives)

* **项目名称**: MEAM (博物馆展览资产管理系统) 原型
* **部署环境**: 家庭实验室服务器 (`sunjing-server-eq12`), Linux/Docker 环境
* **文档中心**:
  * [🚀 快速开始 & 工作流指南 (Workflow Guide)](docs/WORKFLOW_GUIDE.md)
  * [🤖 AI 辅助开发与部署指南 (AI Setup Guide)](docs/AI_DEVELOPMENT_GUIDE.md)
  * [🏗️ 系统架构设计 (System Architecture)](docs/SYSTEM_ARCHITECTURE.md)
  * [📦 数据传输架构解析 (Data Ingest Architecture)](docs/DATA_INGEST_ARCHITECTURE.md)
  * [🍈 Cantaloupe 部署笔记 (Cantaloupe Notes)](docs/CANTALOUPE_DEPLOY_NOTES.md)
  * [🐳 Windows Docker 安装指南](docs/INSTALL_DOCKER_WINDOWS.md)
* **核心目标**:
  1. 建立统一的数字资产库，支持超大分辨率图像 (BigTIFF/PSB) 的存储与预览。
  2. 提供数字资源录入模块，提供录入界面，帮助完成数据录入，图像与数据匹配，以及图片自动加工缩略图等业务工作。
  3. 提供数字资源利用模块，具备可视化检索界面，具备收藏夹和购物车，可以完成选择图片，框选局部，录入利用单信息及提交。可以自动按照利用单需求加工图片并生成交付数据。
  4. 验证容器化部署方案的可行性。

## 2. 核心功能模块 (Core Modules)

### 2.1 数字资源录入模块 

* **多格式上传**: 支持 JPG, PNG, MP4 以及专业格式 **PSB/BigTIFF** (集成之前的转换逻辑)。
* **元数据提取**: 自动提取 Exif, IPTC 信息（拍摄时间、设备、版权）。
* **智能预览**:
  * 普通图片：生成 WebP 缩略图。
  * **超大图片**: 集成 **Mirador 3** 查看器，基于 **IIIF Presentation API 3.0** 规范。
  * **Manifest 生成**: 后端动态生成符合 IIIF 规范的 Manifest JSON，自动映射元数据与 Cantaloupe 图像服务。

### 2.2 数字资源利用模块 (Exhibition Planning)

* **可视化检索**: 可以以图搜图，也可以多条件交叉检索，可以多选检索后的图片，加入购物车或收藏夹。
* **购物车**: 可以归集选择的数据，可以选择图片需要的规格和格式，可以进一步选择图片中的局部作为利用数据，可以一键导出购物车清单。
* **自动交付**: 购物车点击提交利用单后，后台可以自动根据需要的规格和格式进行加工，并将完成数据打包提供下载链接。

### 2.3 系统管理模块 (System Admin)

* **用户管理**: 简单的基于角色的访问控制 (RBAC)。
* **存储监控**: 实时显示服务器磁盘空间占用情况。

## 3. 技术架构设计 (Technical Architecture)

采用 **前后端分离** + **容器化** 架构，确保易部署、易迁移。

| 层次 | 技术选型 | 说明 |
| :--- | :--- | :--- |
| **前端交互层** | **React 18 + Ant Design** | 现代化的管理后台 UI，操作流畅。 |
| **后端服务层** | **FastAPI (Python 3.12)** | 高性能异步框架，集成 `libvips` 处理图像。 |
| **图像服务层** | **Cantaloupe IIIF Server** | 专门用于超大分辨率图像 (BigTIFF) 的切片与流式预览。 |
| **数据持久层** | **PostgreSQL** | 存储资产元数据、展览关系结构。 |
| **文件存储** | **Local FS / MinIO** | 映射服务器物理路径，方便直接管理文件。 |
| **部署架构** | **Docker Compose** | 一键编排所有服务，包含 Nginx 反向代理。 |

## 4. 实施路线图 (Implementation Roadmap)

### 阶段一：原型构建 (本次任务)

1. **环境搭建**: 初始化 Docker Compose 项目结构。
2. **后端开发**: 实现文件上传 API、元数据解析、数据库模型设计。
3. **前端开发**: 搭建资产列表页、上传组件、详情页。
4. **部署验证**: 在 `sunjing-server-eq12` 上跑通流程。

### 阶段二：高级功能 (未来规划)

1. 集成 PSB 转 BigTIFF 自动化流水线。
2. 引入 AI 标签识别（如自动识别画作内容）。
3. 3D 展厅可视化预览。
