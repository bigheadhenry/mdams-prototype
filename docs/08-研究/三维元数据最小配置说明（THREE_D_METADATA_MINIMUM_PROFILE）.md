# 三维元数据最小配置说明

## 目的

本文档用于把 MDAMS 当前三维子系统中的 metadata 分层、对象字段和文件角色，收敛成一个**最小可实施的三维 metadata/profile 框架**。

它的目标不是宣称当前已经完成完整 3D 标准化，而是回答：
- 当前代码里已经稳定存在哪些三维字段层；
- 哪些字段足以构成最小 3D profile；
- 不同 profile 类型各自至少需要什么字段；
- 哪些内容应作为后续 CS3DP 或保存导向扩展。

## 一、实现锚点

当前三维元数据的主要实现锚点是：
- `backend/app/models.py`
- `backend/app/services/three_d_metadata.py`
- `backend/app/services/three_d_storage.py`
- `backend/app/services/three_d_detail.py`

截至 **2026-04-08**，三维侧已经形成如下稳定分层：
- `core`
- `management`
- `collection`
- `technical`
- `profile`
- `preservation`
- `raw_metadata`

这意味着当前最合理的做法，是围绕这 7 层建立最小 profile，而不是重新造一套平行结构。

## 二、最小三维 metadata 分层

### 1. Core

用于标识三维资源版本对象是谁、属于哪个对象组、当前处于什么状态。

| 字段 | 当前来源 |
|---|---|
| `source_id` | `three_d_metadata.core` |
| `source_system` / `source_label` | `three_d_metadata.core` |
| `resource_type` / `resource_type_label` | `ThreeDAsset.resource_type` |
| `title` | `three_d_metadata.core` |
| `status` | `ThreeDAsset.status` |
| `profile_key` / `profile_label` | `three_d_metadata.core` |
| `collection_object_id` | `ThreeDAsset.collection_object_id` |
| `resource_group` | `ThreeDAsset.resource_group` |
| `version_label` / `version_order` | `ThreeDAsset.version_label` / `version_order` |
| `is_current` | `ThreeDAsset.is_current` |
| `is_web_preview` | `ThreeDAsset.is_web_preview` |
| `web_preview_status` / `web_preview_reason` | `ThreeDAsset.web_preview_*` |

### 2. Management

用于说明资源由谁、在什么项目、何时采集或制作。

| 字段 | 当前来源 |
|---|---|
| `project_name` | `three_d_metadata.management` |
| `creator` | `three_d_metadata.management` |
| `creator_org` | `three_d_metadata.management` |
| `capture_time` | `three_d_metadata.management` |
| `remark` | `three_d_metadata.management` |
| `tags` | `three_d_metadata.management` |

### 3. Collection

用于表达藏品对象或上层对象语义。

| 字段 | 当前来源 |
|---|---|
| `collection_object_id` | `ThreeDCollectionObject.id` |
| `object_number` | `ThreeDCollectionObject.object_number` |
| `object_name` | `ThreeDCollectionObject.object_name` |
| `object_type` | `ThreeDCollectionObject.object_type` |
| `collection_unit` | `ThreeDCollectionObject.collection_unit` |
| `summary` | `ThreeDCollectionObject.summary` |
| `keywords` | `ThreeDCollectionObject.keywords` |

### 4. Technical

用于说明文件技术特征和资源包结构。

| 字段 | 当前来源 | 建议级别 |
|---|---|---|
| `original_file_name` | `three_d_metadata.technical` | 必选 |
| `file_size` | `three_d_metadata.technical` | 必选 |
| `format_name` | `three_d_metadata.technical` | 必选 |
| `format_version` | `three_d_metadata.technical` | 建议 |
| `extension` | `three_d_metadata.technical` | 建议 |
| `vertex_count` | `three_d_metadata.technical` | 模型类建议 |
| `face_count` | `three_d_metadata.technical` | 模型类建议 |
| `material_count` | `three_d_metadata.technical` | 模型类可选 |
| `texture_count` | `three_d_metadata.technical` | 模型类可选 |
| `point_count` | `three_d_metadata.technical` | 点云类建议 |
| `lod_count` | `three_d_metadata.technical` | 模型类可选 |
| `coordinate_system` | `three_d_metadata.technical` | 点云类建议 |
| `unit` | `three_d_metadata.technical` | 建议 |
| `scale` | `three_d_metadata.technical` | 可选 |
| `bounding_box` | `three_d_metadata.technical` | 可选 |
| `checksum_algorithm` | `three_d_metadata.technical` | 建议 |
| `checksum` | `three_d_metadata.technical` | 建议 |
| `files` / `file_count` / `file_groups` | `three_d_metadata.technical` | 包化资源建议 |
| `primary_file` / `primary_file_role` | `three_d_metadata.technical` | 包化资源建议 |

