# PREMIS 事件映射（细粒度落地版）

## 目的

本文档用于把 MDAMS Prototype 当前核心工作流中的操作与 PREMIS 的事件思路进行细粒度映射，并尽量向“可实施的事件模型草案”靠拢。

它的目标不是宣称系统已经完整实现 PREMIS，而是为后续落地提供一个中间层规范，帮助回答以下问题：
- 当前系统里哪些动作应该被记录为事件；
- 这些事件最小应记录哪些字段；
- 一个事件在系统里应如何区分开始、完成、失败、重试等状态；
- 后续如果要把处理链路正式化，最应该先落哪些事件。

---

## 一、当前使用原则

### 1. 不追求一次性完整 PREMIS 实现
当前目标是建立一个**最小可落地、能支撑工作流追踪、保存意识和后续研究表达**的事件层。

### 2. 先围绕核心主链路建模
本轮只优先覆盖当前最重要的工作流：
- 上传 / 接收；
- ingest；
- fixity；
- metadata extraction；
- conversion；
- manifest generation；
- export。

### 3. 事件必须与资产对象绑定
MDAMS 当前以数字资产（Asset）为核心对象，因此事件应优先关联：
- `asset_id`
- `file_id` 或文件路径/文件标识
- 事件时间
- 事件类型
- 事件状态
- 执行代理（agent）
- 结果摘要

### 4. 一条事件不等于一条日志
日志可以很碎，但事件应是“具有业务意义和保存意义的动作记录”。

---

## 二、建议的最小事件记录结构

建议后续系统中每条事件至少具备以下字段：

| 字段 | 含义 | 是否建议必填 |
|---|---|---|
| `event_id` | 事件唯一标识 | 是 |
| `event_type` | 事件类型 | 是 |
| `event_status` | 事件状态（started/completed/failed/retried/skipped/cancelled） | 是 |
| `event_time` | 事件发生时间 | 是 |
| `asset_id` | 关联资产 ID | 是 |
| `file_id` | 关联文件 ID，如有 | 否 |
| `object_role` | 对象角色（原始文件/衍生文件/访问表示/导出包等） | 建议 |
| `agent_type` | 执行主体类型（system/user/worker/service） | 建议 |
| `agent_id` | 执行主体标识 | 建议 |
| `outcome` | 事件结果摘要 | 建议 |
| `outcome_detail` | 详细结果或错误信息 | 否 |
| `task_id` | 异步任务 ID，如有 | 否 |
| `related_event_id` | 关联前序事件 | 否 |
| `checksum_type` | 如事件涉及校验值 | 否 |
| `checksum_value` | 如事件涉及校验值 | 否 |
| `metadata_profile` | 如事件涉及元数据提取 | 否 |
| `software_name` | 执行软件/服务名 | 否 |
| `software_version` | 执行软件版本 | 否 |
| `source_path` | 输入对象路径 | 否 |
| `target_path` | 输出对象路径 | 否 |
|

---

## 三、建议的统一事件状态词表

为避免后续事件语义混乱，建议统一使用以下状态：

| 状态 | 含义 |
|---|---|
| `started` | 事件已开始 |
| `completed` | 事件成功完成 |
| `failed` | 事件执行失败 |
| `retried` | 事件被重新执行 |
| `skipped` | 事件按规则被跳过 |
| `cancelled` | 事件被取消 |

说明：
- 如果系统想保持简洁，第一阶段也可只启用 `started / completed / failed`；
- 但从落地角度看，`retried` 和 `skipped` 对异步任务链非常有价值。

---

## 四、MDAMS 核心工作流事件映射

以下按当前主链路给出建议事件集合。

### 1. 文件上传 / 接收阶段

#### 1.1 `file_receive`
**含义**：系统开始接收一个用户上传或导入的文件对象。

**建议状态**：
- `started`
- `completed`
- `failed`

**建议记录要点**：
- 触发用户或来源；
- 原始文件名；
- 输入来源（上传/API/导入）；
- 接收后的临时路径或目标路径；
- 文件大小与 MIME type（如已知）。

**落地意义**：
这是原始数字对象进入系统边界的起点事件。

