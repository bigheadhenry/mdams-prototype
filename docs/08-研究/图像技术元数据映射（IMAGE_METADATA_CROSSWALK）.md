# 图像技术元数据 Crosswalk（面向 NISO Z39.87）

## 目的

本文档用于把 MDAMS 当前二维图像工作流中的技术元数据能力，与 NISO Z39.87《Data Dictionary – Technical Metadata for Digital Still Images》的核心关注点建立一个**最小可实施 crosswalk**。

截至 **2026-04-08**，它优先回答：
- 当前代码里到底已经稳定出现了哪些图像技术字段；
- 哪些字段可以直接进入最小 still image profile；
- 哪些字段属于 MDAMS 的访问/处理扩展，而不是 Z39.87 核心字段；
- 下一步应先 formalize 哪一组字段。

## 一、实现锚点

当前图像元数据的最可靠实现锚点是：
- `backend/app/services/metadata_layers.py`
- `Asset.metadata_info`
- `ImageRecord.metadata_info`
- `iiif_access` 服务中的访问副本生成与回写

从 `metadata_layers.py` 当前定义看，二维图像侧已经存在这些稳定字段簇：
- `core`
- `management`
- `technical`
- `profile`
- `raw_metadata`

这说明当前最务实的方向，不是重新发明一套 schema，而是把已有字段分层收口成**最小图像技术 profile**。

## 二、最小 still image profile

### 1. Core

这些字段用于说明对象是谁、来自哪里、属于什么范围。

| 字段 | 当前来源 | 作用 |
|---|---|---|
| `source_id` | layered metadata | 对象标识 |
| `source_system` | layered metadata | 来源系统标识 |
| `resource_type` | `Asset.resource_type` | 资源类型 |
| `visibility_scope` | `Asset.visibility_scope` | 可见性范围 |
| `collection_object_id` | `Asset.collection_object_id` | 藏品对象关联 |
| `profile_key` | layered metadata | 图像 profile |

### 2. Management

这些字段主要是业务与管理上下文，不是 Z39.87 核心技术字段，但对项目工作流重要。

| 字段 | 当前来源 |
|---|---|
| `project_type` | `metadata_layers.MANAGEMENT_FIELDS` |
| `project_name` | `metadata_layers.MANAGEMENT_FIELDS` |
| `photographer` | `metadata_layers.MANAGEMENT_FIELDS` |
| `photographer_org` | `metadata_layers.MANAGEMENT_FIELDS` |
| `copyright_owner` | `metadata_layers.MANAGEMENT_FIELDS` |
| `capture_time` | `metadata_layers.MANAGEMENT_FIELDS` |
| `remark` / `tags` | `metadata_layers.MANAGEMENT_FIELDS` |

### 3. Technical

这些字段是当前最适合与 NISO Z39.87 建立最小映射的部分。

| 字段 | 当前来源 | 建议级别 |
|---|---|---|
| `original_file_name` | `TECHNICAL_FIELDS` | 必选 |
| `file_size` | `TECHNICAL_FIELDS` | 必选 |
| `format_name` | `TECHNICAL_FIELDS` | 必选 |
| `format_version` | `TECHNICAL_FIELDS` | 建议 |
| `byte_order` | `TECHNICAL_FIELDS` | 可选 |
| `width` | `TECHNICAL_FIELDS` | 必选 |
| `height` | `TECHNICAL_FIELDS` | 必选 |
| `color_space` | `TECHNICAL_FIELDS` | 建议 |
| `checksum_algorithm` | `TECHNICAL_FIELDS` | 必选 |
| `checksum` / `fixity_sha256` | `TECHNICAL_FIELDS` | 必选 |
| `original_mime_type` | `TECHNICAL_FIELDS` | 建议 |
| `conversion_method` | `TECHNICAL_FIELDS` | 扩展 |

### 4. Access Extension

这些字段与图像访问链密切相关，但不属于 Z39.87 的核心 still image 技术词典，应视为 MDAMS 扩展字段。

