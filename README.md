# MDAMS Prototype

**Museum Digital Asset Management System Prototype**

一个面向博物馆 / 展览数字资源场景的原型系统，当前重点验证以下能力：

- 数字资产上传、入库与基础管理
- PSB / BigTIFF 等超大图像处理链路
- 基于 IIIF 的标准化图像服务与预览
- 面向家庭实验室环境的容器化部署可行性

当前项目更准确地说是：

> **以数字资产入库、超大图像处理和 IIIF 预览为核心的技术原型。**

---

## 1. 当前核心能力

### 已实现

- 基础文件上传与资产列表管理
- SIP 风格入库接口
- SHA256 fixity 校验
- 图像元数据提取（Exif / IPTC 等）
- IIIF Manifest 动态生成
- Mirador 预览集成
- PSB 异步转换 BigTIFF
- BagIt ZIP 打包下载
- Docker Compose 容器化部署结构

### 规划中 / 待完善

- 高级检索与筛选
- 资产详情页
- 收藏夹 / 购物车
- 利用申请单与自动交付
- 用户与权限管理
- 更完整的编目模型与衍生文件关系

---

## 2. 技术架构概览

| 层次 | 技术选型 | 说明 |
| :--- | :--- | :--- |
| 前端交互层 | React 18 + Vite + TypeScript + Ant Design | 管理后台 UI 与入库演示界面 |
| 后端服务层 | FastAPI + SQLAlchemy | 资产管理、上传、Manifest 生成、下载接口 |
| 异步任务层 | Celery + Redis | PSB 转 BigTIFF 等后台任务 |
| 图像服务层 | Cantaloupe IIIF Server | 超大图像切片与 IIIF 服务 |
| 数据持久层 | PostgreSQL | 存储资产与元数据记录 |
| 文件与部署层 | Docker Compose + 本地/NAS 存储 | 容器编排与实验室环境落地 |

---

## 3. 项目结构

```text
backend/        FastAPI 后端服务
frontend/       React 前端界面
cantaloupe/     Cantaloupe 镜像与相关配置
docs/           项目文档
docker-compose.yml  容器编排入口
```

当前部署结构主要包括：

- frontend
- backend
- celery_worker
- db
- redis
- cantaloupe
- filebrowser

---

## 4. 文档导航

### 项目入口文档
- [项目现状与开发路线图](docs/PROJECT_STATUS.md)
- [工作流指南](docs/WORKFLOW_GUIDE.md)
- [AI 辅助开发与部署指南](docs/AI_DEVELOPMENT_GUIDE.md)

### 架构与部署文档
- [系统架构说明](docs/SYSTEM_ARCHITECTURE.md)
- [项目架构文档](docs/ARCHITECTURE.md)
- [部署指南](docs/DEPLOYMENT.md)
- [数据传输架构解析](docs/DATA_INGEST_ARCHITECTURE.md)
- [Cantaloupe 部署笔记](docs/CANTALOUPE_DEPLOY_NOTES.md)

### 参考与补充文档
- [手动图像处理指南](docs/MANUAL_IMAGE_GUIDE.md)
- [Git 部署指南](docs/GIT_DEPLOY_GUIDE.md)
- [Windows Docker 安装指南](docs/INSTALL_DOCKER_WINDOWS.md)

---

## 5. 当前阶段判断

当前项目最成熟的部分是：

1. 数字资产入库主链路
2. PSB → BigTIFF → IIIF 预览链路
3. Manifest 动态生成能力
4. 面向真实实验环境的部署结构

当前项目仍然主要是一个：

> **高价值技术原型，而非完整业务化 DAMS。**

这意味着它已经证明关键技术路线可行，但后续仍需要继续补齐：

- 业务模型
- 检索与利用流程
- 用户与权限体系
- 更清晰的模块边界与配置管理

---

## 6. 建议的下一步工作

建议优先推进以下方向：

1. 统一命名与文档入口
2. 整理后端模块结构
3. 逐步抽离运行配置
4. 固化标准演示流程
5. 补齐资产详情与衍生文件关系模型

更完整的阶段规划见：

- [项目现状与开发路线图](docs/PROJECT_STATUS.md)

---

## 7. 项目目标（中长期）

中长期目标是将该原型逐步演进为一个适用于博物馆 / 展览数字资源场景的 MDAMS 系统，支持：

- 数字资源录入
- 超大图像标准化预览
- 检索与筛选
- 利用申请与自动交付
- 更规范的元数据与资产管理流程
