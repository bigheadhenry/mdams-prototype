# Prototype Design

## Modules
- 二维影像子系统：资产上传、列表、详情、预览图、IIIF Manifest、Mirador、下载与 BagIt 导出
- 图像记录工作流：`ImageRecord` 创建、提交、退回、待上传池、匹配、校验、重复检测
- 三维资源子系统：对象与版本、多文件资源包、viewer 契约、平台接入、Web 预览
- 统一平台层：来源适配器、注册表、统一目录、统一详情、按类型/状态/profile 过滤
- 认证与权限层：测试用户播种、登录/会话、角色权限、`collection_owner` 责任范围过滤
- 利用申请层：申请车、申请单、审批、交付导出
- AI 辅助层：Mirador 自然语言控制、候选资源搜索、操作日志链路
- 运行与基础设施：FastAPI、React、PostgreSQL、Celery、Redis、Cantaloupe、Docker Compose

## Technical Route
- 核心对象路线：以数字资产为中心连接文件、元数据、处理状态、访问表示和导出表示
- 前端路线：React 18 + Vite + TypeScript + Ant Design；二维预览使用 Mirador，三维预览使用 `@google/model-viewer`
- 后端路线：FastAPI 路由分区 + SQLAlchemy 模型 + 服务层；以 `assets`、`image-records`、`platform`、`three-d`、`applications` 为主要业务边界
- 异步与处理路线：Celery + Redis；支持大图像处理、衍生与转换任务
- 图像访问路线：Cantaloupe 提供 IIIF 图像服务，Mirador 使用 Manifest 和图像服务进行展示
- 聚合路线：通过平台适配器注册表，把二维与三维等来源汇总为统一资源目录与详情

## Current Stage
- Done:
  - 多条主链路已可演示：二维影像、ImageRecord 协作、申请交付、统一平台、三维对象管理、Mirador AI 辅助交互
  - 基础测试体系已建立：后端 `pytest`，前端 `Playwright`
  - 研究文档已具备：研究问题、概念模型、设计决策、标准映射、评估框架、论文大纲
- In progress:
  - 对象模型、PREMIS 事件模型和 metadata/profile 已有最小框架，但仍待进一步 formalize
  - IIIF、BagIt、OAIS 的细粒度支撑材料与 IIIF / BagIt 样本级证据已建立
  - 标准化演示主链路已建立，实施边界清单也已建立，且已开始进入实现或测试补强
  - 统一平台来源定位契约已冻结，但跨子系统最小事件边界仍待进入 detail / test 层
  - 长期保存与治理相关表达仍未形成完整体系
- Next:
  - 继续把跨子系统事件边界向更明确的保存/审计语义推进，必要时再决定是否需要统一持久化表
  - 为三维最小 profile 建立工作流级 contract tests

## Confirmed Strengths
- 仓库不是纸面设计，已有真实代码、真实部署、真实回归测试
- 主链路可解释性较强，适合演示与论文表达
- 标准引入方式相对克制，避免了“全都支持”的过度宣称
- 平台适配器、角色范围控制、三维子系统已经形成继续扩展的工程底座

## Known Constraints
- 文档数量多，若缺少稳定 `memory/` 和 `tasks/` 层，容易继续漂移
- `Asset`、`ImageRecord`、藏品对象、3D 对象/版本、导出包之间的统一对象模型仍需收口
- 当前标准到实现映射未完全反映三维子系统和近期实现进展
- 长期保存、事件审计、图像技术元数据与三维 profile 仍缺更强 formalization
- 二维 profile 最小规则和 IIIF / BagIt 输出层 contract tests 已补，但跨子系统事件边界仍未进入实现层
- 项目应保持研究原型边界，避免过早进入生产级工程化扩张
