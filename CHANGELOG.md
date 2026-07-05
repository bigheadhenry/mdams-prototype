# Changelog

所有显著变更均记录在此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

---

## [0.3.1] — 2026-06-23


### 安全

- **P0 安全补丁**（2026-07-04）：`POST /api/ingest/sip` 增加 `image.upload` 权限校验；`/api/video/*` 端点增加 `video.view` / `video.delete` 权限校验；申请审批状态机加固，`approve` / `reject` 仅允许从 `submitted` 状态操作，`export` 仅允许从 `approved` 状态操作；后端 `permissions.py` 与前端 `permissions.ts` 同步新增 video 权限；新增 P0 安全回归测试与前端权限 spec。

### 修复

- **安全后门关闭**：`X-MDAMS-User` Header 认证现受 `MDAMS_DEMO_MODE` 环境变量控制，默认关闭（`0`）。生产部署默认不再接受 Header 模拟用户，仅允许 Authorization（Bearer Token）和 mdams.session Cookie 两种认证方式。
- **Docker healthcheck**：为 db / redis / cantaloupe 三个服务添加 Docker healthcheck，backend 和 celery_worker 的 depends_on 改为 `condition: service_healthy`，启动时等待上游服务就绪
- **部署脚本改进**：`deploy.sh` 将盲等 `sleep 10` 替换为 active polling（最多 90s 轮询所有服务健康状态）
- **CANTALOUPE_INTERNAL_URL 默认值修正**：`.env.example` 中默认值改为 `http://cantaloupe:8182/iiif/2`，与 Docker Compose 内部网络一致
- **Alembic 迁移系统**：初始化 Alembic、生成初始 migration（捕获全部 15 张表）、替换 `_ensure_sqlite_schema_compatibility()`、容器启动自动执行 `alembic upgrade head`、后备路径保留 `Base.metadata.create_all()`
- **根目录遗留文档归档**：7 个根级文档（ARCHITECTURE/SYSTEM_ARCHITECTURE/DEPLOYMENT/WORKFLOW/CANTALOUPE/MANUAL_IMAGE/INSTALL_DOCKER）移入 `docs/00-归档/`，更新 `DOCUMENT_GOVERNANCE.md` 混淆说明和 `DOCUMENT_REGISTRY.md` 记录
- **影像利用申请交付包增加授权说明**：交付包新增 `授权说明.md`，包含授权编号、获批用途、使用范围、使用限制、署名要求与版权声明；`application.json` 追加 `reviewed_at`；关联测试扩展验证交付包内容完整性
- **审批与导出操作追加操作人记录**：`Application` 模型新增 `reviewed_by_user_id` 和 `exported_by_user_id` 字段（FK → users），审批/拒绝/导出 API 写入当前操作用户，响应 schema 返回 `reviewed_by` / `exported_by` 显示名；Alembic 迁移 `c7f0f77cf2a2`；测试新增 `test_reject_application` + `current_user` 参数覆盖
- **审批审计日志系统**：新增 `ApplicationAuditLog` 模型（独立审计表），创建/审批/拒绝/导出 4 个操作点写入审计日志；Alembic 迁移 `e4a8b3c1d2f0`；所有测试验证审计记录条数和内容
### 2026-06-25 - 统一检索平台优化 P0+P1
- **P0 多选批量加车**: PlatformDirectory 卡片视图新增左上角 Checkbox + 顶部批量操作栏（已选 N 项 + 批量加入申请车）
- **P1 排序控件**: GET /api/platform/resources 新增 sort_by(updated_at/title/status) + sort_order(asc/desc) 参数
- **P1 搜索订阅系统**: 新增 SearchSubscription 模型 + subscriptions 路由（CREATE/LIST/DELETE/CHECK）；Alembic 迁移 f5a6b7c8d9e0
- **P1 资源详情增强**: UnifiedResourceDetail 新增 Collapse 分组展示 4 层元数据（Core/Management/Technical/Profile）
- **Bug 修复**: cart.py threading.Lock → RLock（递归锁死锁问题）
- **安全增强**: 购物车上限检查（413）、搜索订阅参数白名单校验
- **申请车批量导入 + 文物号查询**：新增 `POST /api/cart/import` 批量导入端点和 `GET /api/cart/lookup` 文物号查询端点；前端 `ImportDialog` 组件（三 Tab：查文物号 / 粘贴文本 / 上传文件），支持智能解析决策树：有图片ID精确匹配 / 只有文物号展开多图 + 筛选勾选
- **粘贴/文件导入支持文物号展开多图**：扩展 `ImportDialog`（1011→1449 行），新增 `ExpandSelectionModal` 子组件，粘贴文本和上传文件 Tab 中的"展开多图"行现在会批量调 lookup API 查询关联影像，弹出多图选择界面供用户勾选后再导入

### 新增

- 新增 `MDAMS_DEMO_MODE` 环境变量，控制 `X-MDAMS-User` 遗留头认证是否可用

### 内部

- 测试 conftest 自动设置 `MDAMS_DEMO_MODE=1`，确保现有测试不受影响

