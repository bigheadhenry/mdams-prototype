# MDAMS 文档更新方案

## 1. 目标

这份方案用于对当前仓库的所有项目文档做一次系统更新，解决以下问题：

- 文档入口分散，根目录与 `docs/` 并存且内容重复
- 目录结构已经调整，但根 README 仍然指向旧路径
- 部分历史文档存在编码异常、术语不统一、描述与当前代码不一致的问题
- 若干已经实现的模块缺少对应说明文档
- 实施方案、正式说明、研究材料、运维记录目前混放，边界不够清晰

本方案的目标不是简单“整理文件夹”，而是建立一套可持续维护的项目文档体系，使文档能够真实反映当前代码、配置、运行方式和开发边界。

## 2. 本次复盘依据

本方案基于以下实际项目内容整理：

- 根目录入口与配置：`README.md`、`.env.example`、`docker-compose.yml`、`deploy.sh`
- 后端主入口与模块：`backend/app/main.py`、`backend/app/routers/`、`backend/app/services/`
- 后端脚本：`backend/scripts/`
- 前端主入口与页面组件：`frontend/src/App.tsx`、`frontend/src/components/`
- 测试体系：`backend/tests/`、`frontend/tests/`
- 现有文档目录：`docs/`
- 参考样例目录：`reference/`

## 3. 当前主要问题

### 3.1 导航与入口问题

- 根 `README.md` 仍然引用旧的 `docs/*.md` 路径，当前已经全部失效
- 根目录仍保留一批历史 Markdown 文档，与 `docs/` 中的新文档重复
- `docs/README.md` 已经成为目录入口，但尚未与根 README 建立一致的导航关系

### 3.2 内容重复与分层不清

- 根目录的 `ARCHITECTURE.md`、`DEPLOYMENT.md`、`SYSTEM_ARCHITECTURE.md`、`WORKFLOW_GUIDE.md` 与 `docs/` 下同主题文档高度重叠
- `docs/02-架构设计/` 中存在“总体架构”和“系统架构”两类文档，边界需要重新划定
- `docs/01-总览/PROJECT_STATUS.md`、`NEXT_PHASE_PLAN.md`、`WORK_LOG.md` 都在描述项目现状，但职责不同步
- `docs/04-实施方案/` 既有仍在生效的实施基线，也有已经归档的历史计划，目前缺少状态标识

### 3.3 与实际代码不一致

- 根目录部分历史文档仍在描述旧的 `MEAM` 命名、旧部署方式或不存在的组件
- 根目录旧部署脚本和工作流文档仍提到 `FileBrowser` 等当前 `docker-compose.yml` 中不存在的服务
- 根目录旧工作流文档以 `git push production master` 为中心，但当前仓库也有本地容器启动与常规 GitHub 协作路径，需要重新说明适用场景
- 当前后端已包含 `auth`、`applications`、`image_records`、`platform`、`three_d`、`ai_mirador` 等模块，但文档覆盖仍不完整

### 3.4 编码与格式问题

- 多个历史文档在终端输出中出现中文乱码，说明编码一致性需要专项处理
- 中英文术语混用，如 `MEAM` / `MDAMS`、`2D Image` / `二维资源`、`resource` / `asset` / `object`，需要统一词汇表
- 目录重组后，根 README 尚未同步更新，局部引用与命名风格也不完全一致

### 3.5 缺失文档

- 缺少一份面向当前实现的 API 路由总览
- 缺少一份环境变量字典
- 缺少一份后端脚本说明
- 缺少一份图像记录工作台说明
- 缺少一份统一平台接入与来源适配器说明
- 缺少一份三维子系统的数据包、状态和对象模型说明
- 缺少一份测试矩阵与运行方式说明
- 缺少一份参考样例数据和 `reference/` 目录用途说明

## 4. 目标文档体系

建议将文档体系稳定为如下结构：

- 根目录只保留一个总入口 `README.md`
- 根目录历史同主题文档全部迁移为“归档入口”或直接删除
- `docs/` 作为唯一项目文档主目录
- `docs/01-总览/` 负责入口、状态、计划、验收、日志
- `docs/02-架构设计/` 负责系统、数据、权限、平台架构
- `docs/03-产品与流程/` 负责角色、页面、业务规则、用户流程
- `docs/04-实施方案/` 负责仍有执行价值的实施基线，历史方案明确标记为归档
- `docs/05-部署与运维/` 负责安装、部署、环境变量、排障、运维脚本
- `docs/06-参考资料/` 负责字段参考、映射关系、示例
- `docs/07-图示/` 负责可视图与图源
- `docs/08-研究/` 继续保留研究材料，但与项目正式文档清晰隔离

## 5. 既有文档处理策略

### 5.1 根目录文档

