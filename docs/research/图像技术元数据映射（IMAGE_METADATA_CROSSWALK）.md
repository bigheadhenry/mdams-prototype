# 图像技术元数据 Crosswalk（面向 NISO Z39.87）

## 目的

本文档用于把 MDAMS Prototype 当前图像导向工作流中的技术元数据能力，与 NISO Z39.87《Data Dictionary – Technical Metadata for Digital Still Images》的核心关注点建立一个**最小可实施 crosswalk**。

它的目标不是宣称系统已经完整实现 Z39.87，而是回答以下问题：
- 当前系统已经在处理哪些图像技术信息；
- 这些信息可以大致对应到 Z39.87 的哪些类别；
- 当前仍缺哪些重要部分；
- 如果未来要 formalize，应该先落哪一个最小 profile。

---

## 一、当前使用原则

### 1. 先做“最小可实施映射”，不追求一次性完整标准覆盖
Z39.87 是一个正式技术元数据标准，但 MDAMS 当前仍处于原型阶段。

因此，本文件采用的策略是：
- 先从当前工作流中已经明显存在的图像技术信息出发；
- 先建立类别级和字段级的近似映射；
- 再识别哪些部分以后值得 formalize。

### 2. 以 still image 场景为优先
当前 MDAMS 最适合和 Z39.87 对接的对象，是：
- 静态图像主文件；
- 大图像文件；
- 访问/衍生图像；
- 与 IIIF 访问链直接相关的图像对象。

### 3. 不把任意 metadata JSON 自动当作标准化元数据
当前系统已存在 `metadata JSON` 字段与图像元数据提取能力，但这不等于已经形成了标准 profile。

因此，本文件区分：
- 当前可能已提取/已掌握的信息；
- 当前尚未标准化表达的信息；
- 未来值得纳入 profile 的信息。

---

## 二、当前 MDAMS 中已知与图像技术元数据相关的能力

根据当前项目事实与研究文档，已经确认的相关能力包括：
- 图像元数据提取；
- 大图像处理；
- PSB → BigTIFF 异步转换；
- IIIF 导向访问表示；
- 基于 Cantaloupe 的图像服务；
- 与资产记录绑定的文件名、路径、大小、MIME type、metadata JSON；
- fixity 生成/校验。

这说明当前系统并不是“只有文件上传”，而是已经具备了图像技术对象识别与处理的基础。

---

## 三、建议采用的最小图像技术元数据 profile

如果后续要先做一个最小可实施 profile，建议至少覆盖以下字段组：

### A. 对象标识与基本文件信息
- `asset_id`
- `file_id`
- `filename`
- `relative_path`
- `file_size`
- `mime_type`
- `format_name`
- `format_version`（如可得）

### B. 图像技术特征
- `image_width`
- `image_height`
- `color_space`
- `bit_depth`
- `compression`
- `orientation`（如可得）
- `resolution_x` / `resolution_y`（如可得）
- `resolution_unit`（如可得）

### C. 对象角色与处理关系
- `object_role`（原始/规范化/衍生/访问）
- `source_object_id`
- `derivation_type`
- `conversion_software`
- `conversion_time`

### D. 保存导向技术信息
- `checksum_type`
- `checksum_value`
- `file_created_time`（如可得）
- `metadata_extracted_time`

### E. 访问链相关信息
- `iiif_enabled`
- `iiif_source_object`
- `access_derivative_path`
- `manifest_id` 或 `manifest_url`

---

## 四、类别级 Crosswalk

下面先做类别级映射，帮助把当前系统的技术信息与 Z39.87 的关注点对上。

| MDAMS 当前信息类别 | 当前实现状态 | 对应的 Z39.87 关注方向 | 当前判断 |
|---|---|---|---|
| 文件名、路径、大小、MIME type | 已确认存在 | basic digital object information / file information | 已有基础，但仍偏实现字段 |
| 格式信息 | 可能部分存在 | format designation / format registry information | 值得 formalize |
| 图像尺寸信息 | 很可能在图像提取中存在 | image technical characteristics | 应优先纳入最小 profile |
| 色彩/位深/压缩 | 可能部分存在 | image encoding / technical image characteristics | 需要盘点实际提取字段 |
| 分辨率信息 | 可能存在 | image resolution-related characteristics | 需要确认 |
| checksum/fixity | 已确认存在 | 虽非 Z39.87 唯一核心，但属于关键技术/管理信息 | 应保留并与保存层联动 |
| 衍生/转换关系 | 当前工作流中明显存在 | transformation / relationship context（近似对应） | 值得加强 |
| IIIF 访问相关信息 | 已明显存在 | 不直接属于 Z39.87 核心，但与图像对象技术使用密切相关 | 应作为扩展字段处理 |

---

## 五、字段级最小 Crosswalk（工作草案）

> 说明：由于当前仓库中的图像元数据提取字段尚未逐项复核，本表是“当前研究阶段的最小工作草案”，用于指导后续正式字段盘点。

