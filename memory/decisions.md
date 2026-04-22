# Decisions

## Decision 1
- Date: 2026-03-08
- Topic: 优先稳定可演示的核心工作流
- Chosen option: 围绕采集、校验、处理、访问、导出的主链路推进原型，而不是继续横向扩张功能面
- Alternatives considered:
  - 优先补更多外围业务模块
  - 优先做 UI 层美化
  - 优先追求更完整生产级工程化
- Rationale: 研究型原型首先需要可解释、可演示、可评估
- Impact on prototype: 主链路优先级高于零散功能扩张
- Impact on writing: 论文结构可以围绕主链路展开，而不是功能清单

## Decision 2
- Date: 2026-03-09
- Topic: 以数字资产作为核心管理对象
- Chosen option: 采用 `Asset` 作为系统核心对象，用其连接文件、元数据、状态、访问表示和导出表示
- Alternatives considered:
  - 以单个文件为中心
  - 以完整藏品管理对象为中心
  - 以项目/批次为中心
- Rationale: 资产模型最符合当前实现事实，也最适合连接研究问题与系统架构
- Impact on prototype: 功能和数据模型更容易围绕统一对象组织
- Impact on writing: 有利于形成清晰概念模型和贡献表述

## Decision 3
- Date: 2026-03-09
- Topic: 采用选择性标准对齐
- Chosen option: IIIF 和 BagIt 作为直接实现层；OAIS 作为概念解释层；PREMIS 和 NISO Z39.87 作为部分对齐层
- Alternatives considered:
  - 宣称全面标准合规
  - 完全不谈标准
  - 只保留单一标准路径
- Rationale: 在原型阶段兼顾工程可行性、研究解释力和边界诚实
- Impact on prototype: 降低过度实现和过度宣称风险
- Impact on writing: 可以清楚区分“已实现”“部分对齐”“概念借鉴”“未来扩展”

## Decision 4
- Date: 2026-03-27
- Topic: 把三维能力纳入同一 MDAMS 原型，而不是当作独立演示分支
- Chosen option: 通过平台适配器、统一目录与对象/版本模型，将三维资源纳入统一资源框架
- Alternatives considered:
  - 三维独立成单独子项目
  - 先不进入平台聚合层
  - 仅保留三维上传 demo
- Rationale: 三维子系统已经具备对象、版本、文件包和 viewer 契约，纳入统一框架更符合“数字资源底座”定位
- Impact on prototype: 平台聚合更具真实价值，但也提高了对象模型澄清的必要性
- Impact on writing: 论文可以从单一图像原型上升为多来源数字资源管理案例

## Decision 5
- Date: 2026-04-08
- Topic: 建立稳定 `memory/` 与 `tasks/` 层
- Chosen option: 从 `docs/` 中抽离出一套轻量、长期维护的研究记忆与任务文件
- Alternatives considered:
  - 继续只依赖现有 `docs/` 文档树
  - 只在聊天记录中维护上下文
  - 等文档再次漂移后再补
- Rationale: 当前项目已经同时包含实现、研究和路线图，如果没有稳定层，后续最容易出现文档漂移和任务上下文断裂
- Impact on prototype: 后续开发与研究可以围绕明确记忆层持续推进
- Impact on writing: 更容易把实现事实转化为论文材料，并保持持续更新

## Decision 6
- Date: 2026-04-08
- Topic: 二维 profile 最小必填规则采用共享服务层单一来源
- Chosen option: 将二维 profile 的最小必填字段收口到 `metadata_layers.py`，并让提交校验与参考导入完整性检查共同引用
- Alternatives considered:
  - 继续在 `image_record_validation.py` 与 `reference_import.py` 维护两套独立常量
  - 直接把完整 profile 逻辑迁入数据库或 schema 层
  - 暂时只在文档中说明，不改代码
- Rationale: 当前不一致已经是实现问题而不是解释问题；共享规则来源是最小且最稳的推进方式
- Impact on prototype: `ImageRecord` 提交校验和参考导入完整性判断的一致性提高
- Impact on writing: “最小 profile” 的研究表述更接近系统真实行为

## Decision 7
- Date: 2026-04-08
- Topic: IIIF / BagIt 继续保持派生输出对象，并通过 contract tests 固化边界
- Chosen option: 不把 IIIF Manifest 或 BagIt ZIP 变成第一类持久化对象，而是为其输出字段、文件选择、fixity 和失败模式增加 contract tests
- Alternatives considered:
  - 为访问表示和导出表示建立独立持久化对象模型
  - 继续只依赖样本级文档说明，不补测试
  - 先做更复杂的输出治理层再回头补测试
