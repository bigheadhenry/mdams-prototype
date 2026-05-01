# 工作日志

## 规则

1. 每次项目开发、修改、重构、修复或配置变更，必须追加记录。
2. 每条记录至少包含日期、修改范围、变更内容、验证结果和备注。
3. 只追加，不回改历史；如需更正，另起一条“更正说明”。
4. 代码、文档、测试、部署和脚本都属于项目变更，不能遗漏。
5. 一次工作如果包含多个独立修改，尽量拆成多条记录，避免写成一大段。

## 记录格式

```text
YYYY-MM-DD
- 修改范围：...
- 变更内容：...
- 验证结果：...
- 备注：...
```

## 工作记录

### 2026-03-27 - 统一资源目录 profile 过滤
- 修改范围：平台统一资源目录、前端目录页、统一资源摘要、回归测试。
- 变更内容：补充 `profile_key/profile_label`，后端增加 `profile_key` 查询参数并按 profile 过滤；前端增加 Profile 下拉筛选，并在列表中显示 profile 标签。
- 验证结果：`python -m pytest backend\tests -q` 通过，`11 passed`；`npm run lint` 通过；`npm run build` 通过；`npm run test` 通过，`15 passed`。
- 备注：统一目录从“按关键字检索”推进到“可按对象 profile 检索”。

### 2026-03-27 - 平台来源接入模板与注册表
- 修改范围：平台来源抽象、来源注册表、二级来源适配器、平台路由。
- 变更内容：新增 `PlatformSourceAdapter`、`PlatformSourceRegistry` 和模板来源适配器；二维影像来源改为注册式适配器，平台路由改为通过注册表汇总来源和资源。
- 验证结果：`python -m py_compile` 通过；`python -m pytest backend\tests -q` 通过，`11 passed`。
- 备注：后续新增来源时，只需实现适配器并注册即可接入统一目录和统一详情。

### 2026-03-27 - 三维数据管理子系统
- 修改范围：三维数据模型、三维上传与详情、三维管理页、统一平台接入、回归测试。
- 变更内容：新增三维资源表和三维管理路由，支持上传、列表、详情、下载和删除；新增三维元数据分层构建和详情响应；前端增加 3D Data 管理入口。
- 验证结果：`python -m pytest backend\tests -q` 通过，`12 passed`；`python -m py_compile` 通过；`npm run lint` 通过；`npm run build` 通过；`npm run test` 通过，`15 passed`。
- 备注：MDAMS 的第二个真实来源子系统开始成型。

### 2026-03-27 - 三维资源包化
- 修改范围：三维资源模型、三维上传接口、三维详情服务、三维管理页、回归测试。
- 变更内容：将三维资源从单文件扩展为“资源记录 + 多文件记录”结构，支持模型、点云、倾斜摄影图像分别保存；详情页与下载接口同步展示文件构成并支持资源包下载。
- 验证结果：`python -m pytest backend\tests -q` 通过，`13 passed`；`python -m py_compile` 通过；`npm run lint` 通过；`npm run build` 通过；`npm run test` 通过，`15 passed`。
- 备注：三维子系统开始支持真正的资源包管理语义。

### 2026-03-27 - 三维文件预览
- 修改范围：三维详情接口、三维文件访问接口、前端三维详情页、三维子系统回归测试。
- 变更内容：为三维资源包新增文件级访问接口，详情响应补充每个文件的 `download_url/preview_url`；前端详情页新增图像预览区，倾斜摄影图像可直接缩略预览。
- 验证结果：`python -m pytest backend\tests -q` 通过，`13 passed`；`python -m py_compile` 通过；`npm run lint` 通过；`npm run build` 通过；`npm run test` 通过，`15 passed`。
- 备注：三维资源已具备基础“可查看”能力。

### 2026-03-27 - 三维版本与 Web 展示状态
- 修改范围：三维数据模型、三维详情响应、三维上传接口、前端三维管理页、平台适配器、三维子系统回归测试。
- 变更内容：为三维资源新增 `resource_group`、`version_label`、`version_order`、`is_current`、`is_web_preview`、`web_preview_status`、`web_preview_reason` 等字段；上传时可录入版本号和 Web 展示状态。
- 验证结果：`python -m pytest backend\tests -q` 通过，`13 passed`；`python -m py_compile` 通过；`npm run lint` 通过；`npm run build` 通过；`npm run test` 通过，`15 passed`。
- 备注：三维资源开始按“原始版 / 版本号 / 可展示状态”管理。

### 2026-03-27 - 三维数字对象聚合视图
- 修改范围：三维管理页、工作日志。
- 变更内容：三维资源列表改为按 `resource_group` 聚合展示，把一个数字对象视为一组版本资源；组内展开后可查看原始版、v1、v2 等版本记录。
- 验证结果：`npm run lint` 通过。
- 备注：管理视角从单条版本记录切换为“数字对象 + 版本列表”。

### 2026-03-27 - 三维数字对象概览卡
- 修改范围：三维管理页、工作日志。
- 变更内容：在对象级聚合视图上方增加概览卡，展示数字对象数、版本总数、可展示对象数和文件总数，并补充最近对象快捷入口。
- 验证结果：前端构建与测试通过。
- 备注：让管理页先看总览，再进入版本明细。

### 2026-03-27 - 三维 PRD 对照表
- 修改范围：三维 PRD 对照文档、工作日志。
- 变更内容：新增 `docs/THREE_D_PRD_ALIGNMENT.md`，将 PRD 的三层对象、元数据分层、生产链路、展示与保存分层、系统接口与分阶段建设要求，与当前三维子系统实现逐项对照。
- 验证结果：文档整理完成，未涉及代码变更。
- 备注：该文档用于后续三维子系统排期与缺口追踪。

### 2026-03-27 - 同步 GitHub
- 修改范围：工作日志、仓库同步流程。
- 变更内容：整理三维 PRD 对照表并补充工作日志，然后同步当前分支到 GitHub；同时更新 `.gitignore`，避免 Playwright 报告、测试缓存和本地参考材料误入仓库。
- 验证结果：仓库已同步到远端分支。
- 备注：同步内容以源码、文档和三维子系统最新实现为主，不包含本地生成物。

### 2026-03-27 - 三维 PRD 对齐与生产链路补强
- 修改范围：三维数据模型、藏品对象关联、标准元数据字典、生产链路记录、保存层与展示层分离、回归测试。
- 变更内容：为三维资源补充藏品对象关联和标准元数据字典；把采集、处理、发布、保存串入生产链路记录；把 Web 展示状态与长期保存状态分开管理。
- 验证结果：`python -m pytest backend\tests -q` 通过，`13 passed`；`python -m py_compile` 通过。
- 备注：三维子系统开始从“版本化资源包”推进到“对象关联 + 生产链路 + 保存层”结构。