---

## [0.3.0] — 2026-05-27

### 新增

- **标准演示交付流**：端到端演示流程可验证，涵盖资源查看→申请→审批→交付导出
- **三维上传验证强化**：文件类型、格式约束、边界检查加固
- **三维子系统代码模块化**：将三维服务从混用状态拆分为独立职责的服务模块

### 变更

- **统一资源目录与详情可视化优化**（信息效率导向）：
  - 卡片 Meta 三层化、排序下拉、筛选 chips、批量操作入口
  - 检索概览栏三段重组 + 可点击切换 Tab + 可折叠
  - 详情页 Hero 真双栏、操作分主次、锚点导航、生命周期 Timeline
  - 三维源详情 Drawer 拆独立组件 + 5 Tab + 底部固定栏
  - 主导航 Sider 默认收起
  - 目录上下文持久化（进详情后返回还原 Tab/页码/排序/筛选）
- **资源处理安全审计**：
  - 文件名 basename 归一化防路径穿越
  - CORS 从通配改为可配置来源列表
  - 认证密码哈希升级为带随机盐的 PBKDF2，兼容旧哈希自动迁移
  - 二维下载与 BagIt 导出补充认证与可见范围校验
  - 三维下载增加资源目录边界检查和归档文件名清洗
  - BagIt tag files 固定 Windows 下换行输出
  - 前端依赖 `npm audit` 修复（17 漏洞降至 4 中危）

### 内部

- 三维详情、字典、预览服务分离为独立文件

---

## [0.2.0] — 2026-05-01

### 新增

- **人脸识别链路**：Celery 异步任务 + 本地/远程/自动 provider 切换，业务活动类影像记录自动检测并回写 `main_person`
- **跨子系统最小事件边界正式化**：按二维资产、图像记录、三维对象、访问/导出、申请交付五个子域划清事件边界，明确当前不引入统一事件表
- **AI 操控 Mirador 工具调用标准化**：新增 `tool_call` 结构与 MCP 化路线图

### 变更

- 统一平台详情从复合标识符过渡到 `source_system/source_id` 路径
- Cantaloupe 调整为后端内部访问 + 前端代理访问分离
- 二维 profile 必填字段集中到 `metadata_layers.py`，校验与参考导入共用同一规则
- 输出契约测试覆盖 IIIF/BagIt 基本形状
- 研究材料补全（实施边界清单、关键讨论问题、RepoWiki）

### 修复

- 人脸识别 Docker 环境变量传递：`docker-compose.yml` 显式传给 `backend` 和 `celery_worker`
- 人脸识别运行时目录从仓库根目录移到 `backend/runtime/` 下

---

## [0.1.0] — 2026-04-12

### 新增

- **图像记录工作流 Phase 1**：创建/编辑/提交/退回/待上传池，录入 + 摄影分离角色
- **入库单 (Ingest Sheet)** 管理：批次创建、行号、批次状态流转
- **利用申请交付导出**：BagIt 格式交付包，IIIF + 原文件两种 variant
- **三维数据管理子系统**：三维对象/版本/多角色文件包（模型/点云/倾斜摄影）
- **三维 Web 展示链路**：Web 查看摘要、对象详情、文件级预览
- **统一平台来源注册表**：`PlatformSourceAdapter` + `PlatformSourceRegistry`
- **统一资源目录**：跨来源聚合、筛选、统一详情
- **视频资源接入**：统一平台 video 来源适配器
- **登录与权限框架**：11 角色、RBAC、collection_scope 范围控制
- **前端菜单按角色裁剪**
- **Mirador AI 面板**：后端计划 + 前端执行器

### 变更

- 项目命名从 MEAM 过渡到 MDAMS
- 文档体系重建：从根目录散落文档 → `docs/` 分层结构
- 平台来源改为注册式适配器，后续新增来源只需实现适配器

### 修复

- Cantaloupe 构建从 Docker Hub 改为本地构建，解决网络不可用问题
- Python 3.13 兼容性调整
- N100 低内存环境的 VIPS/Java 参数优化

### 内部

- 测试分层：`unit` / `integration` / `smoke` / `contract` 标记体系
- `memory/` 项目记忆层建立：决策记录、实验日志、原型设计
- Playwright 回归测试：菜单导航、统一平台、图像记录

---

## [0.0.1] — 2026-01-14~2026-03-08

### 新增

- 初始 FastAPI + React 项目脚手架
- 基础二维影像资产上传/列表/详情
- IIIF Manifest 生成 + Mirador 预览
- Cantaloupe IIIF Server 集成
- PSB/TIFF 自动转换与 BagIt 下载
- Docker Compose 编排：backend/frontend/cantaloupe/db
- 下一阶段计划与项目状态文档

### 内部

- `.env.example` 配置模板
- Git push-to-deploy 自动部署机制
- 参考资源导入与校验脚本

---

[0.3.0]: https://github.com/sunjing/mdams-prototype/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/sunjing/mdams-prototype/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/sunjing/mdams-prototype/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/sunjing/mdams-prototype/releases/tag/v0.0.1
