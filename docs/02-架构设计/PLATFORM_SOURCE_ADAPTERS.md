# 统一平台来源适配器

- 最后核对日期：2026-04-06
- 核对范围：`backend/app/platform/registry.py`、`backend/app/platform/image_source.py`、`backend/app/platform/three_d_source.py`、`backend/app/routers/platform.py`

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
| 三维来源 | `three_d_source.py` | 三维对象 / 资源包 |

## 4. 当前平台接口

平台接口包括：

- `GET /api/platform/sources`
- `GET /api/platform/resources`
- `GET /api/platform/resources/{resource_id}`

它们分别对应：

- 来源摘要
- 统一目录列表
- 统一详情

## 5. 适配器职责

每个适配器当前至少负责三件事：

1. 返回来源摘要
2. 返回统一资源列表
3. 返回统一资源详情

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
- `resource_type`
- `profile_key`
- `profile_label`
- `preview_enabled`
- `manifest_url`
- `detail_url`

## 7. 三维来源适配器

三维来源适配器当前负责：

- 从 `ThreeDAsset` 读取三维对象
- 复用三维元数据层
- 汇总对象标题、profile、版本、预览状态
- 返回统一详情结构

三维来源和二维来源不同点在于：

- 它更多面向对象 / 版本 / 多文件角色
- `preview_enabled` 与 Web 预览状态相关

## 8. 当前平台筛选能力

当前平台目录已支持以下筛选参数：

- `q`
- `status`
- `resource_type`
- `profile_key`
- `preview_enabled`
- `source_system`

筛选会先由平台层分发，再由来源适配器在各自内部执行。

## 9. 当前边界

当前平台层已经成立，但仍有边界：

- 还没有统一全文检索索引
- 还没有更多外部来源适配器
- 统一详情仍以“来源详情聚合”为主，而不是完全独立的新模型

## 10. 后续扩展建议

后续新增来源时，建议保持相同模式：

1. 新建来源适配器
2. 实现摘要、列表、详情三类能力
3. 在注册表中注册
4. 让平台目录自动聚合

## 11. 关联文档

- `API_ROUTE_MAP.md`
- `THREE_D_SUBSYSTEM_ARCHITECTURE.md`
- `../03-产品与流程/WORKFLOW_GUIDE.md`
