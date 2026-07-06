# 统一平台来源适配器

- 最后核对日期：2026-05-17
- 核对口径：仅以已提交代码中的稳定实现为准，不纳入当前工作区未提交改动
- 核对范围：`backend/app/platform/registry.py`、`backend/app/platform/image_source.py`、`backend/app/platform/three_d_source.py`、`backend/app/platform/video_source.py`、`backend/app/routers/platform.py`

## 1. 目标

本文件用于说明统一平台当前如何聚合不同来源系统，以及来源适配器当前已经支持哪些能力。

## 2. 当前平台结构

统一平台当前由三部分组成：

1. 来源注册表 `registry`
2. 各来源适配器
3. 平台路由 `/api/platform/*`

当前平台层并不直接存储新的资源实体，而是从已有来源系统读取并转换为统一视图。

## 3. 当前来源

当前已注册来源包括：

| 来源系统 | 适配器文件 | 资源类型方向 |
| :--- | :--- | :--- |
| `image_2d` | `image_source.py` | 二维影像 |
| `three_d` | `three_d_source.py` | 三维数字对象 / 模型表现 |
| `video` | `video_source.py` | 视频资源 |

## 4. 当前平台接口

平台接口包括：

- `GET /api/platform/sources`
- `GET /api/platform/resources`
- `GET /api/platform/resources/{source_system}/{source_id}`
- `GET /api/platform/resources/{resource_id}`（旧复合 ID 兼容路径，已标记 deprecated）

它们分别对应：

- 来源摘要
- 统一目录列表
- 统一详情
- 旧路径兼容

## 5. 适配器职责

每个适配器当前至少负责三件事：

1. 返回来源摘要
2. 返回统一资源列表
3. 返回统一资源详情
4. 为统一资源提供面向前端的 actions

这意味着平台层只负责调度和聚合，不负责来源内部业务逻辑。

## 6. 二维来源适配器

二维来源适配器当前负责：

- 从 `Asset` 表读取二维资源
- 复用元数据分层结果
- 生成统一资源摘要
- 为二维资源提供平台详情跳转

二维来源当前会暴露：

- `source_system`
- `source_label`
- `source_id`
- `resource_type`
- `profile_key`
- `profile_label`
- `preview_enabled`
- `manifest_url`
- `detail_url`
- `thumbnail_url`
- `actions`
- `source_record_type`
- `source_record_schema`

## 7. 三维来源适配器

三维来源适配器当前负责：

- 从 `ThreeDAsset` 读取三维资源记录
- 复用三维元数据层
- 按 `collection_object_id + resource_group` 聚合为三维数字对象
- 汇总对象标题、profile、模型表现、文件数、预览状态
- 返回对象级统一详情结构

三维来源和二维来源不同点在于：

- 平台默认输出粒度是 `three_d_digital_object`
- 统一详情中会嵌入对象下的模型表现列表
- `preview_enabled` 取决于对象下是否存在可作为默认 Web 预览的表现
- `source_id` 可以是 `object-{anchor_asset_id}`，旧数字 ID 仍可被适配器兼容解析

## 8. 视频来源适配器

视频来源适配器当前负责：

- 从 `VideoAsset` 表读取视频资源
- 复用视频元数据分层结果
- 生成统一资源摘要
- 提供统一详情中的视频 source record
- 提供播放、详情和下载 actions

视频来源当前稳定标识为：

- `source_system`: `video`
- `source_label`: `视频子系统`
- `resource_type`: `video_cultural_object`

当前视频来源主要用于统一平台的多模态接入与预览演示，不应被描述为完整视频生产管理子系统。

## 9. 当前平台筛选能力

当前平台目录已支持以下筛选参数：

- `q`
- `status`
- `resource_type`
- `profile_key`
- `preview_enabled`
- `source_system`（由前端标签页注入，不再暴露为用户可选下拉）

筛选会先由平台层分发，再由来源适配器在各自内部执行。

前端交互已从「来源筛选下拉 + 侧边栏卡片」切换为「二维 / 三维 / 视频」维度标签页，用户无需感知底层子系统概念。标签页 key 与 `source_system` 的映射为：`2d → image_2d`、`3d → three_d`、`video → video`。

## 10. 当前统一资源结构重点

统一资源摘要和详情应优先围绕以下字段理解：

- `id`：平台复合 ID，例如 `image_2d:12` 或 `three_d:object-5`
- `source_system`：来源系统标识
- `source_id`：来源内稳定定位 ID
- `resource_type`：平台侧资源类型
- `preview_enabled`：是否存在可预览访问表示
- `manifest_url`：当前来源的主要访问入口；二维为 IIIF Manifest，三维为默认预览资源入口，视频为 stream 入口
- `actions`：前端可展示的预览、详情、来源详情、下载或导出动作
- `source_record_type` / `source_record_schema`：统一详情内嵌来源记录的类型和结构版本

## 11. 当前边界

当前平台层已经成立，但仍有边界：

