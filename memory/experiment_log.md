# Experiment Log

## Round 1
- Date: 2026-03-08 to 2026-03-26
- Goal: 建立并稳定以数字资产为中心的二维主链路
- Data/sample scope: 二维影像资产、技术元数据提取、IIIF Manifest、Mirador 预览、BagIt 导出
- Setup: FastAPI + React + PostgreSQL + Celery + Redis + Cantaloupe + Docker Compose
- Observation: 系统已不只是上传下载工具，而是能把采集、校验、处理、访问、导出串成一条可演示工作流
- Result summary: 二维链路形成了当前最强的直接标准实现层，尤其是 IIIF 与 BagIt
- Success cases:
  - 资产上传、列表、详情、预览与下载
  - 动态 Manifest 生成与 Mirador 集成
  - BagIt 导出与 fixity 导向流程
- Failure cases:
  - 事件模型和长期保存表述仍多为隐含存在
  - 图像技术元数据 profile 仍未 formalize
- Paper-usable evidence: 可把二维主链路作为“最小可演示核心工作流”的直接案例

## Round 2
- Date: 2026-03-27
- Goal: 把统一平台、三维对象与版本管理引入真实实现，而不是停留在路线图
- Data/sample scope: 平台适配器、统一目录、统一详情、三维资源包、viewer 契约、测试模型
- Setup: 后端平台注册表与适配器机制；前端三维管理页与 `@google/model-viewer`
- Observation: 三维子系统从“单文件尝试”推进为“对象 + 版本 + 文件包 + viewer 契约”的可验证原型
- Result summary: MDAMS 从二维主链路扩展为多来源数字资源原型，统一平台层开始具有真实平台化意义
- Success cases:
  - 三维对象和版本管理
  - 多文件上传、包化管理和基础预览
  - 平台目录聚合二维与三维来源
- Failure cases:
  - 三维研究文档尚未完全跟上实现进展
  - 三维元数据 profile 与保存叙事仍需补强
- Paper-usable evidence: 可支撑“原型不是单一二维系统，而是可扩展数字资源底座”的论断

## Round 3
- Date: 2026-03-27 to 2026-03-29
- Goal: 强化权限、角色范围控制与利用申请闭环
- Data/sample scope: 登录、会话、角色权限、`collection_owner` 可见性、申请单、审批、交付导出
- Setup: 后端权限判断与前端菜单/页面裁剪；Playwright 回归覆盖不同角色
- Observation: 权限框架已经是实际行为控制，而非占位代码；申请流程也已形成端到端路径
- Result summary: 系统开始具备最小业务系统语义，而不是技术模块拼装
- Success cases:
  - 登录和角色播种
  - 菜单与资源可见性按权限变化
  - 申请车、审批与导出闭环
- Failure cases:
  - 规则治理与审计说明仍需更明确
  - 更复杂的审批与权限粒度仍未展开
- Paper-usable evidence: 可以支持“系统具备真实组织语义和责任范围控制”的论证

## Round 4
- Date: 2026-04-02
- Goal: 验证 AI 辅助 Mirador 交互是否能作为可追踪、可确认的实验性增强层
- Data/sample scope: Mirador AI 面板、自然语言控制、候选图搜索、比较模式、操作日志
- Setup: 前端 AI 面板 + 后端 AI 意图解析路由；使用 OpenAI 兼容接口
- Observation: AI 功能可用，但其最合理定位是辅助交互与日志化验证，不应盖过系统核心贡献
- Result summary: AI 面板形成了一个可研究的附加实验面，但不应取代主链路叙事
- Success cases:
  - 自然语言控制 Mirador 视图
  - 候选图确认机制
  - 比较模式切换与完整动作日志
- Failure cases:
  - 对外部模型服务仍有依赖
  - 研究表达中若处理不当，容易喧宾夺主
- Paper-usable evidence: 可作为“交互增强层”或“原型延展能力”章节的补充案例，而非论文主轴

