# 文档治理与入口说明

- 最后核对日期：2026-05-17
- 事实基线：以已提交代码中的稳定实现为准，不纳入当前工作区未提交试验改动。

## 1. 文档状态标签

为避免历史方案、研究材料和当前事实入口混用，`docs/` 下文档按以下状态理解：

| 状态 | 含义 | 使用方式 |
|---|---|---|
| 当前事实入口 | 与当前稳定实现对齐，可作为开发、部署、验收和对外说明依据 | 优先阅读和引用 |
| 专题说明 | 围绕某个子系统、流程、标准或样例展开 | 在处理对应专题时阅读 |
| 研究材料 | 服务论文、研究论证、标准映射和方法整理 | 用于研究写作，不直接替代工程事实 |
| 实施方案 / 路线图 | 阶段计划、Phase 方案或下一步建议 | 用于追溯设计意图和规划，不直接当作已实现事实 |
| 历史 / 已迁移 / 应急 | 旧入口、已迁移说明或特定环境排障记录 | 仅在追溯历史或处理相同特殊问题时使用 |

## 2. 当前事实入口

| 主题 | 当前入口 |
|---|---|
| 项目状态 | `01-总览/PROJECT_STATUS.md` |
| 系统架构 | `02-架构设计/SYSTEM_ARCHITECTURE.md` |
| API 路由 | `02-架构设计/API_ROUTE_MAP.md` |
| 统一平台来源 | `02-架构设计/PLATFORM_SOURCE_ADAPTERS.md` |
| 统一来源定位契约 | `02-架构设计/UNIFIED_PLATFORM_SOURCE_LOCATOR_CONTRACT.md` |
| 认证与 IIIF | `02-架构设计/AUTH_AND_IIIF_INTEGRATION_PLAN.md` |
| 核心工作流 | `03-产品与流程/WORKFLOW_GUIDE.md` |
| 角色权限 | `03-产品与流程/USER_ROLE_PERMISSION_MATRIX.md` |
| 前端菜单 | `03-产品与流程/FRONTEND_MENU_VISIBILITY_MATRIX.md` |
| 部署与配置 | `05-部署与运维/SETUP_AND_DEPLOYMENT.md` |
| 环境变量 | `05-部署与运维/ENVIRONMENT_VARIABLES.md` |
| 排障 | `05-部署与运维/TROUBLESHOOTING.md` |
| 测试策略 | `01-总览/TESTING_STRATEGY.md` |

## 3. 专题说明入口

| 专题 | 推荐入口 |
|---|---|
| 图像记录工作台 | `03-产品与流程/IMAGE_RECORD_WORKBENCH_GUIDE.md` |
| 二维衍生与 IIIF access | `03-产品与流程/IMAGE_DERIVATIVE_POLICY.md`、`08-研究/IIIF清单配置说明（IIIF_MANIFEST_PROFILE）.md` |
| 三维子系统 | `02-架构设计/THREE_D_SUBSYSTEM_ARCHITECTURE.md`、`03-产品与流程/THREE_D_OBJECT_MODEL_AND_PLATFORM_VIEW.md` |
| 视频来源 | `02-架构设计/PLATFORM_SOURCE_ADAPTERS.md`、`02-架构设计/API_ROUTE_MAP.md` |
| AI / Mirador | `04-实施方案/AI_MIRADOR_CONTROL_ROADMAP.md` |
| 人脸识别 | `08-研究/当前项目事实（CURRENT_PROJECT_FACTS）.md`、`01-总览/TESTING_STRATEGY.md` |
| 脚本与参考数据 | `05-部署与运维/SCRIPT_AND_JOB_GUIDE.md`、`06-参考资料/REFERENCE_DATASET_GUIDE.md` |

## 4. 研究材料入口

研究线的入口是：

- `08-研究/README（研究子项目说明）.md`
- `08-研究/当前项目事实（CURRENT_PROJECT_FACTS）.md`
- `08-研究/论文写作摘要（PAPER_READY_SUMMARY）.md`

研究材料可以引用当前事实入口，但不应反过来替代部署、API、权限和流程文档。

## 5. 容易混淆的文档关系

| 容易混淆项 | 当前解释 |
|---|---|
| `ARCHITECTURE.md` vs `SYSTEM_ARCHITECTURE.md` | `ARCHITECTURE.md` 是快速概览；`SYSTEM_ARCHITECTURE.md` 是当前系统架构事实入口 |
| `DEPLOYMENT.md` vs `SETUP_AND_DEPLOYMENT.md` | `DEPLOYMENT.md` 只是迁移提示；当前部署以 `SETUP_AND_DEPLOYMENT.md` 为准 |
| `INSTALL_DOCKER_WINDOWS.md` | 已迁移提示，首次启动看 `SETUP_AND_DEPLOYMENT.md` |
| `MANUAL_IMAGE_GUIDE.md` | 特定网络环境下的应急记录，不是常规部署流程 |
| `04-实施方案/*_PLAN.md` | 阶段方案和设计意图，不能直接当作当前实现事实 |
| `PROJECT_DIRECTION_AGGREGATION_ARCHITECTURE.md` | 中长期方向说明，当前 API / 平台事实以 `API_ROUTE_MAP.md` 和 `PLATFORM_SOURCE_ADAPTERS.md` 为准 |

## 6. 更新规则

1. 当前事实变化时，先更新当前事实入口。
2. 专题说明只能补充当前事实，不应和入口文档冲突。
3. 研究材料必须标清“已实现 / 部分对齐 / 概念借鉴 / 未来扩展”。
4. 实施方案完成后不删除，改为归档或在入口文档中说明其历史状态。
5. 新增来源或权限时，同步更新 API 路由、平台来源、角色权限和菜单矩阵。