- Rationale: 当前输出行为已经稳定，最有价值的下一步是固化边界，而不是增加结构复杂度
- Impact on prototype: 访问/导出表示的行为回归更稳，且不引入不必要的模型膨胀
- Impact on writing: 可以更准确地把 IIIF / BagIt 描述为“可重复生成的派生输出表示”

## Decision 8
- Date: 2026-04-10
- Topic: 跨子系统事件边界先落 detail / test 层，而不是先建统一事件表
- Chosen option: 先用 detail 层事件摘要、三维现有生产记录和 contract tests 收口事件边界，再决定是否需要跨子系统统一持久化
- Alternatives considered:
  - 直接引入统一事件表
  - 继续只在文档中讨论，不进入实现
  - 让各子系统继续各自演化事件表达
- Rationale: 当前系统中“状态”“事件”“输出结果”仍在不同层级；先统一语义和验证边界，比先统一存储更稳
- Impact on prototype: 可以在不做数据库大改的前提下继续增强治理与保存语义
- Impact on writing: 有助于把系统表述为“已有最小事件边界”，而不是过度宣称已有统一事件审计体系

## Decision 9
- Date: 2026-04-17
- Topic: 本机依赖安装和容器运行优先采用国内镜像与可校验的本地镜像缓存
- Chosen option: 先完成 Homebrew、PyPI、NPM、Playwright、Docker CLI / Compose、PostgreSQL、Redis 和图像处理依赖安装；随后使用多连接代理下载并校验 Colima 官方 core 镜像，完成 Docker daemon 初始化和完整 Compose 栈运行验收
- Alternatives considered:
  - 使用普通 Ubuntu cloud image 初始化 Colima
  - 继续使用单连接低速 GitHub 代理下载 Colima 镜像
  - 停留在依赖安装和构建验证，不继续启动完整容器栈
  - 只安装项目直接语言依赖，不处理 Docker / 图像处理 / IIIF 相关系统依赖
- Rationale: Colima 会校验官方 core 镜像 SHA512，普通 Ubuntu cloud image 不可替代；多连接下载既能利用国内可达代理，又能保留镜像完整性校验
- Impact on prototype: 当前机器可以通过 Docker Compose 运行完整 MDAMS 原型服务栈，支持前端测试和后续演示
- Impact on writing: 环境记录可以清楚说明“依赖安装、镜像构建、服务运行、访问验收”的完整复现链路，而不是仅说明依赖就绪

## Decision 10
- Date: 2026-04-21
- Topic: 统一平台共享契约先落在动作与源详情承载，而不是统一存储模型
- Chosen option: 在 `UnifiedResourceSummary` / `UnifiedResourceDetail` 中增加统一 `actions` 契约，并让二维与三维统一详情都显式携带 `source_record_type`、`source_record_schema` 和 JSON 化 `source_record`
- Alternatives considered:
  - 为二维与三维建立统一数据库表或统一持久化资源模型
  - 继续让三维统一详情只返回薄摘要
  - 仅补文档，不把契约推进到代码和测试
- Rationale: 当前统一平台最需要稳定的是“跨来源可展示、可跳转、可访问、可下载”的共享行为，而不是提前把不同来源压进同一存储模型
- Impact on prototype: 统一平台详情可以承载二维和三维源详情，平台目录与详情的动作入口更一致
- Impact on writing: 可将统一平台表述为“语义统一、来源分治”的聚合视图层，并说明其通过共享动作契约而非统一数据库表实现多来源整合

## Decision 11
- Date: 2026-04-22
- Topic: 平台详情路由改为显式 `source_system/source_id`
- Chosen option: 将统一平台详情主路由改为 `/api/platform/resources/{source_system}/{source_id}`，同时保留旧的 `resource_id` 冒号格式作为兼容入口
- Alternatives considered:
  - 继续只使用 `image_2d:1` 这类拼接 ID
  - 直接移除旧路由并强制全量迁移
  - 改用查询参数而不是路径参数
- Rationale: 显式双参数路由能减少编码和语义解析风险，同时兼顾现有前端与测试的平滑迁移
- Impact on prototype: 平台详情入口不再依赖冒号分隔符作为主解析规则，后续新增来源也更容易接入
- Impact on writing: 可以把统一平台描述为“opaque platform identifier + explicit source locator”的组合，而不是依赖字符串切分的 ID 协议

