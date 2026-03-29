# MDAMS Prototype

MDAMS Prototype 是一个面向博物馆二维影像资源的原型系统，当前主线只聚焦一件事：把“上传入库 -> 元数据提取 -> IIIF 预览 -> 导出下载”这条链路做稳。

## 现在已经具备的能力

- 基础文件上传与资产列表
- SIP 风格入库与 fixity 校验
- PSB / BigTIFF 处理
- IIIF Manifest 生成
- Mirador 预览
- 原文件与 BagIt ZIP 下载
- Docker Compose 一键部署

## 技术栈

- 前端：React 18 + Vite + TypeScript + Ant Design + Mirador
- 后端：FastAPI + SQLAlchemy + PostgreSQL
- 异步任务：Celery + Redis
- 图像服务：Cantaloupe IIIF Server

## 快速开始

1. 复制 `.env.example` 为 `.env`，然后按你的机器修改 `HOST_MUSEUM_PATH`、`API_PUBLIC_URL`、`CANTALOUPE_PUBLIC_URL`。
2. 执行 `docker compose up -d --build`。
3. 打开 `http://localhost:3000` 访问前端，`http://localhost:8000/docs` 查看后端接口。

## 文档入口

- 部署与配置：`docs/SETUP_AND_DEPLOYMENT.md`
- 验收清单：`docs/ACCEPTANCE_CHECKLIST.md`
- 当前项目状态：`docs/PROJECT_STATUS.md`
- 下一阶段计划：`docs/NEXT_PHASE_PLAN.md`
- 统一元数据：`docs/UNIFIED_METADATA_REFERENCE.md`
- 对象 Profile 规则：`docs/OBJECT_PROFILE_RULES.md`
- 用户类型与权限矩阵：`docs/USER_ROLE_PERMISSION_MATRIX.md`
- 前端菜单可见矩阵：`docs/FRONTEND_MENU_VISIBILITY_MATRIX.md`
- 认证与 IIIF 整合方案：`docs/AUTH_AND_IIIF_INTEGRATION_PLAN.md`
- 测试策略：`docs/TESTING_STRATEGY.md`
- 工作日志：`docs/WORK_LOG.md`

## 当前判断

这个仓库现在更接近一个“稳定的二维影像底座”，而不是完整的 DAMS。后续工作会继续围绕配置收口、模块边界和资产详情契约推进。