## Round 5
- Date: 2026-04-08
- Goal: 把研究线中已经明确的两个优先边界推进到代码约束和 contract tests
- Data/sample scope: 二维 profile 最小必填规则、`ImageRecord` 提交校验、参考导入完整性检查、IIIF Manifest 输出、BagIt 导出
- Setup: 统一 `metadata_layers.py` 中的二维 profile 必填规则来源；为 `reference_import.py` 增加 `movable_artifact` 对 `object_number` 的提取；新增不依赖 PostgreSQL 的 IIIF / BagIt 输出层单元契约测试
- Observation: 当研究语义已经足够明确时，最有效的推进方式不是继续补文档，而是把规则和输出边界压进共享服务层与 tests
- Result summary: 二维 profile 规则不再分散在多处独立常量中，IIIF / BagIt 也从“有样本说明”进一步推进到“有明确 contract tests”
- Success cases:
  - `image_record_validation.py` 与 `reference_import.py` 现在共享同一组二维 profile 最小必填规则
  - `movable_artifact` 在参考导入时会优先提取 `object_number / 文物号`
  - 新增 IIIF Manifest 编码与 metadata 输出契约测试
  - 新增 BagIt tag files、fixity 和失败模式契约测试
- Failure cases:
  - `image_records` 的 PostgreSQL 集成测试在当前机器上因本地 5432 未启动而多数跳过
  - 跨子系统事件边界仍未进入 detail / test 层
- Paper-usable evidence: 可直接支持“系统已将最小 profile 约束与访问/导出表示边界推进到实现与验证层”的论述

## Round 6
- Date: 2026-04-17
- Goal: 为本机建立可复现的 MDAMS 原型依赖基线，并完成完整容器服务栈运行验收
- Data/sample scope: Homebrew 系统依赖、Python 后端 `.venv`、前端 Node 依赖、Playwright Chromium、Docker / Colima、Docker Compose 全栈、后端健康接口、前端代理、Cantaloupe 入口
- Setup: 使用清华 Homebrew bottles / PyPI 镜像、npmmirror NPM registry、华为云 Ubuntu cloud image 镜像、GitHub 代理多连接下载 Colima core 镜像，并为 Docker / Colima 配置 registry mirrors；本机 Node 固定到 Homebrew `node@20`
- Observation: Colima 官方 core 镜像必须匹配固定 SHA512，普通 Ubuntu cloud image 会被拒绝；通过 `aria2c` 多连接下载官方 Colima core 镜像后，Docker daemon 可用，完整 `docker compose up -d --build` 成功
- Result summary: 当前机器已经完成依赖安装、镜像构建、完整服务启动和基础访问验收；系统可通过前端 `http://localhost:3000` 进行测试
- Success cases:
  - `.venv` 内可导入 FastAPI、SQLAlchemy、OpenCV、ONNX Runtime、InsightFace、pyvips、Redis 和 Celery
  - `frontend` 依赖安装完成，`npm run build` 通过
  - Playwright Chromium 已下载到本机缓存
  - `docker compose config` 和本地 PostgreSQL compose 配置解析通过
  - PostgreSQL、Redis、libvips、ExifTool、ImageMagick、GraphicsMagick、FFmpeg、Java 均已在宿主机可用
  - Docker context `colima` 可用，Compose 全栈 6 个容器均为 `Up`
  - 后端 `/health`、`/ready` 返回 200，数据库和上传目录检查均为 healthy
  - 前端 `/` 返回 200，前端代理 `/api/auth/users` 返回测试用户列表
  - Cantaloupe `/` 返回 200，显示 Cantaloupe 5.0.6
  - 登录接口 `/auth/login` 可用，`system_admin / mdams123` 返回 session token 和权限上下文
  - Playwright Chromium 回归结果为 10 passed、1 skipped
- Failure cases:
  - Colima 默认 VM 镜像来自 GitHub release，直连超时；最终通过代理多连接下载解决
  - Playwright 中两个图像记录工作台测试曾因 mock 仍指向旧接口而失败，已更新为当前 `/api/image-records/sheets` 批次录入接口
- Paper-usable evidence: 可作为“原型复现实验环境准备与运行验收”记录，说明系统可以在本机通过容器栈复现，并具备前端、后端、数据库、Redis、Celery、IIIF 图像服务的最小运行证据