| 文件 | 当前判断 | 处理建议 | 优先级 |
| :--- | :--- | :--- | :--- |
| `README.md` | 总入口有效，但链接全部失效，内容需与新结构同步 | 重写并作为唯一入口，修复全部链接，增加文档导航与范围声明 | P0 |
| `ARCHITECTURE.md` | 历史旧稿，内容乱码且与当前实现不一致 | 删除正文，改为一句话归档指向 `docs/02-架构设计/ARCHITECTURE.md` 或直接删除 | P0 |
| `SYSTEM_ARCHITECTURE.md` | 历史旧稿，内容乱码且与当前实现不一致 | 同上，归档或删除 | P0 |
| `DEPLOYMENT.md` | 历史旧稿，与当前部署入口重复 | 改为归档跳转页或删除 | P0 |
| `CANTALOUPE_DEPLOY_NOTES.md` | 与 `docs/05-部署与运维/` 重复 | 改为跳转页或删除 | P1 |
| `INSTALL_DOCKER_WINDOWS.md` | 与 `docs/05-部署与运维/` 重复 | 改为跳转页或删除 | P1 |
| `MANUAL_IMAGE_GUIDE.md` | 与 `docs/05-部署与运维/` 重复 | 改为跳转页或删除 | P1 |
| `WORKFLOW_GUIDE.md` | 历史工作流说明，含旧部署方式 | 改为跳转页或删除 | P0 |

处理原则：

- 根目录不再保留多份“正文级”专题文档
- 若用户仍可能从旧路径打开，则保留短跳转页 1 个版本即可
- 新增文档只进入 `docs/`

### 5.2 `docs/01-总览/`

| 文件 | 当前判断 | 处理建议 | 优先级 |
| :--- | :--- | :--- | :--- |
| `ACCEPTANCE_CHECKLIST.md` | 有价值 | 按当前功能链路重排为“启动验收 / 功能验收 / 演示验收” | P1 |
| `AI_DEVELOPMENT_GUIDE.md` | 价值存在，但编码异常明显 | 重写为开发者快速上手文档，弱化“AI 专用”命名 | P1 |
| `DEMO_FLOW.md` | 有价值 | 与验收清单对齐，区分“演示路径”和“操作验证” | P1 |
| `NEXT_PHASE_PLAN.md` | 有价值，但偏战略 | 与 `PROJECT_STATUS.md` 拉开边界，只保留阶段目标与优先级 | P1 |
| `PROJECT_STATUS.md` | 有价值 | 加入“最后核对日期”和“已验证范围” | P0 |
| `TESTING_STRATEGY.md` | 有价值但过薄 | 扩展为测试矩阵，覆盖 pytest / Playwright / smoke / fixture | P0 |
| `WORK_LOG.md` | 持续使用中 | 保留，增加记录模板和分节索引规则 | P1 |
| `DOCUMENTATION_UPDATE_PLAN.md` | 新增 | 作为当前这轮整理基线 | P0 |

### 5.3 `docs/02-架构设计/`

| 文件 | 当前判断 | 处理建议 | 优先级 |
| :--- | :--- | :--- | :--- |
| `ARCHITECTURE.md` | 应保留为总览 | 写成一页式高层架构总览 | P0 |
| `SYSTEM_ARCHITECTURE.md` | 与上存在重叠 | 改成运行时组件、部署拓扑、数据流的详细版 | P1 |
| `DATA_INGEST_ARCHITECTURE.md` | 有价值 | 更新为当前 2D 与 3D 的入库差异说明 | P1 |
| `AUTH_AND_IIIF_INTEGRATION_PLAN.md` | 有价值 | 从“方案”改成“当前实现与边界说明”，补权限链路图 | P1 |
| `PROJECT_DIRECTION_AGGREGATION_ARCHITECTURE.md` | 偏大而散 | 拆成“统一平台架构说明”和“未来方向说明”，避免单篇过重 | P2 |

建议新增：

- `API_ROUTE_MAP.md`
- `PLATFORM_SOURCE_ADAPTERS.md`
- `THREE_D_SUBSYSTEM_ARCHITECTURE.md`

### 5.4 `docs/03-产品与流程/`