| 字段 | 当前来源 | 说明 |
|---|---|---|
| `iiif_access_file_name` | `TECHNICAL_FIELDS` | 访问副本文件名 |
| `iiif_access_file_path` | `TECHNICAL_FIELDS` | 访问副本路径 |
| `iiif_access_mime_type` | `TECHNICAL_FIELDS` | 访问副本 MIME type |
| `preview_image_name` | `TECHNICAL_FIELDS` | 预览图 |
| `preview_image_path` | `TECHNICAL_FIELDS` | 预览图路径 |
| `preview_image_mime_type` | `TECHNICAL_FIELDS` | 预览图 MIME type |

### 5. Workflow Extension

这些字段说明对象是如何被处理出来的，适合与 PREMIS 事件模型联动。

| 字段 | 当前来源 |
|---|---|
| `ingest_method` | `TECHNICAL_FIELDS` |
| `derivative_rule_id` | `TECHNICAL_FIELDS` |
| `derivative_strategy` | `TECHNICAL_FIELDS` |
| `derivative_priority` | `TECHNICAL_FIELDS` |
| `derivative_target_format` | `TECHNICAL_FIELDS` |
| `derivative_source_family` | `TECHNICAL_FIELDS` |
| `derivative_reason` | `TECHNICAL_FIELDS` |
| `derivative_threshold_bytes` | `TECHNICAL_FIELDS` |
| `derivative_threshold_pixels` | `TECHNICAL_FIELDS` |
| `error_message` | `TECHNICAL_FIELDS` |

## 三、类别级 crosswalk

| MDAMS 当前字段组 | Z39.87 关注方向 | 当前判断 |
|---|---|---|
| 文件名、大小、MIME、格式 | 基础文件与格式信息 | 已具备基础 |
| 宽度、高度、色彩空间 | 图像技术特征 | 可形成最小 profile |
| 校验算法与校验值 | 管理/技术补充信息 | 应保留，并与保存层联动 |
| 访问副本与预览图字段 | 非 Z39.87 核心，属访问扩展 | 应单独作为扩展组 |
| 衍生策略与转换方法 | 非 Z39.87 核心，属工作流扩展 | 应与事件层联动 |

## 四、字段级最小 crosswalk

| MDAMS 字段 | 近似对应的 Z39.87 关注点 | 当前状态 | 建议 |
|---|---|---|---|
| `original_file_name` | 对象基本识别信息 | 已稳定 | 保留 |
| `file_size` | file size | 已稳定 | 保留 |
| `format_name` | format designation | 已稳定 | 保留 |
| `format_version` | format version | 已存在 | 建议保留 |
| `width` | image dimensions | 已稳定 | 保留 |
| `height` | image dimensions | 已稳定 | 保留 |
| `color_space` | image color characteristics | 已存在 | 建议保留 |
| `byte_order` | encoding/representation detail | 已存在 | 可选 |
| `checksum_algorithm` | 技术/管理补充信息 | 已稳定 | 保留 |
| `checksum` | 技术/管理补充信息 | 已稳定 | 保留 |

## 五、当前最小图像技术 profile 建议

如果现在要收成一版最小 still image profile，建议优先固定以下字段：

### P0 必选
- `original_file_name`
- `file_size`
- `format_name`
- `width`
- `height`
- `checksum_algorithm`
- `checksum`

### P1 建议
- `format_version`
- `color_space`
- `original_mime_type`
- `capture_time`
- `profile_key`

### P2 扩展
- `iiif_access_*`
- `preview_image_*`
- `derivative_*`
- `conversion_method`
- `error_message`

## 六、当前风险

### 1. 当前字段存在，但 profile 边界还不够显式
系统已经能提取和存储不少信息，但“哪些字段属于稳定技术 profile”仍需进一步锁定。

### 2. 访问层字段容易与技术元数据字段混用
IIIF access 和 preview 字段对系统很重要，但不应直接等同于 Z39.87 核心字段。

### 3. 图像记录与资产字段仍需进一步协同
`ImageRecord` 与 `Asset` 目前都能承载部分元数据，后续需要更明确“录入字段”“技术字段”“衍生字段”分别归属哪一层。

## 七、当前工作结论

从当前代码和工作流看，MDAMS 已经具备建立**最小 still image 技术元数据 profile**的现实基础。

最务实的推进路径不是宣称“已实现 Z39.87”，而是：

> 先把当前已稳定存在的图像技术字段收敛为最小 still image profile，再将访问扩展字段和工作流扩展字段与 PREMIS 事件模型联动起来。