## Round 7
- Date: 2026-04-21
- Goal: 推进统一平台共享契约，使二维与三维来源在统一目录和统一详情中暴露一致的动作入口与源详情承载方式
- Data/sample scope: `UnifiedResourceSummary`、`UnifiedResourceDetail`、二维平台适配器、三维平台适配器、统一详情前端组件、平台目录与三维子系统契约测试
- Setup: 在后端 schema 中增加 `UnifiedResourceAction`；二维与三维适配器分别填充 `preview`、`platform_detail`、`source_detail`、`download` 等动作；二维继续提供 BagIt 导出动作；三维统一详情携带 `three_d_detail.v1` 源详情 JSON；前端统一详情按二维/三维源详情分支展示
- Observation: 统一平台最有价值的近期推进点不是扩全文检索或更多来源，而是先固化“统一视图如何表达可访问动作、源详情跳转和来源内部结构”
- Result summary: 平台层从“二维厚详情、三维薄摘要”推进为“二维与三维都满足同一统一详情承载契约”，同时保持来源系统分治和数据库模型不变
- Success cases:
  - `UnifiedResourceSummary` / `UnifiedResourceDetail` 现在都有共享 `actions` 字段
  - 二维资源暴露预览、统一详情、来源详情、下载和 BagIt 导出动作
  - 三维资源暴露预览、统一详情、来源详情和资源包下载动作
  - 三维统一详情返回 `source_record_type=three_d_detail`、`source_record_schema=three_d_detail.v1` 与三维源详情 JSON
  - 前端统一详情可以对二维生命周期和三维生产记录/文件结构做分支展示
- Failure cases:
  - 本机 PostgreSQL 5432 未运行，后端平台相关集成/契约测试被 pytest 标记为 skipped，尚未在真实数据库会话中执行断言
- Paper-usable evidence: 可说明 MDAMS 的统一平台不是通过强制统一存储表实现，而是通过来源适配器、共享摘要字段、共享动作契约和可识别的源详情载荷，形成“语义统一、来源分治”的研究型聚合视图

## Round 8
- Date: 2026-04-22
- Goal: 将统一平台详情入口从冒号拼接 ID 收口为显式 `source_system/source_id` 路由，降低编码和语义解析风险
- Data/sample scope: 平台详情路由、二维/三维统一详情 URL、前端统一详情入口、平台目录按钮、合同测试与 Playwright fixture
- Setup: 后端新增 `/api/platform/resources/{source_system}/{source_id}` 主路由，同时保留旧 `resource_id` 路由作兼容；前端统一目录与统一详情改为传递原子字段；测试 fixture 更新为新 detail URL
- Observation: 显式双参数路由在行为上更清晰，既能避免把可解析语义塞进单一字符串，也能保留现有 `id` 字段作为展示和兼容层
- Result summary: 统一平台详情入口完成了从“字符串分隔协议”到“显式来源定位协议”的迁移，减少后续多来源扩展时的解析歧义
- Success cases:
  - 平台详情主路由改为 `source_system/source_id`
  - 二维与三维统一详情的 `detail_url` 均指向新路由
  - 前端 `PlatformDirectory` / `UnifiedResourceDetail` 不再只传递拼接后的 `resourceId`
  - 旧的冒号格式仍可通过兼容路由访问
- Failure cases:
  - 后端平台集成测试仍因本机 PostgreSQL 未启动而跳过，尚未在真实 DB 连接下复核新旧路由并行行为
- Paper-usable evidence: 可用于说明 MDAMS 统一平台在演进时采用了“显式来源定位 + 兼容旧别名”的迁移策略，以降低契约变更带来的编码和语义风险

## Round 9
- Date: 2026-04-22
- Goal: 进一步收紧统一平台详情路由实现，避免单函数同时承载两种路径参数形态
- Data/sample scope: `backend/app/routers/platform.py` 新旧详情路由分离、前端测试路径匹配、后端语法检查、前端 build、合同测试
- Setup: 将平台详情拆成 `get_resource_by_source` 与 `get_resource` 两个明确入口，共享同一内部解析函数；前端测试 fixture 只保留新路径匹配
- Observation: 明确拆分主路由与兼容路由，比依赖一个带可选参数的处理函数更容易读，也更利于后续删除旧兼容入口
- Result summary: 统一平台详情现在具有更清晰的路由边界，主入口不再依赖字符串分隔解析，旧格式仅作为兼容层存在
- Success cases:
  - `source_system/source_id` 主路由和 `resource_id` 兼容路由都可用
  - 前端测试只验证新路由路径
  - `python3 -m compileall` 和前端 `npm run build` 均通过