| 文件 | 当前判断 | 处理建议 | 优先级 |
| :--- | :--- | :--- | :--- |
| `USER_ROLE_PERMISSION_MATRIX.md` | 重要，但编码异常明显 | 重写为角色、权限、范围控制总表 | P0 |
| `FRONTEND_MENU_VISIBILITY_MATRIX.md` | 重要，但依赖上一份 | 与权限矩阵一起重写，菜单与角色保持一一对应 | P0 |
| `ROLE_PAGE_ACTION_MATRIX.md` | 有价值 | 调整为“角色 -> 页面 -> 操作”矩阵，避免与菜单矩阵重复 | P1 |
| `WORKFLOW_GUIDE.md` | 有价值但偏抽象 | 重写为用户流程总览，链接到图像记录、申请流程等子文档 | P1 |
| `IMAGE_DERIVATIVE_POLICY.md` | 与代码贴合较好 | 补上与 `derivative_policy.py`、`iiif_access.py` 的对应关系 | P1 |
| `OBJECT_PROFILE_RULES.md` | 有价值 | 与参考映射文档联动，明确 profile 来源 | P2 |
| `THREE_D_PRD_ALIGNMENT.md` | 有价值 | 明确哪些项已实现、部分实现、未实现 | P2 |

建议新增：

- `IMAGE_RECORD_WORKBENCH_GUIDE.md`
- `APPLICATION_REVIEW_FLOW.md`
- `UNIFIED_RESOURCE_DIRECTORY_GUIDE.md`

### 5.5 `docs/04-实施方案/`

| 文件 | 当前判断 | 处理建议 | 优先级 |
| :--- | :--- | :--- | :--- |
| `IMAGE_RECORD_ROLE_SPLIT_PHASE1_PLAN.md` | 仍贴合当前代码 | 保留，并标记“已作为实现基线” | P1 |
| `IMAGE_RECORD_MATCHING_PHASE1_PLAN.md` | 同上 | 保留，并补当前已落地程度 | P1 |
| `IMAGE_RECORD_VALIDATION_PHASE1_PLAN.md` | 同上 | 保留，并补当前验证实现对应点 | P1 |
| `IMAGE_IIIF_ACCESS_FORMAT_PHASE1_PLAN.md` | 同上 | 保留，并补当前状态 | P1 |
| `OBJECT_DETAIL_IMPLEMENTATION_PLAN.md` | 需判断是否仍生效 | 若已基本落地则转入归档说明 | P2 |
| `OBJECT_DETAIL_PHASE2_PLAN.md` | 历史方案 | 标记为归档并写明未完成项 | P2 |
| `OBJECT_DETAIL_PHASE3_PLAN.md` | 历史方案 | 标记为归档并写明未完成项 | P2 |
| `CONFIG_REFACTOR_PLAN.md` | 已归档 | 保留短说明即可 | P3 |

建议规则：

- 每个实施方案头部增加 `状态`、`适用范围`、`是否已落地`、`关联代码` 四项
- 已落地但仍有参考价值的方案，移入“已采纳基线”
- 已失效的方案，保留最短归档说明，不保留长正文

### 5.6 `docs/05-部署与运维/`

| 文件 | 当前判断 | 处理建议 | 优先级 |
| :--- | :--- | :--- | :--- |
| `SETUP_AND_DEPLOYMENT.md` | 当前主入口，有效 | 扩展为唯一部署手册，覆盖本地开发、服务器部署、NAS 挂载 | P0 |
| `TROUBLESHOOTING.md` | 有价值 | 扩展为按症状分节的排障手册 | P1 |
| `CANTALOUPE_DEPLOY_NOTES.md` | 有价值 | 改成 Cantaloupe 专题说明，去掉历史噪音 | P1 |
| `GIT_DEPLOY_GUIDE.md` | 仍有价值 | 明确适用场景，只描述 push-to-deploy 路径，不混入日常开发 | P1 |
| `DEPLOYMENT.md` | 已迁移跳转页 | 保留极简跳转或删除 | P2 |
| `INSTALL_DOCKER_WINDOWS.md` | 已迁移跳转页 | 保留极简跳转或删除 | P2 |
| `MANUAL_IMAGE_GUIDE.md` | 特殊场景文档 | 重写为“镜像获取受限场景处理”并注明适用条件 | P2 |

建议新增：

- `ENVIRONMENT_VARIABLES.md`
- `OPERATIONS_RUNBOOK.md`
- `SCRIPT_AND_JOB_GUIDE.md`

### 5.7 `docs/06-参考资料/`

| 文件 | 当前判断 | 处理建议 | 优先级 |
| :--- | :--- | :--- | :--- |
| `UNIFIED_METADATA_REFERENCE.md` | 重要 | 与后端 `metadata_layers.py`、平台目录接口保持一致 | P1 |
| `UNIFIED_METADATA_EXAMPLE.md` | 重要 | 用真实字段样例替换纯概念样例 | P1 |
| `REFERENCE_RESOURCE_IMPORT_MAPPING.md` | 重要 | 与 `reference_import.py` 和脚本说明联动 | P1 |

建议新增：

- `REFERENCE_DATASET_GUIDE.md`
- `PROFILE_FIELD_DICTIONARY.md`

### 5.8 `docs/07-图示/`