### 2026-03-27 - 测试分层与契约测试
- 修改范围：pytest 配置、后端测试分层、三维字典契约、三维生产链路、测试策略文档、README 入口。
- 变更内容：新增 `pytest.ini`，按 `unit / contract / integration / smoke / system` 分层，并启用严格 marker；新增三维元数据字典契约测试和三维生产链路测试。
- 验证结果：`python -m pytest backend\tests -q` 通过，`15 passed`；`python -m py_compile` 通过。
- 备注：后续功能开发要求至少补一条契约测试或集成测试。

### 2026-03-27 - 三维查看器契约
- 修改范围：三维详情响应、三维查看器路由、前端 3D 类型定义、三维子系统回归测试。
- 变更内容：为三维详情新增 `viewer` 契约，统一描述是否可 Web 展示、预览文件、预览 URL 和渲染器类型；新增 `/api/three-d/resources/{id}/viewer` 路由。
- 验证结果：`python -m pytest backend\tests -q` 通过，`15 passed`；`python -m py_compile` 通过；`npm run build` 通过。
- 备注：三维“可展示”从状态字段推进为明确契约。

### 2026-03-27 - 三维 Web 查看器与测试模型
- 修改范围：前端三维查看器组件、三维管理页、前端依赖、测试模型资源、工作日志。
- 变更内容：新增基于 `@google/model-viewer` 的三维 Web 查看器组件，并接入三维管理页；补充本地 `glTF` 测试模型资源，便于浏览器端预览验证。
- 验证结果：`npm run build` 通过；`npm run test` 通过，`15 passed`；`python -m pytest backend\tests -q` 通过，`15 passed`。
- 备注：三维资源开始具备可交互的浏览器端查看能力。

### 2026-03-27 - 三维测试模型样例包扩充
- 修改范围：前端测试模型资源、三维管理页测试入口、工作日志。
- 变更内容：将测试模型扩展为更接近真实业务的样例包，覆盖外部依赖的 glTF、单文件 GLB 和高细节 GLB 三种常见输入形态。
- 验证结果：`npm run build` 通过；`npm run test` 通过，`15 passed`。
- 备注：样例包可用于后续兼容性测试和性能测试。

### 2026-03-27 - 三维子系统原型收口
- 修改范围：三维对象管理、查看器契约、版本管理、生产链路、测试样例、统一平台接入。
- 变更内容：将三维子系统收束为对象聚合、版本管理、Web 展示状态、查看器契约和样例包管理的原型形态；并明确后续要继续补展示治理、藏品对象强关联和长期保存体系。
- 验证结果：关键后端和前端测试持续通过。
- 备注：三维子系统已从“能管理”推进到“可持续验证的原型”。

### 2026-03-27 - 资源申请功能
- 修改范围：IIIF manifest、MiradorViewer、申请车页面、申请管理页面、申请单模型、申请导出、回归测试。
- 变更内容：在 Mirador 中增加“加入申请单”入口，形成申请车草稿；补充申请单与申请项模型、申请提交、审批、导出交付包和申请管理页。
- 验证结果：`python -m pytest backend\tests\test_applications.py -q` 通过；`python -m pytest backend\tests\test_routes_smoke.py -q` 通过；`npm run build` 通过；`npm run test` 通过，`15 passed`。
- 备注：二维影像申请流程已形成“加入申请车 -> 提交申请 -> 审批 -> 导出交付包”的闭环。

### 2026-03-28 - 导入 DigicolPhotoScan 生活用具样本
- 修改范围：本地开发库、导入脚本、工作日志。
- 变更内容：新增 `backend/scripts/import_2d_images.py` 导入脚本，并从 `DigicolPhotoScan/data/images/生活用具` 目录批量导入二维图片资源。
- 验证结果：导入 12 条样本资源，数据库中 `assets` 记录数为 12。
- 备注：为后续 Mirador 预览和申请功能提供样本数据。

### 2026-03-28 - 本地启动 Cantaloupe 并恢复 Mirador 预览
- 修改范围：Cantaloupe 本地配置、运行时目录、前后端服务、工作日志。
- 变更内容：下载并解压 Cantaloupe 5.0.6，生成本地专用配置文件，修正 `base_uri` 和图片目录，移除 UTF-8 BOM，解决启动时报错；恢复前端、后端和 Cantaloupe 服务联调。
- 验证结果：`/health` 正常；IIIF `info.json` 正常返回；Mirador 可正常从 Cantaloupe 获取图像。
- 备注：解决了本地 IIIF 服务链路的启动问题。

### 2026-03-28 - 生活用具资源全量导入
- 修改范围：二维资源库、导入脚本、工作日志。
- 变更内容：使用导入脚本将 `DigicolPhotoScan/data/images/生活用具` 目录中的全部 JPG 样本导入二维资源库。
- 验证结果：新增导入 292 条，连同前一次的 12 条，共计 304 条二维资源；`uploads` 目录也同步为 304 个文件。
- 备注：这批样本可直接用于浏览、预览和申请流程测试。

### 2026-03-29 - 用户类型与权限矩阵
- 修改范围：用户角色设计文档、README 入口、工作日志。
- 变更内容：整理形成第一版 `docs/USER_ROLE_PERMISSION_MATRIX.md`，明确数字化流程人员与业务人员两大类用户，定义二维与三维分别授权、藏品责任范围控制、资源可见范围与业务状态分离，以及第一版 `RBAC + scope` 落地建议。
- 验证结果：文档变更，未涉及代码运行与测试。
- 备注：后续前端菜单裁剪、后端接口权限保护和藏品责任范围建模都以此为基线。

### 2026-03-29 - 前端菜单可见矩阵与权限骨架
- 修改范围：角色权限文档、前端主入口、前端权限定义、后端权限依赖、认证上下文路由、关键接口保护、权限单元测试、README 入口、工作日志。
- 变更内容：新增 `docs/FRONTEND_MENU_VISIBILITY_MATRIX.md`，将角色矩阵细化为菜单可见矩阵；前端接入权限定义、示例用户切换、菜单裁剪、动作级权限控制和请求头透传；后端新增权限模块和认证上下文接口，并把二维资源、三维资源、申请审批等关键接口挂接到权限依赖上。
- 验证结果：`python -m pytest backend\tests\test_permissions.py backend\tests\test_applications.py -q` 通过，`6 passed`；`npm run build` 通过。
- 备注：当前仍是演示态权限框架，但已经能体现不同角色看到不同内容。