- Failure cases:
  - 后端 contract tests 仍受本机 PostgreSQL 5432 未启动影响而跳过
- Paper-usable evidence: 可用于说明平台契约演进不仅包括字段收口，也包括路由职责拆分与兼容迁移策略

## Round 10
- Date: 2026-04-22
- Goal: 将 Mirador AI 搜索结果与候选上下文从 `resource_id` 语义转向显式 `source_system/source_id`
- Data/sample scope: `backend/app/routers/ai_mirador.py` 搜索结果结构、Mirador AI 请求上下文、前端 Mirador 候选展示、相关测试 fixture
- Setup: 在后端 `MiradorSearchResult` 和 `MiradorAIRequest` 中补充显式来源定位字段；前端 `MiradorViewer` 与 `MiradorAiPanel` 记录并展示来源系统与来源 ID；测试 mock 同步新字段
- Observation: Mirador 是高频交互面板，保留 `resource_id` 作为兼容别名有意义，但核心展示和请求上下文应优先使用显式来源定位，以避免把字符串拼接误当语义协议
- Result summary: Mirador AI 相关链路的语义收口更进一步，搜索结果、候选项和请求上下文都能在不拆字符串的情况下表达来源定位
- Success cases:
  - AI 搜索结果新增 `source_system` / `source_id`
  - 前端候选展示优先显示显式来源定位
  - `current_source_system` / `current_source_id` 进入 AI 请求上下文
  - 后端 `test_ai_mirador.py` 与前端 `mirador-ai.spec.ts` 的 fixture 已同步
- Failure cases:
  - 本机 PostgreSQL 仍未启动，相关数据库依赖测试继续被 skip
- Paper-usable evidence: 可用于说明语义收口不只发生在统一目录和详情路由，也延伸到了 AI 辅助搜索与比较界面

## Round 11
- Date: 2026-04-22
- Goal: 将显式来源定位继续传播到申请车路径，避免业务操作入口仍以拼接字符串作为默认表达
- Data/sample scope: `ApplicationCartItem`、`ApplicationCart` 视觉标签、`App` 加入申请车映射、前端 build、后端语法检查
- Setup: 在申请车条目中补充 `sourceSystem/sourceId`，并让展示优先使用 `sourceSystem/sourceId`；保留 `resourceId` 作为兜底值
- Observation: 当来源定位字段已经进入预览和搜索后，继续让申请车也使用同样的定位表示，能够减少界面之间的语义跳变
- Result summary: 申请车不再只展示拼接形式的 `resourceId`，而是优先显示显式来源系统与来源 ID
- Success cases:
  - `ApplicationCartItem` 增加显式来源定位字段
  - 申请车条目标签优先显示 `sourceSystem/sourceId`
  - `App` 从 Mirador 预览器接收并传递来源定位字段
  - `npm run build` 通过，`python3 -m compileall backend/app backend/tests` 通过
- Failure cases:
  - 后端 contract tests 仍未在 PostgreSQL 可用的环境里复跑
- Paper-usable evidence: 可用于说明显式来源定位不仅是检索和详情层的契约，也能延伸到具体业务操作入口和申请材料草稿层

## Round 12
- Date: 2026-04-22
- Goal: 将 `resource_id` 从新契约、新展示和新测试样例中移出，只保留旧路由/旧数据的兼容读取
- Data/sample scope: metadata layers、Mirador AI、申请车、资产详情、合同测试、前端 build、后端语法检查
- Setup: 删除 metadata layers 和三维 metadata 中的 `resource_id` 输出；Mirador AI 请求/响应不再携带 `resource_id`；申请车、Mirador 预览候选和资产详情展示优先使用 `source_system/source_id`；旧平台详情路由标记为 deprecated；主参考文档同步改为显式来源定位
- Observation: 当显式来源定位已经进入主链路后，继续保留旧字符串字段只会扩大歧义；把它退回兼容层后，整个 UI 和测试样例会更一致
- Result summary: 当前项目的活动代码路径已基本不再把 `resource_id` 当作主语义字段，只有少量兼容读取与路由别名仍保留
- Success cases:
  - metadata layers 和三维 metadata 不再输出 `resource_id`
  - Mirador AI 请求/结果只使用 `source_system/source_id`
  - 申请车、Mirador 预览、资产详情展示都优先显示显式来源定位
  - 旧平台详情路由已标记为 deprecated
  - `docs/02-架构设计/API_ROUTE_MAP.md`、`PLATFORM_SOURCE_ADAPTERS.md` 和研究型元数据说明已同步到 `source_system/source_id`
  - `python3 -m compileall backend/app backend/tests` 通过，`frontend` `npm run build` 通过，相关后端测试 10 passed / 6 skipped
