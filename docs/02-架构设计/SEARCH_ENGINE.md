# 搜索引擎架构

> 最后更新：2026-07-06

## 1. 架构概览

MDAMS 采用**双轨搜索架构**：

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端统一检索                              │
│          PlatformDirectory.tsx (前端卡片/列表视图)                │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                              ▼
┌──────────────────────┐    ┌──────────────────────────────┐
│  平台筛选 (Adapter)   │    │  全文检索 (Meilisearch)       │
│  GET /platform/       │    │  GET /platform/reindex       │
│  resources            │    │  POST /subscriptions/check   │
│                      │    │                              │
│  适 配 器 内 部 过滤   │    │  模糊搜索 · 排序 · 分面       │
│  精确匹配 · 轻量       │    │  跨来源 · search_text 强化    │
└──────────────────────┘    └──────────────────────────────┘
```

### 分工决策规则

| 场景 | 谁负责 | 说明 |
|------|--------|------|
| 按来源/状态/类型/profile 精确筛选 | 平台适配器 | 直接走后端 ORM 查询，不影响用户 |
| 全文文本搜索（关键词、模糊） | Meilisearch | `search_text` 字段聚合标题/标签/来源 |
| 排序（按更新时间/标题/状态） | 两者均可 | Meilisearch 提供更好的多字段排序 |
| 分面统计（每种来源/类型的文档数） | Meilisearch | 通过 `facetDistribution` 返回 |
| 搜索订阅定期检查 | Meilisearch → 适配器 fallback | 优先走 Meilisearch，不可用时降级到适配器 |
| 搜索订阅创建/列表/删除 | `subscriptions` 路由 | 基于 PostgreSQL，与搜索引擎无关 |

## 2. 组件说明

### 2.1 平台适配器筛选（默认路径）

`GET /api/platform/resources` 在 `platform.py` 路由中处理，不涉及 Meilisearch。

- 参数：`q`, `status`, `resource_type`, `profile_key`, `preview_enabled`, `source_system`, `sort_by`, `sort_order`
- 逻辑：分发到各来源适配器 → 适配器内部做内存级过滤
- 优点：零外部依赖，任何环境均可工作
- 局限：`q` 参数做的是字符串包含检查（非全文索引），结果质量有限

### 2.2 搜索引擎（Meilisearch）

`POST /api/platform/reindex` 触发全量索引重建。

- 索引名：`mdams_resources`
- 主键：`id`（格式 `{source_system}:{source_id}`）
- 可排序字段：`updated_at`, `title`, `status`
- 可过滤字段：`source_system`, `resource_type`, `profile_key`, `status`, `preview_enabled`, `era`, `object_level`, `main_person`, `main_location`, `format`, `object_number`
- 可搜索字段：`title`, `search_text`, `source_label`, `profile_label`, `resolution`, `format`, `era`, `main_person`, `main_location`
- `search_text` 是预计算的全文搜索优化字段，聚合了标题、来源标签、profile 标签和资源类型

### 2.3 搜索订阅

`/api/subscriptions/` 路由提供轻量搜索订阅功能。

- 用户可保存一组 `query_params`
- `PUT /{id}/check` 重新执行查询并返回新匹配数量
- 检查时优先使用 Meilisearch，不可用时降级到适配器
- 不需要实时推送机制

## 3. 索引文档结构

| 字段 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `id` | string | `source_system:source_id` | 唯一文档 ID |
| `source_system` | string | 适配器 | 来源标识 |
| `source_id` | string | 适配器 | 来源内 ID |
| `title` | string | 适配器 | 资源标题 |
| `resource_type` | string | 适配器 | 资源类型 |
| `status` | string | 适配器 | 状态 |
| `preview_enabled` | bool | 适配器 | 可预览 |
| `updated_at` | string (ISO) | 适配器 | 最后更新 |
| `thumbnail_url` | string\|null | 适配器 | 缩略图 |
| `search_text` | string | 预计算 | 聚合全文搜索内容 |
| `manifest_url` / `detail_url` | string | 适配器 | 前端跳转 |
| `resolution`, `format`, `era`, ... | string\|null | 适配器 | 扩展字段 |

## 4. 搜索边界清单

| 边界 | 说明 |
|------|------|
| ✅ 平台筛选不需要 Meilisearch | 适配器内部过滤可在无搜索引擎时工作 |
| ✅ 搜索订阅有自动降级 | Meilisearch 不可用时走适配器列表 |
| ✅ 索引重建幂等 | `seed_index_from_adapters()` 可以多次调用 |
| ⚠️ 空关键词 | `q=""` 或 `q=None` 返回所有匹配（不分页则为全部文档） |
| ⚠️ 无搜索引擎时搜索订阅仍可用 | 但只能做精确匹配，不支持模糊搜索或分面统计 |
| ❌ 无跨来源统一排序 | 适配器筛选走各自 DB 查询，排序结果由平台层合并 |
| ❌ 无实时索引更新 | 资源变更后需手动 reindex 或等待定期任务 |
| ❌ 无 Elasticsearch 适配器 | 当前只有 Meilisearch 一个实现 |

## 5. 关联测试

| 测试文件 | 类型 | 说明 |
|----------|------|------|
| `test_search_engine.py` | 单元 + 契约 + 集成 | filter 表达式、doc 转换、Mock 引擎、结果结构契约（无需 Meilisearch）、集成测试（需 Meilisearch） |

## 6. 关联文档

- `API_ROUTE_MAP.md` — 搜索相关 API 路由
- `PLATFORM_SOURCE_ADAPTERS.md` — 平台适配器接口
- `../03-产品与流程/UNIFIED_PLATFORM_OPERATIONS_GUIDE.md` — 统一平台操作指南
- `.hermes/plans/2026-07-05_mdams-next-phase-deepseek-v4-flash.md` — 本阶段执行计划