### 2026-03-29 - 真实用户与登录上下文
- 修改范围：用户/角色/会话数据模型、认证服务、认证路由、权限解析、前端登录入口、前端主应用认证上下文、认证与权限单元测试、工作日志。
- 变更内容：新增 users / roles / user_roles / user_sessions 数据模型和认证服务；补充 `/api/auth/users`、`/api/auth/login`、`/api/auth/logout`、`/api/auth/context`；前端主入口从演示用户切换为真实登录上下文，登录后通过 Bearer token 获取角色与权限。
- 验证结果：`python -m pytest backend\tests\test_auth_service.py backend\tests\test_permissions.py backend\tests\test_applications.py -q` 通过，`8 passed`；`python -m py_compile` 通过；`npm run build` 通过。
- 备注：默认种子账号的统一测试密码为 `mdams123`。

### 2026-03-29 - IIIF 认证与应用认证统一
- 修改范围：认证方案文档、IIIF 访问控制、资源可见范围、前端资源详情、工作日志。
- 变更内容：明确 MDAMS 应用认证作为主认证，IIIF 访问控制挂在同一身份体系之下；二维资源增加 `visibility_scope` 和 `collection_object_id`，`collection_owner` 的责任范围过滤接入资源列表、详情和 IIIF 入口。
- 验证结果：后端目标测试通过；`npm run build` 通过。
- 备注：后续 Mirador 取图也将统一走 MDAMS 的权限入口。

### 2026-03-29 - 登录后的权限回归测试
- 修改范围：前端 Playwright 测试、前端主应用、统一资源目录、统一资源详情。
- 变更内容：补充登录态测试，使用 token 和模拟 auth context 验证不同角色的菜单可见性与资源可见性；覆盖 `system_admin`、`resource_user` 和 `collection_owner` 的访问差异。
- 验证结果：`npm run test` 通过，`15 passed`。
- 备注：登录后的测试用于直接验证权限关系是否正确。

### 2026-03-29 - collection_owner 范围回归测试
- 修改范围：前端 Playwright 测试、统一资源目录、统一资源详情、工作日志。
- 变更内容：补充 `collection_owner` 的范围权限回归，验证其能看到自己责任范围内的资源，但看不到其他责任范围的 `owner_only` 资源。
- 验证结果：`npm run build` 通过；`npm run test` 通过，`21 passed`。
- 备注：这条测试将责任范围权限真正落到前端回归里。

### 2026-03-29 - 工作日志编码统一
- 修改范围：工作日志文件本身。
- 变更内容：将旧的乱码日志重写为统一中文版本，并改用 UTF-8 编码保存，避免 Windows 下再出现不可读字符。
- 验证结果：已完成重写，后续可直接用中文继续追加。
- 备注：这是一次基础设施整理，确保后续所有工作记录都能正常阅读。
### 2026-03-29 - README 重新整理
- 修改范围：README 文档。
- 变更内容：根据当前项目实际状态，重写 README 为统一中文版本，补充二维影像子系统、三维数据管理子系统、统一平台、权限登录、测试与工作日志说明，并整理快速开始、开发命令和主要文档入口。
- 验证结果：文档已重写，内容已人工核对；无需运行代码测试。
- 备注：README 现已与当前仓库实现保持一致，避免旧版乱码和过时描述。

### 2026-03-29 - 首页与相关文档整理
- 修改范围：README、项目状态、部署与配置、下一阶段计划、认证与 IIIF 整合文档。
- 变更内容：根据当前仓库实现重写 README 首页说明，并将项目状态、部署说明、下一阶段计划、认证与 IIIF 整合方案同步到当前状态，补充二维影像、三维数据管理、统一平台、权限登录、申请流程和测试分层的最新内容。
- 验证结果：文档已重写并人工核对，可正常阅读；无需运行代码测试。
- 备注：这次整理重点是把仓库首页和关键入口文档统一到当前实现，避免读到过时或乱码内容。

### 2026-03-29 - 文档收口与首页对齐
- 修改范围：ARCHITECTURE、DEMO_FLOW、DATA_INGEST_ARCHITECTURE、WORKFLOW_GUIDE、DEPLOYMENT、INSTALL_DOCKER_WINDOWS、CONFIG_REFACTOR_PLAN、TROUBLESHOOTING。
- 变更内容：将多份历史文档重写为统一中文版本，并按当前实现更新为二维影像子系统、三维数据管理子系统、统一平台、登录权限、申请流程、部署配置和工作流的当前状态；同时保留旧文档的跳转或归档说明，避免继续使用过时描述。
- 验证结果：文档已重写并人工核对，可正常阅读；无需运行代码测试。
- 备注：这次收口完成后，仓库首页与相关辅助文档已经基本对齐当前实现。

### 2026-03-30 - 角色 - 页面 - 动作对照表
- 修改范围：角色权限文档、前端/后端权限说明的补充文档。
- 变更内容：新增 `docs/ROLE_PAGE_ACTION_MATRIX.md`，将当前系统中不同角色可见的页面与可执行动作整理为统一对照表，覆盖 system_admin、resource_user、collection_owner、application_reviewer 和三维管理角色。
- 验证结果：文档新增完成，内容已人工核对。
- 备注：这份表可直接作为后续权限测试和功能验收的基线。

### 2026-03-30 - 缩略图待办项
- 修改范围：下一阶段计划文档。
- 变更内容：在 `docs/NEXT_PHASE_PLAN.md` 中新增二维影像缩略图规格与生成策略待办项，明确后续需要定义缩略图尺寸、格式、预生成策略、即时切片边界和失败降级规则。
- 验证结果：文档已更新，内容已人工核对。
- 备注：该项暂不进入主链路实现，后续作为独立优化任务推进。

### 2026-04-02 - Mirador AI 控制面板与日志链路
- 修改范围：Mirador 前端视图、AI 控制面板、后端 AI 解析路由、OpenAI 配置、前端类型定义、环境变量示例、工作日志。
- 变更内容：为 Mirador 浏览页增加右侧 AI 控制面板，支持自然语言控制缩放、平移、重置、适配窗口，以及关键词检索和对比图打开确认；后端新增 AI 解析与资源搜索接口，并接入 OpenAI 作为意图解析层；同时补充前后端操作日志，记录用户输入、AI 计划、候选图选择、确认和执行结果，便于后续回溯。
- 验证结果：`python -m py_compile backend/app/config.py backend/app/main.py backend/app/routers/ai_mirador.py` 通过；`npm run build` 通过；`npx eslint src/MiradorViewer.tsx src/MiradorAiPanel.tsx src/types/assets.ts src/types/mirador.d.ts --max-warnings 0` 通过。
- 备注：本次变更重点是把 AI 控制做成可追踪、可确认、可回放的交互链路，后续可继续扩展为数据库审计日志。