---

#### 1.2 `asset_register`
**含义**：系统为接收到的对象创建或登记资产记录。

**建议状态**：
- `started`
- `completed`
- `failed`

**建议记录要点**：
- 新建还是更新；
- 对应 `asset_id`；
- 关联的文件标识；
- 初始状态值。

**落地意义**：
此事件把“文件进入系统”提升为“资产进入系统管理”。

---

### 2. Ingest 阶段

#### 2.1 `ingest_start`
**含义**：系统正式开始对资产执行 ingest 流程。

**建议状态**：
- `started`
- `completed`
- `failed`

**建议记录要点**：
- ingest 触发方式；
- 关联资产；
- 输入对象；
- 使用的 ingest 流程或规则。

---

#### 2.2 `ingest_validate`
**含义**：ingest 过程中的基础校验动作。

**建议状态**：
- `started`
- `completed`
- `failed`
- `skipped`

**建议记录要点**：
- 校验范围（文件存在性、格式合法性、基础字段完整性等）；
- 失败原因；
- 是否阻断后续流程。

---

#### 2.3 `ingest_complete`
**含义**：一次 ingest 主流程结束。

**建议状态**：
- `completed`
- `failed`

**建议记录要点**：
- ingest 总体结果；
- 是否触发后续任务；
- 生成了哪些后续对象或任务。

---

### 3. Fixity 阶段

#### 3.1 `fixity_generate`
**含义**：为对象生成校验值。

**建议状态**：
- `started`
- `completed`
- `failed`
- `retried`

**建议记录要点**：
- checksum 算法（当前可先以 SHA256 为主）；
- 目标对象；
- 校验值；
- 执行软件/服务；
- 输入路径。

**落地意义**：
这是最核心的保存导向事件之一。

---

#### 3.2 `fixity_verify`
**含义**：对已有校验值进行验证。

**建议状态**：
- `started`
- `completed`
- `failed`
- `skipped`

**建议记录要点**：
- 比对基准；
- 验证结果（match / mismatch）；
- 如失败，说明技术原因还是内容不一致。

---

### 4. 元数据提取阶段

#### 4.1 `metadata_extract`
**含义**：从文件或资产中提取技术/结构/基础元数据。

**建议状态**：
- `started`
- `completed`
- `failed`
- `retried`

**建议记录要点**：
- 提取工具；
- 提取对象；
- 元数据类型；
- 输出位置；
- 提取结果摘要。

**落地意义**：
这是后续 NISO Z39.87 对齐的重要切入口。

---

#### 4.2 `metadata_normalize`
**含义**：对提取结果进行标准化、清洗或结构整理。

**建议状态**：
- `started`
- `completed`
- `failed`
- `skipped`

**建议记录要点**：
- 使用的字段映射规则；
- 是否写回资产元数据；
- 是否丢弃部分原始字段。

---

### 5. 转换 / 异步处理阶段

#### 5.1 `conversion_request`
**含义**：系统为某对象发起转换任务。

**建议状态**：
- `started`
- `completed`
- `failed`

**建议记录要点**：
- 转换类型（如 PSB → BigTIFF）；
- 输入对象；
- 目标格式；
- task_id。

---

#### 5.2 `conversion_execute`
**含义**：异步 worker 真正执行转换。

**建议状态**：
- `started`
- `completed`
- `failed`
- `retried`
- `cancelled`

**建议记录要点**：
- worker 标识；
- 软件与版本；
- 输入路径与输出路径；
- 错误信息；
- 资源消耗（如后续愿意记录）。

---

#### 5.3 `derivative_register`
**含义**：转换产物被登记为衍生对象或新的文件关联。

**建议状态**：
- `started`
- `completed`
- `failed`

**建议记录要点**：
- 产物文件标识；
- 产物角色（衍生/访问/规范化文件）；
- 与原对象关系。

---

### 6. IIIF / 访问表示阶段

#### 6.1 `manifest_generate`
**含义**：系统生成 IIIF Manifest。

**建议状态**：
- `started`
- `completed`
- `failed`
- `retried`