| 文件 | 当前判断 | 处理建议 | 优先级 |
| :--- | :--- | :--- | :--- |
| `MDAMS-Architecture.drawio` | 有价值 | 与最新架构文档同步命名和图例 | P2 |
| `MDAMS-Deployment.mmd` | 有价值 | 按当前 compose 服务更新 | P2 |
| `MDAMS-Subsystems.mmd` | 有价值 | 按当前 2D / 3D / platform / auth 模块更新 | P2 |

建议新增：

- 图示统一导出 PNG
- 图示索引页 `README.md`

### 5.9 `docs/08-研究/`

当前目录整体保留，但需要单独治理：

- 统一编码为 UTF-8
- 补一份研究目录索引
- 每份材料增加“研究用途”和“是否直接服务当前项目文档”的标识
- 避免研究材料与正式产品文档互相引用过深

优先级建议为 P3，除非近期要同步写论文或汇报材料。

## 6. 需要新增的核心文档

建议补齐以下缺失文档：

1. `docs/02-架构设计/API_ROUTE_MAP.md`
   说明后端当前路由分区：`auth`、`assets`、`applications`、`downloads`、`health`、`iiif`、`ingest`、`image-records`、`platform`、`three-d`、`ai`

2. `docs/05-部署与运维/ENVIRONMENT_VARIABLES.md`
   解释 `.env.example` 中全部变量、默认值、使用场景和典型误配

3. `docs/05-部署与运维/SCRIPT_AND_JOB_GUIDE.md`
   覆盖 `backend/scripts/` 中的数据导入、回填、校验脚本

4. `docs/03-产品与流程/IMAGE_RECORD_WORKBENCH_GUIDE.md`
   解释元数据录入人员与摄影上传人员的工作台差异

5. `docs/02-架构设计/PLATFORM_SOURCE_ADAPTERS.md`
   解释统一平台来源注册表、适配器、来源字段映射

6. `docs/02-架构设计/THREE_D_SUBSYSTEM_ARCHITECTURE.md`
   说明三维对象、版本、展示版、详情页、查看器与生产链路

7. `docs/01-总览/TEST_MATRIX.md` 或扩展现有 `TESTING_STRATEGY.md`
   明确 pytest、Playwright、smoke、fixture 的覆盖范围与执行命令

8. `docs/06-参考资料/REFERENCE_DATASET_GUIDE.md`
   说明 `reference/` 目录中的参考资源包、Excel、图片样例分别用于什么

## 7. 执行顺序

### P0：先修入口与真实性

- 重写根 `README.md`
- 修复全部 Markdown 坏链
- 处理根目录重复文档
- 重写权限矩阵与菜单矩阵
- 重写项目状态文档
- 扩展部署主入口
- 扩展测试策略

### P1：补齐当前已实现模块的说明

- API 路由总览
- 环境变量字典
- 图像记录工作台说明
- 统一平台说明
- 三维子系统说明
- 后端脚本说明
- 验收、演示、排障文档联动更新

### P2：收敛历史方案与图示

- 为实施方案增加状态标记
- 归档已失效计划
- 更新 drawio / mermaid 图示
- 完善对象 profile 和参考资料说明

### P3：研究目录专项治理

- 编码统一
- 研究索引
- 研究材料与项目文档的边界说明

## 8. 文档维护规则

后续建议强制执行以下规则：

- 项目正式说明只放在 `docs/`，根目录只保留总入口
- 每次新增后端路由或前端主要页面，都要补对应文档
- 变更权限、状态机、环境变量时，必须同步更新文档
- 每篇正式文档顶部增加 `最后更新日期`、`关联模块`、`状态`
- 历史方案必须显式标记 `已采纳`、`进行中`、`已归档`
- 所有 Markdown 本地链接需要通过脚本检查
- 所有文档统一 UTF-8 编码
- 术语统一使用 `MDAMS`，不再混用 `MEAM`

## 9. 完成标准

本轮文档治理完成后，应满足以下验收标准：

- 根 README 可作为唯一可信入口
- 仓库内 Markdown 本地链接无坏链
- 根目录不再存在与 `docs/` 重复的正文级文档
- 当前代码中的核心模块均有对应说明
- 部署、权限、统一平台、图像记录、三维子系统都有可直接阅读的主文档
- 历史计划与当前基线有明确区分
- 文档编码统一，终端和编辑器中不再出现中文乱码

## 10. 推荐落地方式

建议把本方案拆成三轮执行：

1. 第一轮只做入口、坏链、重复文档、状态文档和部署文档
2. 第二轮补齐 API、权限、图像记录、三维、平台、脚本文档
3. 第三轮处理研究目录、图示和归档规范

这样可以先把“可读、可找、可信”解决，再去做“全面、精细、长期可维护”。
