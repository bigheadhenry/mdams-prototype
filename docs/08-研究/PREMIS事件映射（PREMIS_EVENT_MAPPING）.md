# PREMIS 事件映射（最小可实施模型）

## 目的

本文档用于把 MDAMS 当前核心工作流中的动作收敛为一个**最小 PREMIS 风格事件模型**。

它的目标不是宣称系统已经完整实现 PREMIS，而是回答以下问题：
- 哪些动作现在最值得被正式记录为事件；
- 每条事件最小要保存哪些字段；
- 事件类型、状态、代理和对象角色如何统一；
- 应优先先落哪些事件，再逐步扩展。

## 当前立场

截至 **2026-04-08**，MDAMS 已经存在大量 proto-PREMIS 行为：
- fixity 生成/校验；
- 元数据提取；
- 转换与访问副本生成；
- IIIF Manifest 生成；
- 绑定、替换、提交、退回等工作流动作；
- 三维生产记录；
- AI 面板动作日志。

但这些行为目前分散在：
- 状态字段；
- `metadata_info`；
- 三维 `production_records`；
- 应用日志或接口返回；
- 前端/后端动作链路。

因此，当前最合理的做法不是一步到位“完整 PREMIS”，而是建立一套**跨工作流可复用的最小事件词表与记录结构**。

## 一、最小事件记录结构

建议后续系统中每条事件至少具备以下字段：

| 字段 | 含义 | 建议级别 |
|---|---|---|
| `event_id` | 事件唯一标识 | 必填 |
| `event_type` | 事件类型 | 必填 |
| `event_status` | 事件状态 | 必填 |
| `event_time` | 事件发生时间 | 必填 |
| `target_object_type` | 目标对象类型 | 必填 |
| `target_object_id` | 目标对象标识 | 必填 |
| `object_role` | 对象角色 | 建议 |
| `agent_type` | 执行主体类型 | 建议 |
| `agent_id` | 执行主体标识 | 建议 |
| `outcome` | 结果摘要 | 建议 |
| `outcome_detail` | 详细结果或错误信息 | 可选 |
| `task_id` | 异步任务 ID | 可选 |
| `related_object_type` | 关联对象类型 | 可选 |
| `related_object_id` | 关联对象标识 | 可选 |
| `source_path` | 输入路径 | 可选 |
| `target_path` | 输出路径 | 可选 |
| `software_name` | 使用的软件/服务 | 可选 |
| `software_version` | 软件版本 | 可选 |
| `checksum_algorithm` | 校验算法 | 可选 |
| `checksum_value` | 校验值 | 可选 |
| `event_note` | 人工备注 | 可选 |

## 二、建议统一词表

### 1. 事件状态

| 状态 | 含义 |
|---|---|
| `started` | 事件已开始 |
| `completed` | 事件成功完成 |
| `failed` | 事件执行失败 |
| `retried` | 事件被重新执行 |
| `skipped` | 事件按规则跳过 |
| `cancelled` | 事件被取消 |

### 2. 代理类型

| 代理类型 | 含义 |
|---|---|
| `user` | 人工用户 |
| `system` | 主系统逻辑 |
| `worker` | 异步任务/后台 worker |
| `service` | 外部或内部工具服务 |

### 3. 目标对象类型

| 对象类型 | 当前对应 |
|---|---|
| `asset` | `Asset` |
| `image_record` | `ImageRecord` |
| `three_d_asset` | `ThreeDAsset` |
| `three_d_file` | `ThreeDAssetFile` |
| `application` | `Application` |
| `application_item` | `ApplicationItem` |
| `access_representation` | IIIF Manifest、预览图、viewer-ready 文件 |
| `export_package` | BagIt ZIP、交付包 |

### 4. 对象角色

| 对象角色 | 说明 |
|---|---|
| `original_file` | 原始文件 |
| `normalized_file` | 规范化/转换后文件 |
| `access_derivative` | 访问副本 |
| `preview_image` | 缩略图/预览图 |
| `manifest` | IIIF Manifest |
| `delivery_package` | 交付包 |
| `bagit_package` | BagIt 包 |
| `three_d_model` | 三维模型文件 |
| `point_cloud` | 点云文件 |
| `oblique_photo` | 倾斜摄影文件 |
| `texture` | 三维贴图 |
| `support_file` | 辅助文件 |

## 三、P0 优先事件集合

P0 事件是当前最值得统一落地的最小事件集合。