### 2026-04-02 - Mirador 比较模式与动作日志补全
- 修改范围：Mirador AI 面板、后端 AI 意图解析、工作日志。
- 变更内容：补全比较模式的真实状态切换逻辑，新增“进入/退出比较模式”和“关闭对比”控制，按照 Mirador 的 `mosaic` / `elastic` 工作区状态切换并保持窗口日志可见；后端对“比较模式”“单图模式”“退出对比”等指令做了更明确的意图识别，避免被误判为普通找图。
- 验证结果：`python -m py_compile backend/app/config.py backend/app/main.py backend/app/routers/ai_mirador.py` 通过；`npm run build` 通过；`npx eslint src/MiradorViewer.tsx src/MiradorAiPanel.tsx src/types/assets.ts src/types/mirador.d.ts --max-warnings 0` 通过。
- 备注：现在比较模式不仅能开关，而且能在面板中看到当前模式、窗口数和完整动作日志。

### 2026-04-02 - Moonshot 模型接入
- 修改范围：后端 AI 配置、环境变量示例、工作日志。
- 变更内容：将 AI 接入默认切换为 Moonshot 的 OpenAI 兼容服务地址，新增 `MOONSHOT_API_KEY`、`MOONSHOT_BASE_URL` 和 `MOONSHOT_MODEL` 配置，并保留 `OPENAI_*` 作为兼容覆盖；默认服务地址指向 `https://api.moonshot.cn/v1`，默认模型改为 `kimi-k2.5`。
- 验证结果：配置文件和环境变量示例已更新，尚未做真实 API 调用验证，因为当前环境未设置有效 key。
- 备注：Moonshot 文档的 Chat API 使用 OpenAI 兼容方式接入，后端现有调用逻辑可以直接复用。

### 2026-04-02 - Moonshot 联通性验证
- 修改范围：本地 `.env`、Moonshot API 连通性、工作日志。
- 变更内容：在本地 `C:\Users\bighe\OneDrive\AI\Codex\.env` 填入 Moonshot 配置后，直接向 `POST /v1/chat/completions` 发送最小 JSON 请求，验证模型服务、Key 和返回格式是否可用。
- 验证结果：请求返回 `200`，模型 `kimi-k2.5` 可正常返回 JSON，响应内容为 `{"ping":"pong"}`。
- 备注：这次验证说明 Moonshot 链路已经可用；后续若手动启动后端，需要确保进程实际加载了同样的环境变量。

### 2026-04-02 - 后端自动读取 .env
- 修改范围：后端配置加载、工作日志。
- 变更内容：在 `backend/app/config.py` 增加轻量 `.env` 自动加载逻辑，启动后端时会优先读取项目父目录中的本地 `.env` 文件，再解析数据库、Moonshot 和其他运行配置。
- 验证结果：配置文件已更新，随后可通过启动后端或运行配置导入来验证环境变量是否自动生效。
- 备注：这样本地改 `.env` 后无需手动导出环境变量，启动体验更顺手。

### 2026-04-02 - .env 加载顺序修正
- 修改范围：后端配置加载、工作日志。
- 变更内容：修正 `.env` 搜索顺序，改为先读取更上层目录中的配置，再读取更接近仓库的配置，避免仓库根目录里空的 `.env` 抢先占位导致父目录配置未生效。
- 验证结果：重新导入 `backend.app.config` 后，能够正确读到 `C:\Users\bighe\OneDrive\AI\Codex\.env` 里的 `MOONSHOT_API_KEY`，`has_key` 验证为 `True`。
- 备注：这一步把本地配置加载路径彻底理顺了，后端启动时就能直接吃到你填好的环境变量。

### 2026-04-02 - Mirador AI 后端回归测试补充
- 修改范围：Mirador AI 后端测试、工作日志。
- 变更内容：新增 `backend/tests/test_ai_mirador.py`，覆盖 OpenAI / Moonshot 计划注入后的对比搜索、无候选图时回退到普通搜索、以及 `search_assets` 的可见性过滤；测试直接调用 AI 路由函数，验证返回计划、候选图、权限边界和 manifest 生成路径。
- 验证结果：`python -m pytest backend\tests\test_ai_mirador.py -q` 通过，`3 passed`；`python -m pytest backend\tests -q` 通过，`37 passed`。
- 备注：后续继续扩展 Mirador AI 时，可以先补这里的回归，再改功能逻辑。

### 2026-04-02 - Mirador AI 前端回归测试补充
- 修改范围：Mirador AI 前端测试、Mirador AI 面板锚点、资产列表预览按钮、dashboard 回归测试、工作日志。
- 变更内容：新增 `frontend/tests/mirador-ai.spec.ts`，覆盖打开资产预览、唤出 AI 面板、提交自然语言指令、展示候选图与确认态、切换候选目标；同时为 AI 面板补充稳定的 `data-testid`，为资产列表预览按钮补充测试锚点，并修正 dashboard 回归里对重复单元格文本的严格定位问题。
- 验证结果：`npm run test -- mirador-ai.spec.ts` 通过，`3 passed`；`npm run test` 通过，`24 passed`；`npm run build` 通过。
- 备注：这次把前端 AI 交互和既有 dashboard 回归一起收紧了，后面继续加 AI 功能时可以直接沿用这套测试入口。

### 2026-04-03 - 代码审计与数据恢复
- 修改范围：后端配置、Mirador 前端、三维管理页、参考资源导入、工作日志、测试回归、忽略规则。
- 变更内容：审计并修正 `.env` 自动加载顺序、清理前端 lint 警告、恢复 Mirador 和 AI 面板中文文案；同时把 `reference/资源包` 重新导入当前 SQLite 库，恢复 12 条二维影像资源索引，并将测试产物与临时数据库加入 `.gitignore`。
- 验证结果：`python -m pytest backend\tests -q` 通过，`38 passed`；`npm run lint` 通过；`npm run build` 通过；`npm run test -- mirador-ai.spec.ts` 通过，`3 passed`；参考资源导入脚本 dry-run 与正式导入均可执行。
- 备注：当前前端“no data”问题的根因是数据库资产记录为空，不是图片文件缺失；已恢复索引，后续如需继续扩容可重复运行参考导入脚本。