**建议记录要点**：
- 关联资产；
- 关联图像/文件对象；
- 生成的 manifest URL 或标识；
- 所用 profile/模板版本。

---

#### 6.2 `access_derivative_prepare`
**含义**：为访问层准备预览图、查看器兼容对象或相关访问资源。

**建议状态**：
- `started`
- `completed`
- `failed`
- `skipped`

**建议记录要点**：
- 访问表示类型；
- 目标文件；
- 与查看器/服务链的关系。

---

### 7. 导出 / 打包阶段

#### 7.1 `export_request`
**含义**：用户或系统发起导出请求。

**建议状态**：
- `started`
- `completed`
- `failed`

**建议记录要点**：
- 导出类型（BagIt ZIP 等）；
- 导出范围；
- 请求主体。

---

#### 7.2 `package_generate`
**含义**：系统实际生成导出包。

**建议状态**：
- `started`
- `completed`
- `failed`
- `retried`

**建议记录要点**：
- 包类型；
- 输出路径；
- 包含对象数；
- 是否附带 manifest/tag files。

---

#### 7.3 `export_deliver`
**含义**：导出包被交付给下载端或外部消费方。

**建议状态**：
- `started`
- `completed`
- `failed`

**建议记录要点**：
- 交付方式；
- 下载链接或交付目标；
- 有效期或访问限制（如有）。

---

## 五、建议优先落地的事件清单

如果不想一次性做太多，建议按以下优先级实施：

### 第一优先级（必须先做）
- `asset_register`
- `ingest_start`
- `fixity_generate`
- `metadata_extract`
- `conversion_execute`
- `manifest_generate`
- `package_generate`

这些事件已经足以支撑：
- 资产进入系统的主链路；
- 保存导向的基本证据；
- 研究线中的 proto-PREMIS 论证；
- 运维排查中的关键路径追踪。

### 第二优先级（建议很快补上）
- `fixity_verify`
- `metadata_normalize`
- `derivative_register`
- `export_request`
- `export_deliver`

### 第三优先级（按复杂度再做）
- `ingest_validate`
- `conversion_request`
- `access_derivative_prepare`

---

## 六、与 PREMIS 概念的对应关系

虽然当前文档更偏落地，但仍建议保留 PREMIS 语义对应，以便未来研究与实现统一。

| MDAMS 字段/概念 | PREMIS 对应理解 |
|---|---|
| `asset_id` / `file_id` | Object |
| `event_type` / `event_status` / `event_time` | Event |
| `agent_type` / `agent_id` | Agent |
| 导出授权、访问限制（未来） | Rights |
| checksum / format / environment info | Object characteristics / environment |

当前最关键的是先把 **Object-Event-Agent** 三者建立起来；Rights 可以后续逐步增强。

---

## 七、对系统落地的建议结构

如果后续要真正实现，建议采用以下策略：

### 方案 A：独立事件表
新增独立 `events` 表，字段尽量贴近本文结构。

**优点**：
- 语义清晰；
- 便于查询；
- 便于后续做审计、工作流追踪和研究导出。

### 方案 B：先从任务日志中抽象事件层
先不完全改数据库，而是从 Celery 任务、后端处理逻辑中抽象出“事件写入点”。

**优点**：
- 改动小；
- 能快速落地；
- 适合原型阶段。

### 当前建议
建议优先采用：

> **先在现有工作流关键节点插入事件写入点，再逐步收敛为独立事件模型。**

也就是说，先做“事件记录能力”，再做“事件模型重构”。

---

## 八、当前结论

从落地角度看，MDAMS 当前最值得推进的 PREMIS 化方向，不是一次性全面实现 PREMIS，而是：

1. 先识别哪些动作必须成为事件；
2. 先统一事件类型与状态词表；
3. 先把核心链路的事件记录下来；
4. 再逐步把这些事件提升为更正式的保存元数据结构。

因此，当前最务实的判断是：

> MDAMS 应先建设一个 **PREMIS-informed event layer（受 PREMIS 启发的事件层）**，用来连接资产对象、处理流程、保存导向与后续标准化建模。

这会比空谈“全面实现 PREMIS”更实际，也更适合当前原型阶段。
