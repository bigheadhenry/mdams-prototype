# MDAMS Prototype

MDAMS Prototype 是一个面向博物馆馆内业务的数字资源管理原型，当前重点已经从“单一二维影像 PoC”推进到“二维影像子系统 + 三维数据管理子系统 + 统一平台入口 + 利用申请流程 + 登录权限框架”的组合形态。

这个仓库的目标不是先堆出一个大而全的 DAMS，而是先把几条关键链路做实：

- 二维资源入库、元数据、IIIF 预览、下载与利用申请
- 三维资源对象、版本、Web 展示版、对象级聚合管理
- 统一资源目录、统一详情与来源接入适配
- 馆内用户登录、角色、权限与资源范围控制
- 可持续的测试分层与工作日志

## 当前已实现的能力

### 二维影像子系统

- 基础文件上传与资源列表
- SIP 风格入库与 fixity 校验
- PSB / BigTIFF 处理
- IIIF Manifest 生成
- Mirador 预览
- 原文件与 BagIt ZIP 下载
- 申请车、申请单、审批与交付包导出
- 资源可见范围与藏品责任范围控制

### 三维数据管理子系统

- 三维资源对象与多文件资源包管理
- 模型、点云、倾斜摄影图像分角色保存
- 版本号与 Web 展示状态管理
- 对象级聚合视图与对象级概览
- 三维 Web 查看器
- 藏品对象关联与生产链路记录
- 长期保存状态与展示状态分离

### 统一平台

- 统一资源目录
- 统一详情页
- 来源注册表与适配器
- 二维 / 三维来源接入
- 按 profile、状态、资源类型、可见范围筛选

### 权限与登录

- 用户、角色、会话、登录上下文
- 前端菜单按角色可见
- 后端关键接口按权限保护
- `RBAC + scope` 权限模型
- `collection_owner` 藏品责任范围过滤

### 测试与日志

- 后端 pytest 分层
- 前端 Playwright 登录态回归
- 三维元数据字典契约测试
- 三维生产链路测试
- 工作日志机制

## 技术栈

- 前端：React 18 + Vite + TypeScript + Ant Design + Mirador + model-viewer
- 后端：FastAPI + SQLAlchemy + Pydantic
- 数据库：PostgreSQL
- 异步任务：Celery + Redis
- 图像服务：Cantaloupe IIIF Server
- 三维预览：`@google/model-viewer`
- 测试：pytest + Playwright

## 快速开始

### 1. 准备环境

复制 `.env.example` 为 `.env`，并根据你的本机环境调整以下配置：

- `HOST_MUSEUM_PATH`
- `UPLOAD_DIR`
- `DATABASE_URL`
- `REDIS_URL`
- `API_PUBLIC_URL`
- `CANTALOUPE_PUBLIC_URL`

> 如果你在 Windows 上使用中文路径或 NAS 路径，建议确认 `.env` 以 UTF-8 保存。

### 2. 启动服务

```bash
docker compose up -d --build
```

### 3. 打开系统

- 前端：`http://localhost:3000`
- 后端 API：`http://localhost:8000`
- 接口文档：`http://localhost:8000/docs`
- Cantaloupe：`http://localhost:8182`

## 常用开发命令

### 前端

```bash
cd frontend
npm install
npm run dev
npm run build
npm run lint
npm run test
```

### 后端

```bash
cd backend
python -m pytest
python -m py_compile app/*.py
```

## 主要文档

- 部署与配置：[`docs/SETUP_AND_DEPLOYMENT.md`](docs/SETUP_AND_DEPLOYMENT.md)
- 验收清单：[`docs/ACCEPTANCE_CHECKLIST.md`](docs/ACCEPTANCE_CHECKLIST.md)
- 项目状态：[`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md)
- 下一阶段计划：[`docs/NEXT_PHASE_PLAN.md`](docs/NEXT_PHASE_PLAN.md)
- 统一元数据参考：[`docs/UNIFIED_METADATA_REFERENCE.md`](docs/UNIFIED_METADATA_REFERENCE.md)
- 对象 Profile 规则：[`docs/OBJECT_PROFILE_RULES.md`](docs/OBJECT_PROFILE_RULES.md)
- 用户类型与权限矩阵：[`docs/USER_ROLE_PERMISSION_MATRIX.md`](docs/USER_ROLE_PERMISSION_MATRIX.md)
- 前端菜单可见矩阵：[`docs/FRONTEND_MENU_VISIBILITY_MATRIX.md`](docs/FRONTEND_MENU_VISIBILITY_MATRIX.md)
- 认证与 IIIF 整合方案：[`docs/AUTH_AND_IIIF_INTEGRATION_PLAN.md`](docs/AUTH_AND_IIIF_INTEGRATION_PLAN.md)
- 测试策略：[`docs/TESTING_STRATEGY.md`](docs/TESTING_STRATEGY.md)
- 三维 PRD 对照：[`docs/THREE_D_PRD_ALIGNMENT.md`](docs/THREE_D_PRD_ALIGNMENT.md)
- 工作日志：[`docs/WORK_LOG.md`](docs/WORK_LOG.md)

## 当前判断

这个仓库现在更接近一个“稳定的馆内数字资源底座”，而不是完整生产级 DAMS。已经验证的部分包括：

- 二维影像资源管理与 IIIF 预览
- 三维数字对象管理与浏览器查看
- 统一平台目录与统一详情
- 馆内角色权限与资源范围控制
- 资源申请与交付闭环

后续工作会继续围绕这几个方向推进：

- 继续完善统一平台层
- 继续完善二维 / 三维子系统
- 继续补齐权限、治理与长期保存能力
- 继续增强测试分层与回归质量

## 备注

- 本仓库包含本地测试资源、样例模型和开发脚本。
- 运行时生成物、数据库文件和测试报告不应提交到仓库。
- 项目变更会持续记录在 `docs/WORK_LOG.md`。