### 2026-04-04 - Mirador IIIF 直连 Cantaloupe
- 修改范围：IIIF 路由、配置默认值、单测、环境变量示例、工作日志。
- 变更内容：把 manifest 中的 image service 从后端代理路径改为直接指向 Cantaloupe 公共地址，保持旧的 proxy 路由作为兼容入口；同时把本地默认 `CANTALOUPE_PUBLIC_URL` 调整为 `http://localhost:8182/iiif/2`，并同步更新测试断言与 `.env.example`。
- 验证结果：当前只修复了 `backend/tests/test_asset_visibility.py` 的旧路径断言，后续需要重新跑 `python -m pytest backend\\tests -q` 以确认全量后端测试通过。
- 备注：这是对照 `mirador-compare` 的第一步优化，目标是减少浏览器到首图之间的请求绕行，让 Mirador 更快拿到 IIIF service。

### 2026-04-04 - Mirador 直连 Cantaloupe 预检修复
- 修改范围：Mirador 前端请求拦截、工作日志。
- 变更内容：给 Mirador 的统一请求预处理器加了白名单，只对后端 `api/auth` 请求附加 `Authorization` 头，不再把这个头带到 Cantaloupe 的 IIIF 请求上，避免跨域预检卡住图片加载。
- 验证结果：`npm run build` 通过；前端构建后可热更新到当前运行中的 Vite 开发服务。
- 备注：这一步对应你截图里“预览一直白屏”的现象，根因是直接 Cantaloupe 请求被额外鉴权头触发了预检，但浏览器侧不需要也不应该给图片服务带 token。

### 2026-04-04 - 列表缩略图缓存失效修复
- 修改范围：缩略图缓存生成逻辑、回归测试、工作日志。
- 变更内容：把列表页缩略图的缓存键从固定的 `asset-{id}.preview.jpg` 改成带源文件指纹的路径，改为按 `asset id + 源文件 mtime/size` 匹配；同一个资产一旦源文件变化，就会自动生成新的缩略图文件，避免继续复用旧错图。
- 验证结果：新增 `backend/tests/test_preview_images.py`，`python -m pytest backend\\tests\\test_preview_images.py -q` 通过，`1 passed`；`python -m pytest backend\\tests -q` 通过，`39 passed`。
- 备注：这能修正你看到的“列表缩略图和大图不一致”的问题，本质是旧预览缓存没有失效，而不是 Mirador 主图加载慢。

### 2026-04-04 - 缩略图浏览器缓存切断
- 修改范围：资产列表前端、缩略图接口缓存头、工作日志。
- 变更内容：列表页缩略图 URL 追加 `created_at + file_size` 版本标识，并给 `/assets/{id}/preview` 响应加上 `Cache-Control: no-store`，确保浏览器不会继续复用旧的缩略图响应。
- 验证结果：前端代码已更新，后端需要重启后才能生效；下一轮刷新页面时会强制取新图。
- 备注：这一步是专门针对“我改了缩略图逻辑但页面还是看见旧图”的情况，避免浏览器或中间缓存把旧响应留住。

### 2026-04-04 - Mirador AI 执行层加固
- 修改范围：Mirador AI 面板、Mirador Viewer、前端回归测试、工作日志。
- 变更内容：重写 `frontend/src/MiradorAiPanel.tsx` 的执行层，给 `zoom/pan/reset/fit` 增加真实视口变更校验，优先直连 OSD viewer 执行动作，并在 `viewerApiRef.current.actions` 不可用时回退到 Mirador 官方 action creator；同时让 AI 面板显式感知 `MiradorViewer` 的 ready 状态，在 viewer 未完成初始化前禁用快捷控制和确认按钮，避免“按钮可点但实际未就绪”的假执行。
- 验证结果：`npm run test -- mirador-ai.spec.ts` 通过，`3 passed`；`npm run build` 通过。
- 备注：这一步先把现有动作的执行可靠性补扎实了；Playwright 仍主要覆盖计划流和候选图确认，后续如果要把“真实缩放/平移成功”也做成稳定 E2E，需要再补更贴近 Mirador 运行态的 viewport 测试桩。

### 2026-04-06 - 影像记录拆分与 IIIF 访问层 Phase 1 基线
- 修改范围：影像记录模型与权限、影像记录路由与验证服务、IIIF 访问副本服务、资产/入库/详情/IIIF 路由、前端录入工作台与权限菜单、类型定义、回归测试、阶段方案文档、工作日志。
- 变更内容：围绕“录入人员先建记录、摄影师后传图匹配”的新流程，新增 `ImageRecord` 相关后端与前端骨架，包括记录列表/表单/详情/工作台、记录提交与退回、待上传记录池、临时上传分析、显式确认绑定/替换；同时补充 `image_record_validation` 和 `iiif_access` 服务，把校验拆成提交校验与绑定后校验两阶段，并把 PSB / 大 TIFF 的 IIIF 访问策略收敛到“原件保留、访问副本独立、Mirador 只读访问副本”的方向。另新增 4 份阶段基线文档，分别固定角色拆分、匹配机制、验证规则和 IIIF 访问格式策略。
- 验证结果：`python -m pytest backend\tests\test_image_records.py backend\tests\test_iiif_access_phase1.py backend\tests\test_ingest.py backend\tests\test_derivative_policy.py backend\tests\test_metadata_layers.py -q` 通过，`25 passed`；`npm run build` 通过。
- 备注：这次提交的重点是把 Phase 1 的业务边界和实现骨架一起推到仓库里，后续新线程可以直接以 4 份 `IMAGE_*_PHASE1_PLAN.md` 文档为固定实施基线继续推进。

### 2026-04-06 - 影像记录上传链路修复与摄影师替换入口恢复
- 修改范围：影像记录绑定/替换路由、IIIF 访问副本衍生触发、PSB/PSD 探测兜底、摄影师工作台与详情页、后端与前端回归测试、工作日志。
- 变更内容：修正 `ImageRecord` 的确认绑定与替换流程，使其复用统一的 IIIF 访问策略判断，必要时将新资产置为 `processing` 并触发 `generate_iiif_access_derivative`；补充临时上传分析的 ExifTool / `pyvips` 兜底，避免 PSD/PSB 因 Pillow 无法读取而被误判为不可绑定；同时将摄影师工作台从仅看 `ready_for_upload` 扩展为可继续查看自己 `uploaded_pending_validation` 的已指派记录，并允许在详情页重新进入替换上传流程。
- 验证结果：`pytest backend\tests\test_image_records.py -q` 通过，`10 passed`；`pytest backend\tests\test_iiif_access_phase1.py -q` 通过，`3 passed`；`npm run build` 通过；`npx playwright test tests/dashboard.spec.ts` 通过，`27 passed`。
- 备注：Playwright 运行期间仍有现存的 Vite 代理 `ECONNREFUSED` 日志噪音，但不影响用例通过；本次修复主要收敛了影像记录上传链路与摄影师替换闭环。

