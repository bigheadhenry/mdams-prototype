# MDAMS Prototype

MDAMS Prototype 是一个面向馆内业务场景的数字资源管理原型仓库。它当前不再只是“单一二维影像上传 PoC”，而是已经形成了一个由二维影像子系统、三维资源子系统、统一平台目录、利用申请流程、登录与权限框架组成的可持续开发底座。

当前阶段更准确的定位是：

> 一个可稳定运行、可持续迭代、可用于演示与验证的馆内数字资源管理原型，而不是完整生产级 DAMS。

## 当前已覆盖的能力

### 二维影像

- 资产上传、列表、详情与预览图
- 图像记录 `ImageRecord` 录入、提交、退回、待上传池
- 文件与记录匹配、基础校验、重复检测
- IIIF Manifest 生成与 Mirador 预览
- 原文件下载与 BagIt 下载
- 衍生文件策略与 IIIF access 流程

### 利用申请

- 申请车
- 申请单提交
- 审批通过 / 拒绝
- 交付包导出

### 三维资源

- 三维对象与版本管理
- 多文件资源包上传
- 模型 / 点云 / 倾斜摄影等角色区分
- Web 查看摘要与对象详情

### 统一平台

- 统一来源注册
- 统一资源目录
- 统一资源详情
- 按状态、类型、profile、预览能力筛选

### 权限与登录

- 内置测试用户与角色播种
- 登录、会话、上下文接口
- 前端菜单按角色裁剪
- 后端权限校验与范围控制
- `collection_owner` 责任范围过滤

### 测试与工程支撑

- 后端 `pytest` 测试
- 前端 `Playwright` 回归测试
- 参考资源导入与校验脚本
- 工作日志与阶段文档

## 技术栈

- 前端：React 18 + Vite + TypeScript + Ant Design
- 二维预览：Mirador
- 三维展示：`@google/model-viewer`
- 后端：FastAPI + SQLAlchemy + Pydantic
- 数据库：PostgreSQL
- 异步任务：Celery + Redis
- 图像服务：Cantaloupe IIIF Server
- 测试：pytest + Playwright

## 仓库结构

```text
mdams-prototype/
|- backend/        FastAPI API、服务层、脚本、测试
|- frontend/       React 前端、Playwright 测试、静态资源
|- docs/           项目正式文档主目录
|- cantaloupe/     Cantaloupe 构建与相关配置
|- reference/      参考资源包与导入样例
|- uploads/        本地开发默认挂载目录
|- docker-compose.yml
|- .env.example
```

## 快速开始

### 1. 准备环境变量

复制示例配置：

```powershell
Copy-Item .env.example .env
```

至少确认以下变量符合你的本机环境：

- `HOST_MUSEUM_PATH`
- `DATABASE_URL`
- `REDIS_URL`
- `API_PUBLIC_URL`
- `CANTALOUPE_PUBLIC_URL`

说明：

- `HOST_MUSEUM_PATH` 是宿主机目录，会被挂载到容器内 `/app/uploads`
- `API_PUBLIC_URL` 和 `CANTALOUPE_PUBLIC_URL` 必须是浏览器可访问的地址
- 如果你希望浏览器统一走前端代理，`CANTALOUPE_PUBLIC_URL` 本地建议使用 `http://localhost:3000/iiif/2`

### 2. 启动容器

```powershell
docker compose up -d --build
```

### 3. 打开系统

- 前端：`http://localhost:3000`
- 后端 API 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`
- 就绪检查：`http://localhost:8000/ready`
- Cantaloupe：`http://localhost:8182`

## 默认测试账号

系统启动后会自动播种一组测试用户，默认密码统一为：

```text
mdams123
```

常用账号包括：

- `system_admin`
- `resource_user`
- `collection_owner`
- `image_metadata_entry`
- `image_photographer`
- `image_editor`
- `image_ingest`
- `image_review`
- `image_manager`
- `three_d_operator`
- `application_review`

登录相关接口见后端 `auth` 路由，前端登录页会直接读取 `/api/auth/users` 列出可用账号。

## 常用开发命令

### 前端

```powershell
cd frontend
npm install
npm run dev
npm run build
npm run lint
npm run test
```

### 后端

```powershell
cd backend
python -m pytest
```

如需先在本机启动独立 PostgreSQL 测试库：
```powershell
.\manage_local_postgres.ps1 up
$env:TEST_DATABASE_URL="postgresql://meam:meam_secret@localhost:5432/meam_db_test"
python -m pytest backend\tests
```

## 当前主要后端模块

后端当前包含以下主要路由分区：

- `auth`
- `assets`
- `applications`
- `downloads`
- `health`
- `iiif`
- `ingest`
- `image-records`
- `platform`
- `three-d`
- `ai`

这意味着项目当前已经明确覆盖了登录权限、二维资产、图像记录、统一平台、三维资源、利用申请和 AI 辅助 Mirador 面板等模块，而不是仅仅停留在文件上传阶段。

## 文档入口

项目正式文档请从这里进入：

- 文档总入口：[docs/README.md](docs/README.md)
- 当前文档更新方案：[docs/01-总览/DOCUMENTATION_UPDATE_PLAN.md](docs/01-总览/DOCUMENTATION_UPDATE_PLAN.md)

建议优先阅读：

- 先从 `docs/README.md` 进入完整目录
- 当前这轮治理基线见 `docs/01-总览/DOCUMENTATION_UPDATE_PLAN.md`
- 部署、状态、权限、测试、日志等专题文档统一放在 `docs/` 内各分区

## 当前边界

当前仓库已经能支持演示和持续开发，但仍然属于原型阶段，主要边界包括：

- 权限模型已经建立，但还不是完整生产级身份治理
- 平台聚合已经可用，但来源接入和统一检索仍在持续完善
- 三维子系统已经有对象、版本和浏览链路，但规范化程度还可继续增强
- 长期保存、治理、审计、迁移与监控能力仍需后续补齐

## 与旧文档的关系

根目录里仍有一些历史 Markdown 文档，它们将逐步被 `docs/` 中的新结构替代。后续应以 `docs/` 为唯一正式文档主目录，以免出现重复入口和内容漂移。