### 5. Profile

当前三维 profile 已由代码稳定限定为以下类型：
- `model`
- `point_cloud`
- `oblique_photo`
- `package`
- `other`

### 6. Preservation

用于表达当前尚较轻量的保存导向信息。

| 字段 | 当前来源 |
|---|---|
| `storage_tier` | `ThreeDAsset.storage_tier` |
| `preservation_status` | `ThreeDAsset.preservation_status` |
| `preservation_note` | `ThreeDAsset.preservation_note` |

## 三、文件角色词表

当前三维文件角色词表已由 `three_d_storage.py` 稳定定义为：

| 角色 | 含义 |
|---|---|
| `model` | 三维模型 |
| `point_cloud` | 点云 |
| `oblique_photo` | 倾斜摄影图像 |
| `texture` | 贴图 |
| `support` | 辅助文件 |
| `other` | 其他 |

这个角色词表已经足够作为当前三维 profile 的最小文件结构语义。

## 四、各 profile 的最小字段要求

### 1. `model`

**至少应有：**
- `title`
- `format_name`
- `version_label`
- `resource_group`
- `vertex_count` 或 `face_count`
- 至少一个 `model` 文件角色

### 2. `point_cloud`

**至少应有：**
- `title`
- `format_name`
- `version_label`
- `resource_group`
- `point_count`
- 至少一个 `point_cloud` 文件角色

### 3. `oblique_photo`

**至少应有：**
- `title`
- `project_name`
- `capture_time`
- `version_label`
- 至少一个 `oblique_photo` 文件角色

### 4. `package`

**至少应有：**
- `title`
- `resource_group`
- `version_label`
- `file_count`
- `role_summary`
- 至少两种文件角色或多文件结构

## 五、最小三维 profile 建议

如果当前要先落一版“能写进研究，也能继续实施”的最小三维 profile，建议优先固定：

### P0 必选
- `title`
- `resource_type`
- `profile_key`
- `resource_group`
- `version_label`
- `is_current`
- `is_web_preview`
- `web_preview_status`
- `original_file_name`
- `file_size`
- `format_name`
- `file_count`
- `primary_file_role`

### P1 建议
- `collection_object_id`
- `object_number`
- `object_name`
- `project_name`
- `creator`
- `capture_time`
- `checksum_algorithm`
- `checksum`
- `storage_tier`
- `preservation_status`

### P2 扩展
- `vertex_count`
- `face_count`
- `point_count`
- `coordinate_system`
- `unit`
- `bounding_box`
- `creator_org`
- `tags`
- `preservation_note`

## 六、当前风险

### 1. 当前三维元数据已分层，但对象层与版本层仍容易混用
`ThreeDCollectionObject`、`ThreeDAsset`、`ThreeDAssetFile` 各自承担不同语义，后续若不坚持分层，很容易再次混回单表字段堆叠。

### 2. Web 展示语义与保存语义仍需继续分开
`is_web_preview` / `web_preview_status` 不等于保存状态，不能替代 `storage_tier` / `preservation_status`。

### 3. 当前 profile 已足够支撑研究表达，但尚不足以宣称三维标准化已完成
当前更合理的说法是：系统已经具备 minimum viable 3D profile 的现实基础。

## 七、当前工作结论

截至 **2026-04-08**，MDAMS 三维子系统已经不再只是上传和预览入口，而是具备：
- 对象/版本/文件包分层；
- 最小文件角色词表；
- 技术字段、对象字段和保存字段分层；
- Web 展示状态与保存状态并存的基础。

因此，当前最务实的推进路径是：

> 先把这套现有字段收敛为 minimum viable 3D metadata/profile，再考虑更正式的三维标准映射与长期保存 formalization。