### 2026-04-06 - 文档体系重构与总入口更新
- 修改范围：根 `README.md`、`docs/` 目录结构、项目状态、测试策略、权限矩阵、菜单矩阵、工作流、部署与运维、认证与 IIIF、图像记录工作台、API 路由、平台适配器、三维子系统、环境变量、脚本说明、参考数据说明、文档索引、工作日志。
- 变更内容：将原本平铺的 `docs/` 重组为中文分类目录，统一整理为总览、架构设计、产品与流程、实施方案、部署与运维、参考资料、图示、研究八个分区；重写根 `README.md` 使其与当前项目实现保持一致，并修复原有坏链；同时补齐此前缺失的专题文档，包括 `API_ROUTE_MAP.md`、`PLATFORM_SOURCE_ADAPTERS.md`、`THREE_D_SUBSYSTEM_ARCHITECTURE.md`、`IMAGE_RECORD_WORKBENCH_GUIDE.md`、`ENVIRONMENT_VARIABLES.md`、`SCRIPT_AND_JOB_GUIDE.md`、`REFERENCE_DATASET_GUIDE.md` 等，使文档覆盖到当前后端路由、统一平台、三维子系统、图像记录工作台、环境变量和参考资源导入链路。
- 验证结果：对仓库内 Markdown 本地链接执行检查，结果为 `NO_BROKEN_LOCAL_LINKS`；本轮未运行代码测试，因为修改范围仅限文档，但所有重写内容均已对照当前 `backend/app/*`、`frontend/src/*`、`docker-compose.yml` 和 `.env.example` 实际实现核对。
- 备注：当前文档体系已经基本形成单一正式入口，后续应以 `docs/` 为唯一主文档目录；根目录中的历史 Markdown 文档仍可在下一轮继续收敛为跳转页或归档说明，以彻底消除重复入口。

### 2026-04-06 - PostgreSQL 测试环境固化与本机联调打通
- 修改范围：后端测试夹具、健康检查测试、资产可见性测试、批处理脚本默认数据库连接、本地 PostgreSQL 管理脚本、本地 compose、README、部署与运维文档、工作日志。
- 变更内容：将 `backend/tests` 统一切换为 PostgreSQL 测试库工作流，新增 `TEST_DATABASE_URL` 约定，并让测试在缺失数据库时给出明确跳过原因；修正测试夹具中 SQLAlchemy URL 密码被掩码导致的认证失败问题；把多个 `backend/scripts/*` 的默认 `--database-url` 从 `backend-dev.db` 改为 PostgreSQL；新增仓库根目录 `manage_local_postgres.ps1` 与 `docker-compose.local-postgres.yml`，用于在本机一键启动、查看、停止、重置独立 PostgreSQL 测试环境；同时删除 `docs/01-总览/DEMO_FLOW.md` 和 `docs/01-总览/DOCUMENTATION_UPDATE_PLAN.md` 两份旧文档，使其与本轮结构调整一并收敛。
- 验证结果：使用 `.\manage_local_postgres.ps1 up` 在本机拉起 `mdams-local-postgres`，主机侧 `localhost:5432` 可用，`meam_db` 与 `meam_db_test` 均可正常连接；执行 `python -m pytest backend\tests`，结果为 `55 passed`。
- 备注：当前仓库已经具备稳定的本机 PostgreSQL 测试基线；后续如继续推进数据库侧演进，建议下一步补齐 Alembic 迁移链，逐步替代 `Base.metadata.create_all()` 的启动式建表方式。

### 2026-04-08 - 研究记忆层建立与研究文档对齐
- 修改范围：`memory/`、`tasks/`、研究子项目文档、工作日志。
- 变更内容：新增稳定的 `memory/` 与 `tasks/` 层，用于沉淀项目简述、原型设计、论文论点、实验记录、设计决策和术语翻译；同时重写研究子项目中的当前项目事实、标准映射、标准到实现映射、概念模型、评估框架、论文大纲与研究 README，使其与截至 2026-04-08 的当前仓库实现保持一致；新增 `论文写作摘要（PAPER_READY_SUMMARY）.md` 和 `研究文档对齐差异清单（RESEARCH_ALIGNMENT_DIFF_CHECKLIST）.md`，分别服务论文写作和后续持续对齐。
- 验证结果：已人工核对新增与重写文档内容，使其与 `README.md`、`docs/01-总览/PROJECT_STATUS.md`、`docs/01-总览/WORK_LOG.md`、`backend/app/`、`frontend/src/` 当前结构保持一致；本轮未运行代码测试，因为修改范围仅限 Markdown 文档与任务记忆层。
- 备注：这一步的重点不是新增更多研究材料，而是先消除“研究线落后于实现线”的漂移，为后续统一对象模型、PREMIS 事件模型和 metadata profile 工作建立稳定基线。

### 2026-04-08 - 统一对象模型、PREMIS 最小事件模型与 metadata/profile 基线
- 修改范围：研究子项目文档、`memory/`、`tasks/`、工作日志。
- 变更内容：新增 `统一对象模型（UNIFIED_OBJECT_MODEL）.md`，把 `Asset`、`ImageRecord`、三维对象/版本、访问表示、导出表示、统一平台与权限范围收敛为一页对象框架；重写 `PREMIS事件映射（PREMIS_EVENT_MAPPING）.md` 为最小可实施事件模型，明确事件记录结构、统一词表、P0/P1 事件集合和按工作流映射；重写 `图像技术元数据映射（IMAGE_METADATA_CROSSWALK）.md`，使其直接对应当前二维元数据分层字段；新增 `三维元数据最小配置说明（THREE_D_METADATA_MINIMUM_PROFILE）.md`，把当前三维 metadata 分层、文件角色词表与最小 profile 收口；同步更新研究 README、项目记忆和任务层，把当前任务切换为 IIIF / BagIt / OAIS 三项支撑材料。
- 验证结果：已对照 `backend/app/models.py`、`backend/app/services/metadata_layers.py`、`backend/app/services/three_d_metadata.py`、`backend/app/services/three_d_storage.py`、`backend/app/services/three_d_detail.py` 人工核对文档字段与术语；本轮未运行代码测试，因为修改范围仅限 Markdown 文档与任务记忆层。
- 备注：这一步把研究线从“已有概念材料”推进到“已有可复用的对象、事件和 metadata/profile 基线”，后续标准论证与实现 formalization 可以直接建立在这组文件上。