## Decision 12
- Date: 2026-04-22
- Topic: Mirador AI 搜索结果和候选上下文补充显式来源定位字段
- Chosen option: 在 `MiradorSearchResult` 与 Mirador AI 请求上下文中加入 `source_system`、`source_id`，并让前端候选展示优先使用显式来源定位
- Alternatives considered:
  - 继续只用 `resource_id` 作为候选展示和 AI 上下文
  - 只在前端做字符串拆分，不改后端契约
  - 直接删除 `resource_id` 并强制全量迁移
- Rationale: Mirador 是高交互面板，最容易把别名当语义用；把来源定位显式化能减少后续比较、检索和应用加入流程里的歧义
- Impact on prototype: AI 搜索结果更容易与统一平台、应用加入和后续多来源扩展对接
- Impact on writing: 可作为“交互增强层也遵循显式来源定位契约”的证据，说明语义收口不仅发生在目录层，也发生在 AI 辅助层

## Decision 13
- Date: 2026-04-22
- Topic: 申请车展示优先使用显式来源定位
- Chosen option: 在 `ApplicationCartItem` 中补充 `sourceSystem` / `sourceId`，并让申请车条目优先展示 `sourceSystem/sourceId`，`resourceId` 只做兼容回退
- Alternatives considered:
  - 继续只显示 `resourceId`
  - 直接删除 `resourceId`
  - 只在 Mirador 中做收口，申请车保持现状
- Rationale: 申请车属于后续业务操作入口，若继续展示拼接 ID，会把兼容别名延长成默认表达；显式定位更便于审核、导出和未来多来源申请
- Impact on prototype: 从预览、搜索到申请车的路径都更一致，后续可把定位字段继续向导出和审批材料传播
- Impact on writing: 可以把“应用加入”描述为显式来源定位的业务化落点，而不是仅仅附着在预览器上的临时字段

## Decision 14
- Date: 2026-04-22
- Topic: 将 `resource_id` 彻底降级为历史兼容层，移出新契约和新展示
- Chosen option: 从 metadata layers、Mirador AI 请求/结果、申请车、资产详情渲染与相关测试样例中移除 `resource_id`，只保留旧路由和少量兼容读取作为弃用入口
- Alternatives considered:
  - 继续在新响应里保留 `resource_id` 作为默认展示字段
  - 直接删除所有兼容入口并强制全量迁移
  - 只在文档里说明弃用但不改代码
- Rationale: 语义收口只有在新接口、新 UI 和测试样例都统一之后才算真正完成；兼容入口可以保留，但不能再作为默认表达
- Impact on prototype: 新输出现在优先使用 `source_system/source_id`，老字段不会再污染页面与新测试样例
- Impact on writing: 可将 `resource_id` 定义为历史兼容命名，而不是统一平台的主定位协议

## Decision 15
- Date: 2026-04-22
- Topic: 冻结统一平台来源定位契约
- Chosen option: 将 `id + source_system/source_id` 定义为统一平台的主契约，并以独立文档固定；`resource_id` 仅保留旧路由和历史数据兼容
- Alternatives considered:
  - 继续让多个文档各自描述路由和字段
  - 把 `resource_id` 作为主契约写进新标准页
  - 只在聊天里口头确认，不形成文档
- Rationale: 契约只有被单独冻结、被主文档引用、被实现和测试共同遵守，才算真正稳定
- Impact on prototype: 后续所有新来源、新 UI、新测试都可以直接按显式来源定位接入
- Impact on writing: 统一平台现在可以被写成“显式来源定位契约下的聚合视图”，而不是“字符串拼接 ID 的聚合器”

## Decision 16
- Date: 2026-04-23
- Topic: 用共享词表和 contract tests 固化跨子系统最小事件边界
- Chosen option: 新增 `backend/app/services/event_boundary.py` 作为最小事件词表锚点，并用测试覆盖二维 lifecycle、三维 production records 和共享事件语义
- Alternatives considered:
  - 直接设计统一事件表
  - 只保留文档定义，不进入测试
  - 继续让各子系统各自表达事件术语
- Rationale: 原型阶段最需要的是可验证的最小边界，而不是额外持久化复杂度；共享词表能把实现、测试和论文叙述拉到同一层
- Impact on prototype: 事件边界从文档约束推进到可 import、可测试的代码约束
- Impact on writing: 可以更稳地把系统描述为具有 proto-event boundary 的 preservation-aware 原型

## Current Open Decisions
- 是否要把 `ImageRecord`、藏品对象、3D 对象/版本正式纳入统一概念模型中的二级实体体系
- 是否要引入最小 PREMIS 风格事件模型作为后续治理/保存层基线
- 二维图像技术元数据 profile 和三维元数据 profile 是否分别定义最小可行版本