| 事件类型 | 目标对象 | 当前实现锚点 | 优先级 |
|---|---|---|---|
| `file_receive` | `asset` / `three_d_asset` | 上传与接收入口 | P0 |
| `asset_register` | `asset` | 资产创建/登记 | P0 |
| `image_record_submit` | `image_record` | 图像记录提交 | P0 |
| `image_record_return` | `image_record` | 图像记录退回 | P0 |
| `image_record_bind_confirm` | `image_record` + `asset` | 绑定/替换确认 | P0 |
| `fixity_generate` | `asset` | SHA256 生成 | P0 |
| `fixity_verify` | `asset` | 校验值验证 | P0 |
| `metadata_extract` | `asset` / `three_d_asset` | 元数据提取 | P0 |
| `conversion_execute` | `asset` | PSB/PSD/TIFF 等处理链 | P0 |
| `iiif_access_generate` | `access_representation` | IIIF access 副本生成 | P0 |
| `manifest_generate` | `access_representation` | IIIF Manifest 生成 | P0 |
| `export_generate` | `export_package` | BagIt / 交付包导出 | P0 |

## 四、P1 扩展事件集合

| 事件类型 | 目标对象 | 当前实现锚点 | 优先级 |
|---|---|---|---|
| `three_d_version_register` | `three_d_asset` | 三维版本创建 | P1 |
| `three_d_file_register` | `three_d_file` | 三维文件包登记 | P1 |
| `three_d_preview_status_change` | `three_d_asset` | Web 展示状态切换 | P1 |
| `production_stage_record` | `three_d_asset` | 三维生产记录 | P1 |
| `application_submit` | `application` | 申请单提交 | P1 |
| `application_review` | `application` | 审批通过 / 拒绝 | P1 |
| `delivery_export` | `export_package` | 利用交付包导出 | P1 |
| `ai_action_execute` | `access_representation` | Mirador AI 动作日志 | P1 |

## 五、按工作流映射

### 1. 二维数字资产主链路

| 工作流动作 | 建议事件类型 | 目标对象 | 说明 |
|---|---|---|---|
| 文件进入系统 | `file_receive` | `asset` | 记录来源、文件名、路径、大小 |
| 系统登记资产 | `asset_register` | `asset` | 把文件提升为管理对象 |
| 生成校验值 | `fixity_generate` | `asset` | 记录算法和值 |
| 提取元数据 | `metadata_extract` | `asset` | 记录工具与输出摘要 |
| 转换或衍生 | `conversion_execute` | `asset` | 记录输入、输出与软件 |
| 生成访问副本 | `iiif_access_generate` | `access_representation` | 区分访问副本与原始对象 |
| 生成清单 | `manifest_generate` | `access_representation` | 记录 Manifest 路径或标识 |
| 生成导出包 | `export_generate` | `export_package` | 记录 BagIt 或交付路径 |

### 2. 图像记录协作链路

| 工作流动作 | 建议事件类型 | 目标对象 | 说明 |
|---|---|---|---|
| 提交记录 | `image_record_submit` | `image_record` | 表示记录进入待上传/待处理阶段 |
| 退回记录 | `image_record_return` | `image_record` | 表示协作回退 |
| 确认绑定 | `image_record_bind_confirm` | `image_record` + `asset` | 是“协作记录”与“数字资产”连接的关键事件 |
| 替换上传 | `image_record_bind_confirm` | `image_record` + `asset` | 可通过 `outcome_detail` 区分 bind/replace |

### 3. 三维对象链路

| 工作流动作 | 建议事件类型 | 目标对象 | 说明 |
|---|---|---|---|
| 登记三维版本 | `three_d_version_register` | `three_d_asset` | 记录 version_label、resource_group |
| 登记文件包 | `three_d_file_register` | `three_d_file` | 记录 role、file_count、primary file |
| 记录生产阶段 | `production_stage_record` | `three_d_asset` | 可映射当前 `production_records` |
| 切换展示状态 | `three_d_preview_status_change` | `three_d_asset` | 记录 is_web_preview / web_preview_status |

### 4. 申请与交付链路

| 工作流动作 | 建议事件类型 | 目标对象 | 说明 |
|---|---|---|---|
| 提交申请 | `application_submit` | `application` | 记录申请人、目的、范围 |
| 审批处理 | `application_review` | `application` | 记录 approved / rejected |
| 导出交付包 | `delivery_export` | `export_package` | 记录与申请单的关联 |

## 六、当前落地策略

### Phase 1
- 先落 P0 事件类型；
- 只要求 `started / completed / failed` 三种状态；
- 只强制记录 `event_type`、`event_time`、`target_object_type`、`target_object_id`、`event_status`、`outcome`。

### Phase 2
- 把图像记录、三维、申请交付纳入统一事件层；
- 引入 `related_object_type` / `related_object_id`；
- 引入 `retried` / `skipped`。

### Phase 3
- 再考虑 rights、agent registry、事件持久化表、跨对象时间线。

## 七、当前工作结论

当前最重要的不是争论“是否已经实现 PREMIS”，而是先把 MDAMS 中最有保存意义和工作流意义的动作收敛成统一事件层。

对当前项目而言，最现实的表述是：

> MDAMS 已经具备建立最小 PREMIS 风格事件模型的现实基础，下一步应优先把二维资产主链路、图像记录协作链路和三维生产/展示链路中的核心动作统一为可追踪、可解释、可扩展的事件集合。