| MDAMS 候选字段 | 当前状态 | 可近似对应的 Z39.87 类别/含义 | 建议处理 |
|---|---|---|---|
| `filename` | 已存在 | 对象基本识别信息 | 保留 |
| `relative_path` | 已存在 | 文件定位/管理信息 | 保留 |
| `file_size` | 已存在 | file size | 保留 |
| `mime_type` | 已存在 | format-related basic info | 保留 |
| `format_name` | 推测可提取 | format designation | 应纳入 |
| `format_version` | 可能未稳定 | format designation / version | 可选纳入 |
| `image_width` | 预期可提取 | image dimensions | 应纳入 |
| `image_height` | 预期可提取 | image dimensions | 应纳入 |
| `color_space` | 可能可提取 | image color characteristics | 建议纳入 |
| `bit_depth` | 可能可提取 | image encoding / sample precision | 建议纳入 |
| `compression` | 可能可提取 | compression / encoding characteristics | 建议纳入 |
| `resolution_x` | 可能可提取 | spatial resolution | 可优先纳入 |
| `resolution_y` | 可能可提取 | spatial resolution | 可优先纳入 |
| `resolution_unit` | 可能可提取 | resolution unit | 可选纳入 |
| `orientation` | 可能可提取 | image orientation | 可选纳入 |
| `checksum_type` | 已存在 | 管理/技术补充信息 | 保留 |
| `checksum_value` | 已存在 | 管理/技术补充信息 | 保留 |
| `object_role` | 建议新增或显式化 | 对象角色语境 | 应显式化 |
| `source_object_id` | 建议新增 | 对象关系/衍生来源 | 应显式化 |
| `conversion_software` | 当前应可记录 | 生成/转换环境信息 | 建议纳入 |
| `conversion_time` | 当前应可记录 | 处理时间信息 | 建议纳入 |
| `manifest_url` | 已存在或可构造 | 非 Z39.87 核心字段，属访问扩展信息 | 作为扩展字段 |

---

## 六、当前最值得优先 formalize 的字段

如果现在不想一次性做很多，建议优先把以下字段先稳定下来：

### 第一优先级（最小 still image profile）
- `filename`
- `file_size`
- `mime_type`
- `format_name`
- `image_width`
- `image_height`
- `bit_depth`
- `compression`
- `checksum_type`
- `checksum_value`

### 第二优先级（增强 profile）
- `color_space`
- `resolution_x`
- `resolution_y`
- `resolution_unit`
- `orientation`
- `object_role`
- `source_object_id`

### 第三优先级（工作流/环境增强）
- `format_version`
- `conversion_software`
- `conversion_time`
- `manifest_url`

这样做的好处是：
- 第一阶段就足以形成一个“能说得清”的图像技术元数据子集；
- 第二阶段再补对象关系与图像更细节特征；
- 第三阶段再把工作流/访问层信息接进来。

---

## 七、当前缺口与风险

### 1. 当前字段盘点还不够细
虽然已确认系统具备图像元数据提取能力，但当前研究线还没有逐项核实实际提取字段清单。

### 2. 当前 metadata JSON 可能是“装得下很多”，但“语义不够稳”
也就是说，当前技术信息可能已经存在，但尚未形成：
- 稳定字段名；
- 稳定字段语义；
- 稳定 profile 边界。

### 3. 转换链与对象关系还未充分结构化
例如：
- 原始图像与 BigTIFF 衍生对象之间的关系；
- 访问层对象与保存导向对象之间的关系；
- 哪个文件是 IIIF source object。

这些问题如果不显式化，会影响后续标准化表达。

---

## 八、对项目落地的建议

### 建议 1：先做字段盘点，再做 profile 收敛
先确认当前代码与 metadata JSON 中到底有哪些图像字段，再决定最终保留的最小 profile。

### 建议 2：把图像技术元数据与对象角色一起看
不要只记录“这个文件有什么参数”，还要回答：
- 它是原始文件还是衍生文件；
- 它是保存导向对象还是访问导向对象；
- 它与哪个源对象关联。

### 建议 3：和 PREMIS 事件层联动
图像技术元数据不应只是静态字段，还应与事件层结合，例如：
- `metadata_extract`
- `conversion_execute`
- `derivative_register`

这样会更利于解释对象是如何变化的。

---

## 九、当前结论

从当前项目状态看，MDAMS 已经具备了与 NISO Z39.87 建立最小对齐的现实基础，原因在于：
- 系统已具备图像元数据提取能力；
- 系统已具备图像导向处理链；
- 系统已具备大图像与 IIIF 访问场景；
- 系统已具备 fixity 与对象记录基础。

因此，当前最务实的推进路径不是宣称“已实现 Z39.87”，而是：

> 先形成一个 **面向 still image 的最小技术元数据 profile**，再逐步把当前提取字段、对象关系与处理事件收敛为更稳定的标准化表达。

这会让 MDAMS 的图像侧研究表达与后续实现都更扎实。
