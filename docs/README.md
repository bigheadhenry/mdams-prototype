# 文档索引

当前项目正式文档统一放在 `docs/`。

当前入口文档以已提交代码中的稳定实现为事实来源；本地未提交的试验性改动不作为正式文档事实。

文档状态、入口优先级和历史/方案稿使用规则见：

- `DOCUMENT_GOVERNANCE.md`

## 目录结构

- `01-总览/`
  项目状态、下一阶段计划、验收、测试策略、工作日志
- `02-架构设计/`
  系统架构、平台适配器、API 路由、认证与 IIIF、三维子系统、统一来源定位
- `03-产品与流程/`
  角色权限、菜单矩阵、核心工作流、图像记录工作台、三维对象与平台视图
- `04-实施方案/`
  各阶段实施方案、路线图与归档方案，不直接等同于当前实现事实
- `05-部署与运维/`
  部署、环境变量、排障、脚本与批处理说明
- `06-参考资料/`
  元数据参考、样例、参考资源导入说明
- `07-图示/`
  架构图与图源文件
- `08-研究/`
  研究子项目材料

## 建议阅读顺序

如果你第一次进入这个仓库，建议按下面顺序看：

1. `01-总览/PROJECT_STATUS.md`
2. `05-部署与运维/SETUP_AND_DEPLOYMENT.md`
3. `02-架构设计/API_ROUTE_MAP.md`
4. `02-架构设计/PLATFORM_SOURCE_ADAPTERS.md`
5. `03-产品与流程/USER_ROLE_PERMISSION_MATRIX.md`
6. `03-产品与流程/WORKFLOW_GUIDE.md`
7. `02-架构设计/SYSTEM_ARCHITECTURE.md`
8. `01-总览/TESTING_STRATEGY.md`

## 当前核心入口

### 总览

- `DOCUMENT_GOVERNANCE.md`
- `01-总览/PROJECT_STATUS.md`
- `01-总览/NEXT_PHASE_PLAN.md`
- `01-总览/TESTING_STRATEGY.md`
- `01-总览/WORK_LOG.md`

### 架构

- `02-架构设计/SYSTEM_ARCHITECTURE.md`
- `02-架构设计/ARCHITECTURE.md`（快速概览）
- `02-架构设计/API_ROUTE_MAP.md`
- `02-架构设计/PLATFORM_SOURCE_ADAPTERS.md`
- `02-架构设计/UNIFIED_PLATFORM_SOURCE_LOCATOR_CONTRACT.md`
- `02-架构设计/THREE_D_SUBSYSTEM_ARCHITECTURE.md`
- `02-架构设计/AUTH_AND_IIIF_INTEGRATION_PLAN.md`

### 业务与权限

- `03-产品与流程/USER_ROLE_PERMISSION_MATRIX.md`
- `03-产品与流程/FRONTEND_MENU_VISIBILITY_MATRIX.md`
- `03-产品与流程/WORKFLOW_GUIDE.md`
- `03-产品与流程/IMAGE_RECORD_WORKBENCH_GUIDE.md`
- `03-产品与流程/THREE_D_OBJECT_MODEL_AND_PLATFORM_VIEW.md`
- `03-产品与流程/THREE_D_PRD_ALIGNMENT.md`
- `03-产品与流程/THREE_D_FORMAT_SUPPORT.md`

### 多模态与平台

- 二维影像入口：`02-架构设计/API_ROUTE_MAP.md`、`03-产品与流程/IMAGE_DERIVATIVE_POLICY.md`
- 三维资源入口：`02-架构设计/THREE_D_SUBSYSTEM_ARCHITECTURE.md`、`03-产品与流程/THREE_D_OBJECT_MODEL_AND_PLATFORM_VIEW.md`
- 统一平台入口：`02-架构设计/PLATFORM_SOURCE_ADAPTERS.md`
- AI / Mirador 入口：`04-实施方案/AI_MIRADOR_CONTROL_ROADMAP.md`

### 部署与运维

- `05-部署与运维/SETUP_AND_DEPLOYMENT.md`
- `05-部署与运维/ENVIRONMENT_VARIABLES.md`
- `05-部署与运维/TROUBLESHOOTING.md`
- `05-部署与运维/SCRIPT_AND_JOB_GUIDE.md`

### 参考资料

- `06-参考资料/UNIFIED_METADATA_REFERENCE.md`
- `06-参考资料/UNIFIED_METADATA_EXAMPLE.md`
- `06-参考资料/REFERENCE_RESOURCE_IMPORT_MAPPING.md`
- `06-参考资料/REFERENCE_DATASET_GUIDE.md`

## 历史与方案稿使用说明

- `04-实施方案/` 下多数文件是阶段方案或路线图，用于追溯设计意图。
- `05-部署与运维/DEPLOYMENT.md`、`INSTALL_DOCKER_WINDOWS.md` 是迁移提示，不作为当前部署入口。
- `05-部署与运维/MANUAL_IMAGE_GUIDE.md` 是特殊网络环境下的应急记录。
- 研究材料统一从 `08-研究/README（研究子项目说明）.md` 进入。