- 还没有统一全文检索索引
- 还没有更多外部来源适配器
- 统一详情仍以“来源详情聚合”为主，而不是完全独立的新模型
- 视频来源是多模态扩展示例，不是完整视频 DAM 子系统
- 三维数字对象聚合已经在平台层成立，但底层仍复用 `ThreeDAsset` 等现有表结构

## 12. 后续扩展建议

后续新增来源时，建议保持相同模式：

1. 新建来源适配器
2. 实现摘要、列表、详情三类能力
3. 在注册表中注册
4. 让平台目录自动聚合

新增来源时还应同步补充：

- `source_system` 稳定命名
- `resource_type` 资源类型
- `actions` 可用动作
- `source_record_type` 和 `source_record_schema`
- 平台详情页是否需要专门展示组件

## 13. 关联文档

- `API_ROUTE_MAP.md`
- `UNIFIED_PLATFORM_SOURCE_LOCATOR_CONTRACT.md`
- `THREE_D_SUBSYSTEM_ARCHITECTURE.md`
- `../03-产品与流程/WORKFLOW_GUIDE.md`
- `../03-产品与流程/UNIFIED_PLATFORM_OPERATIONS_GUIDE.md`

---

## 14. 三来源最小字段契约（2026-07-06）

所有平台来源（`image_2d` / `three_d` / `video`）必须至少提供以下最小字段集。这是契约测试的基准。

### 14.1 UnifiedResourceSummary 最小字段

| 字段 | 类型 | 说明 | 是否可选 |
|------|------|------|----------|
| `id` | `str` | 平台复合 ID，如 `image_2d:12` | 必填 |
| `source_system` | `str` | 来源系统标识 | 必填 |
| `source_id` | `str` | 来源内稳定定位 ID | 必填 |
| `source_label` | `str` | 来源中文名称 | 必填 |
| `title` | `str` | 资源标题（fallback 到文件名） | 必填 |
| `resource_type` | `str` | 平台侧资源类型 | 必填 |
| `profile_key` | `str \| None` | 元数据模板键 | 可为空 |
| `profile_label` | `str \| None` | 元数据模板中文名 | 可为空 |
| `status` | `str` | 资源状态 | 必填 |
| `preview_enabled` | `bool` | 是否可预览 | 必填 |
| `manifest_url` | `str` | 主要访问入口 | 必填 |
| `detail_url` | `str` | 统一详情 URL | 必填 |
| `thumbnail_url` | `str \| None` | 缩略图 URL | 可为空 |
| `preview_data` | `dict \| None` | 预览数据（三维专用） | 可为空 |
| `updated_at` | `datetime` | 最后更新时间 | 必填 |
| `actions` | `list[UnifiedResourceAction]` | 可用操作列表 | 必填，可空数组 |

每个 action 必须包含：`key`、`label`、`kind`、`target`、`url`（可空）、`enabled`。

### 14.2 三来源差异对照

| 特征 | `image_2d` | `three_d` | `video` |
|------|:----------:|:---------:|:-------:|
| 额外字段 | `resolution`, `format`, `era`, `object_level`, `main_person`, `main_location` | `preview_data` | 无额外字段 |
| `thumbnail_url`来源 | `/api/assets/{id}/preview` | `preview_data.poster_url` | `/api/video/resources/{id}/stream` |
| `preview_enabled`判断 | `is_iiif_ready(asset)` | 有默认预览表现 | `status == "ready"` |
| `manifest_url`含义 | IIIF Manifest | 默认预览资源入口 | 视频 stream |
| actions 数量 | 5（含 export_bagit） | 4（无 export） | 4（无 export） |
| source_record | 二维详情对象 | 三维对象+表现列表 | 视频详情对象 |

### 14.3 统一详情新增字段（继承 Summary 基础上）

| 字段 | 类型 | 说明 | 是否可选 |
|------|------|------|----------|
| `source_detail_url` | `str` | 来源原详情 URL | 必填 |
| `source_record_type` | `str \| None` | 来源记录类型标识 | 可为空 |
| `source_record_schema` | `str \| None` | 来源记录结构版本 | 可为空 |
| `source_record` | `dict \| None` | 来源记录完整信息 | 可为空 |
| `rights_display` | `RightsDisplay \| None` | 权利展示信息 | 可为空 |

### 14.4 数据验证规则

1. 每个来源的 `source_system` 必须唯一且稳定。
2. `id` 应为 `{source_system}:{source_id}` 格式。
3. `source_id` 在同来源内必须稳定（不随列表页刷新变化）。
4. `actions` 中至少应包含 `platform_detail`（跳转统一详情）和 `source_detail`（跳转来源原页面）。
5. `detail_url` 应对应 `GET /api/platform/resources/{source_system}/{source_id}` 可访问。
6. `thumbnail_url` 可为 None，但不能返回 404 或崩溃。
7. `updated_at` 应为 UTC 或带时区标记、ISO 格式。