### 2026-04-08 - IIIF、BagIt 与 OAIS 支撑材料收口
- 修改范围：研究子项目文档、`memory/`、`tasks/`、工作日志。
- 变更内容：重写 `IIIF清单配置说明（IIIF_MANIFEST_PROFILE）.md`，使其直接对应 `backend/app/routers/iiif.py`、`iiif_access.py`、Mirador 消费路径和权限测试；重写 `长期保存SIP打包说明（BAGIT_SIP_PROFILE）.md`，把 `download-bag` 路由当前真实生成的 bag 结构、tag files、payload 和边界收敛为可引用说明；新增 `OAIS范围对照（OAIS_SCOPE_MAP）.md`，以轻量范围图和职能域对照说明当前系统与 OAIS 的概念关系；同步更新研究 README、项目记忆、任务层和对齐差异清单，把当前任务切换为“标准化演示主链路”。
- 验证结果：已对照 `backend/app/routers/iiif.py`、`backend/app/routers/downloads.py`、`backend/tests/test_asset_visibility.py`、`frontend/src/MiradorViewer.tsx`、`docs/08-研究/输出层边界说明（EXPORT_BOUNDARIES）.md` 人工核对文档内容；本轮未运行代码测试，因为修改范围仅限 Markdown 文档与任务记忆层。
- 备注：这一步的重点是把标准论证从“高层映射”推进到“带实现锚点的支撑材料”，为后续论文案例链和真实样本说明建立直接引用基础。

### 2026-04-08 - 标准化演示主链路与论文案例摘要
- 修改范围：研究子项目文档、`memory/`、`tasks/`、工作日志。
- 变更内容：新增 `标准化演示主链路（STANDARDIZED_DEMO_CHAINS）.md`，将二维数字资产主链路、图像记录协作链路和三维对象与统一平台链路固化为 3 条标准化案例链，分别补入适用角色、前提条件、演示步骤、预期输出、验证点和研究材料链接；新增 `演示链路论文案例摘要（DEMO_CASE_SUMMARY）.md`，把这 3 条链路压缩为可直接进入论文“当前实现与演示链路”章节的案例摘要；同步更新研究 README、项目记忆、任务层和 backlog，把当前任务切换为 IIIF / BagIt 真实样本级材料。
- 验证结果：已对照 `docs/03-产品与流程/WORKFLOW_GUIDE.md`、`docs/03-产品与流程/IMAGE_RECORD_WORKBENCH_GUIDE.md`、`frontend/src/App.tsx`、`backend/tests/test_applications.py`、`backend/tests/test_image_records.py`、`backend/tests/test_three_d_subsystem.py` 人工核对链路步骤与验证点；本轮未运行代码测试，因为修改范围仅限 Markdown 文档与任务记忆层。
- 备注：这一步把当前研究底座进一步压缩成可演示、可验收、可写入论文案例链的材料，后续重点应转向真实样本和结构注释，增强证据密度。

### 2026-04-08 - IIIF 与 BagIt 样本级证据补充
- 修改范围：研究子项目文档、`memory/`、`tasks/`、工作日志。
- 变更内容：新增 `IIIF清单样本（IIIF_MANIFEST_SAMPLE）.md`，基于当前 `iiif.py`、`iiif_access.py` 和权限测试整理代表性 Manifest 样本与字段注释；新增 `BagIt样本结构（BAGIT_SAMPLE_STRUCTURE）.md`，基于当前 `download-bag` 打包逻辑整理代表性 bag 目录样本、tag files 和关键字段说明；同步更新研究 README、项目记忆、任务层和 backlog，把当前任务切换为“将研究文档推进到更稳定的实施边界”。
- 验证结果：已对照 `backend/app/routers/iiif.py`、`backend/app/services/iiif_access.py`、`backend/tests/test_asset_visibility.py`、`backend/app/routers/downloads.py`、`frontend/src/components/AssetDetail.tsx`、`frontend/src/components/UnifiedResourceDetail.tsx` 人工核对样本结构和字段说明；本轮未运行代码测试，因为修改范围仅限 Markdown 文档与任务记忆层。
- 备注：这一步的重点是把标准支撑材料从“有实现锚点”进一步推进到“有样本级证据”，为论文和对外演示提供更直接的结构材料。

### 2026-04-08 - 实施边界推进清单与下一轮优先项切换
- 修改范围：研究子项目文档、`memory/`、`tasks/`、工作日志。
- 变更内容：新增 `实施边界推进清单（IMPLEMENTATION_BOUNDARY_CHECKLIST）.md`，把统一对象模型、PREMIS 风格事件模型、二维与三维 profile、IIIF 与 BagIt 输出层分别压缩为“当前锚点 / 当前断层 / 推荐动作 / 优先级”的实施边界清单，并明确下一轮最推荐先做“二维 profile 必填规则统一”和“IIIF / BagIt 输出层 contract tests”；同步更新研究 README、项目记忆、对齐差异清单、当前任务和 backlog，把当前任务切换为“挑选 1 到 2 个优先项进入实现或测试补强”。
- 验证结果：已对照 `backend/app/models.py`、`backend/app/services/image_record_validation.py`、`backend/app/services/metadata_layers.py`、`backend/app/services/reference_import.py`、`backend/app/services/three_d_metadata.py`、`backend/tests/test_metadata_layers.py`、`backend/tests/test_reference_import.py`、`backend/tests/test_three_d_dictionary.py`、`backend/tests/test_iiif_access_phase1.py` 人工核对实施边界判断；本轮未运行代码测试，因为修改范围仅限 Markdown 文档与任务记忆层。
- 备注：这一步把研究线从“文档已经齐”继续推进到“哪些项值得进入代码约束或测试契约”的层级，避免后续再次停留在只增写说明而不增加实施证据的状态。