- Failure cases:
  - PostgreSQL 5432 仍未启动，因此部分集成/契约测试继续 skip
- Paper-usable evidence: 可用于说明系统完成了从“兼容字段主导”到“显式来源定位主导”的契约收口，且兼容性被明确隔离在旧入口与历史数据层

## Round 13
- Date: 2026-04-22
- Goal: 将统一平台来源定位标准冻结为独立契约页，并让主文档显式引用
- Data/sample scope: `UNIFIED_PLATFORM_SOURCE_LOCATOR_CONTRACT.md`、`API_ROUTE_MAP.md`、`PLATFORM_SOURCE_ADAPTERS.md`、`tasks/current_task.md`、`memory/decisions.md`
- Setup: 新增来源定位契约页；在路由总览和平台适配器文档中补充引用；将任务状态切为已完成；补写决策与实验记录
- Observation: 当契约被单独命名、单独落文档、并被主文档引用后，后续新增来源或 UI 不容易再滑回旧字符串协议
- Result summary: 统一平台来源定位已从“实现上的显式字段”上升为“项目级稳定契约”
- Success cases:
  - 契约页明确了 `id`、`source_system/source_id`、主路由、兼容边界和展示规则
  - `API_ROUTE_MAP.md` 与 `PLATFORM_SOURCE_ADAPTERS.md` 已引用新契约页
  - 项目任务状态已更新为完成
  - 决策和实验日志已记录冻结结果
- Failure cases:
  - 尚未把历史镜像文档批量迁移到新契约页，只保留了主文档对齐
- Paper-usable evidence: 可用于说明 MDAMS 统一平台的契约演进不仅是代码迁移，也是“从实现约束到项目标准”的正式冻结过程

## Round 14
- Date: 2026-04-23
- Goal: 用共享词表和 contract tests 固化跨子系统最小事件边界
- Data/sample scope: `backend/app/services/event_boundary.py`、`backend/tests/test_event_boundary.py`、`backend/app/services/asset_detail.py`、`backend/app/services/three_d_production.py`
- Setup: 新增最小事件词表模块；用测试校验二维 lifecycle 步骤和三维 production event types；把跨子系统事件边界写回研究文档和论文叙述层
- Observation: 原型阶段最稳的做法不是先建统一事件表，而是先把词表、detail 输出和 contract tests 锁到同一边界上
- Result summary: 事件边界从“文档中的建议”推进为“代码里可引用、测试里可验证”的最小约束
- Success cases:
  - 新增 `event_boundary.py` 作为共享词表锚点
  - 新增 `test_event_boundary.py` 覆盖二维 lifecycle 与三维 production events
  - `python3 -m compileall backend/app backend/tests` 通过
  - `pytest backend/tests/test_event_boundary.py backend/tests/test_three_d_production.py backend/tests/test_routes_smoke.py -q` 通过 2 条，3 条因 PostgreSQL 不可用而 skip
- Failure cases:
  - 数据库依赖测试仍受本机 PostgreSQL 5432 未启动影响
- Paper-usable evidence: 可用于说明 MDAMS 现在具备可追踪、可解释的 proto-event boundary，而不是一个还没收口的零散 lifecycle 叙述

## Cross-Round Assessment
- 当前最强证据仍是二维主链路、统一平台、三维对象链路、权限范围控制和测试可验证性
- 当前已经开始把研究边界推进到共享规则与 contract tests，但跨子系统事件边界仍是下一步最关键缺口