### 2026-04-08 - 二维 profile 规则统一与 IIIF / BagIt 输出层 contract tests
- 修改范围：`backend/app/services/metadata_layers.py`、`backend/app/services/image_record_validation.py`、`backend/app/services/reference_import.py`、后端测试、`memory/`、`tasks/`、工作日志。
- 变更内容：将二维 profile 的最小必填字段收口到 `metadata_layers.py` 中的共享规则来源，并让 `image_record_validation.py` 与 `reference_import.py` 共同引用；同时为 `movable_artifact` 参考导入补充 `object_number / 文物号` 提取逻辑，消除提交校验与导入完整性判断的语义分叉；新增 `backend/tests/test_output_contracts.py`，用不依赖 PostgreSQL 的方式补齐 IIIF Manifest 输出编码与 metadata 条目、BagIt tag files / fixity / 失败模式的 unit + contract 测试；同步更新项目记忆和任务层，把下一当前任务切换为“跨子系统最小事件边界”。
- 验证结果：执行 `pytest backend/tests/test_metadata_layers.py backend/tests/test_reference_import.py -q`，结果 `13 passed`；执行 `pytest backend/tests/test_output_contracts.py -q`，结果 `3 passed`；执行 `pytest backend/tests/test_image_records.py -q`，结果 `1 passed, 19 skipped`，跳过原因是本地 PostgreSQL `localhost:5432` 未启动。
- 备注：本轮为了运行仓库测试，执行了 `python3 -m pip install -r backend/requirements-dev.txt`；安装成功，但当前全局 Python 环境中已有其他项目依赖被降级，后续若要避免环境串扰，应优先改用项目虚拟环境。

### 2026-04-08 - 后续 5 个关键讨论问题正式化
- 修改范围：研究子项目文档、工作日志。
- 变更内容：新增 `关键讨论问题（KEY_DISCUSSION_QUESTIONS）.md`，把后续最该正式讨论的 5 个问题固定为：跨子系统最小事件边界、统一对象模型的落点、最小 profile 约束层级、IIIF / BagIt 输出层长期定位、以及下一阶段完成标准；对每个问题补入当前事实、可选方案、推荐立场、对实现和论文的影响，以及建议讨论顺序；同步更新研究 README，把该文档纳入建议阅读顺序和当前状态说明。
- 验证结果：已对照 `tasks/current_task.md`、`docs/08-研究/实施边界推进清单（IMPLEMENTATION_BOUNDARY_CHECKLIST）.md`、`memory/prototype_design.md`、`memory/decisions.md` 和当前代码边界人工核对讨论问题与当前推进状态的一致性；本轮未运行代码测试，因为修改范围仅限 Markdown 文档。
- 备注：这一步的作用不是新增实现，而是为后续决策会、论文方法讨论和下一轮实施优先级排序提供固定框架，避免项目再次回到分散讨论状态。

### 2026-04-10 - 跨子系统最小事件边界正式化
- 修改范围：研究子项目文档、`memory/`、`tasks/`、工作日志。
- 变更内容：新增 `跨子系统最小事件边界（CROSS_SYSTEM_EVENT_BOUNDARY）.md`，把当前系统中与事件相关的表达正式分为状态字段、detail 层 lifecycle / timeline、局部正式事件对象、输出层结果四类，并按二维资产、图像记录、三维对象、访问/导出表示、申请交付五个子域划定最小事件边界；同时明确当前不建议直接引入统一事件表，而应先把事件边界落实到 detail / test 层；同步更新研究 README、项目记忆、设计决策与任务层，把当前任务切换为“事件边界在 detail / test 层的优先落地方案”。
- 验证结果：已对照 `docs/08-研究/PREMIS事件映射（PREMIS_EVENT_MAPPING）.md`、`backend/app/services/asset_detail.py`、`backend/app/services/three_d_detail.py`、`backend/app/services/three_d_production.py`、`backend/tests/test_three_d_production.py` 和 `memory/paper_argument.md` 人工核对事件边界说明与当前实现锚点的一致性；本轮未运行代码测试，因为修改范围仅限 Markdown 文档与任务记忆层。
- 备注：这一步的目标不是增加新功能，而是把“事件到底是什么、先落到哪里”从讨论问题推进为一份可直接指导下一轮实现和论文表达的正式边界说明。

### 2026-04-12 - AI 操控 Mirador 工具调用标准化与 MCP 化路线
- 修改范围：AI Mirador 后端路由、Mirador AI 前端面板、前端类型定义、Mirador AI 测试、实施方案文档、工作日志。
- 变更内容：新增 `docs/04-实施方案/AI_MIRADOR_CONTROL_ROADMAP.md`，将当前“REST AI 计划器 + 前端 Mirador 执行器 + IIIF 服务”的链路拆解为 REST 兼容层标准化、工具注册表与权限审计、浏览器执行桥接、MCP Server 化和高级任务编排五个阶段；同时在 `/api/ai/mirador/interpret` 响应中并行增加 `tool_call` 结构，支持从标准工具调用反推既有 `action`，并让前端当前计划卡片显示工具调用名称。
- 验证结果：`python -m py_compile backend/app/routers/ai_mirador.py` 通过；`python -m pytest backend/tests/test_ai_mirador.py -q` 结果为 `2 passed, 3 skipped`，跳过原因是本机 PostgreSQL `localhost:5432` 未启动；`npm run build` 通过；`npm run test -- mirador-ai.spec.ts` 通过，`3 passed`。
- 备注：当前已经完成 Phase 1 的兼容式标准化，仍保留原有前端 `action` 执行链路；Docker Desktop 当前未连接，暂未能重启 compose 服务，待 Docker 可用后可直接重启后端/前端进行线上测试。

### 2026-05-01 - 同步前日志补齐与未提交改动收口
- 修改范围：人脸识别服务与 Celery 任务、影像记录上传/可见性、统一平台目录与详情契约、IIIF/Cantaloupe 配置、二维 profile 规则、输出契约测试、研究文档、RepoWiki 项目知识库、工作日志。
- 变更内容：为业务活动类影像记录接入可开关的人脸识别链路，新增本地/远程/自动 provider、运行时目录说明、pending/success/failed 元数据状态、识别结果回写 `main_person` 与前端展示；统一平台详情从复合 `resource_id` 过渡到 `source_system/source_id` 路径，补充二维与三维资源 actions、source record schema 和三维详情展示；将 Cantaloupe 调整为后端内部访问与前端代理访问分离，并补齐 `CANTALOUPE_INTERNAL_URL`；把二维 profile 必填字段集中到 `metadata_layers.py`，让影像记录校验和参考导入共用同一规则；同步补充 IIIF/BagIt 输出契约测试、研究线材料、实施边界清单、关键讨论问题、RepoWiki 生成文档和任务记忆层。
- 验证结果：已检查 `WORK_LOG.md` 未提交 diff 与主要代码 diff，确认新增/修改主题均有日志覆盖；执行敏感信息扫描，未发现真实 token 或私钥形态，仅命中示例密码、空 API key 字段和已有测试默认密码。本轮同步前未重新运行全量测试，沿用各条日志中记录的专项验证结果。
- 备注：本条用于把较长时间累积的本地未提交内容统一对齐到日志；`backend/runtime/face_recognition/README.md` 只提交运行时结构说明，模型、索引和识别库数据仍由 `.gitignore` 排除。
