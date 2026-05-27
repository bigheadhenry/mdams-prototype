# 统一平台操作与扩展边界

- 最后核对日期：2026-05-23
- 文档状态：current
- 核对口径：以当前 `/api/platform/*`、来源适配器和前端统一资源目录 / 详情实现为准
- 相关自动化护栏：`backend/tests/test_platform_directory.py`、`backend/tests/test_standard_demo_flow.py`、`frontend/tests/dashboard.spec.ts`

## 1. 目标

统一平台是当前 MDAMS Prototype 的跨来源浏览和申请入口。本文件补充操作层面的规则，帮助后续新增来源、调整统一详情或扩展检索能力时保持一致。

## 2. 当前职责

统一平台当前负责：

1. 汇总已注册来源。
2. 将来源资源转换为统一资源摘要。
3. 提供统一资源详情入口。
4. 暴露统一 actions 供前端渲染。
5. 支持统一资源加入申请车。

统一平台当前不负责：

- 新建独立资源实体。
- 替代来源系统内部管理页面。
- 做完整全文检索索引。
- 保存跨来源的派生文件。

## 3. 稳定来源定位

统一平台当前稳定定位方式为：

```text
source_system + source_id
```

当前主详情路径：

```text
/api/platform/resources/{source_system}/{source_id}
```

旧复合 ID 路径 `/api/platform/resources/{resource_id}` 仅用于兼容，不建议新功能继续依赖。

## 4. 当前来源粒度

| 来源 | `source_system` | 默认粒度 | 说明 |
| :--- | :--- | :--- | :--- |
| 二维影像 | `image_2d` | 单个二维资产 | 可生成 IIIF Manifest，可直接进入 Mirador |
| 三维资源 | `three_d` | 三维数字对象 | 由多个模型表现和文件聚合 |
| 视频资源 | `video` | 单个视频资产 | 作为多模态来源示例 |

三维来源的默认粒度尤其重要：统一平台不应把每个三维文件或每个表现都平铺成普通用户的默认结果。

## 5. Actions 契约

统一资源 actions 应表达前端可执行动作，而不是来源内部全部能力。常见动作包括：

| action key | 含义 |
| :--- | :--- |
| `preview` | 打开当前主要预览 |
| `platform_detail` | 打开统一资源详情 |
| `source_detail` | 打开来源详情 |
| `download` | 下载当前可交付文件或资源包 |
| `export_bagit` | 导出二维 BagIt 包 |

前端展示动作时应优先使用 action 中的 `enabled` 和 `reason`，避免只靠资源类型硬编码。

## 6. 加入申请车规则

统一平台资源加入申请车时必须保留：

- `source_system`
- `source_id`
- `resource_type`
- `title`
- `manifest_url`
- `source_label`

如果是二维来源且 `source_id` 为数字 ID，可同时填充 `asset_id`，这样交付包导出时可以复制实际文件。

三维和视频资源当前可以进入申请单，但交付包只记录来源定位，不自动展开所有文件。

## 7. 筛选与检索边界

当前 `/api/platform/resources` 支持：

- `q`
- `status`
- `resource_type`
- `profile_key`
- `preview_enabled`
- `source_system`
- `skip`
- `limit`

这些筛选仍由来源适配器内部执行，不是独立搜索引擎。后续如引入全文索引，应继续保持当前 API 的基础参数兼容。

## 8. 新增来源检查清单

新增来源前应确认：

- 定义稳定 `source_system`。
- 定义平台侧 `resource_type`。
- 明确默认列表粒度。
- 实现来源摘要、列表、详情。
- 提供统一 actions。
- 明确 `manifest_url` 或主要访问入口的含义。
- 明确是否可加入申请车，以及是否可导出实际文件。
- 补充 contract test。
- 更新 `PLATFORM_SOURCE_ADAPTERS.md` 和本文。

## 9. 回归建议

修改统一平台层后至少运行：

```powershell
python -m pytest backend\tests\test_platform_directory.py backend\tests\test_standard_demo_flow.py -q
cd frontend
npx playwright test tests/dashboard.spec.ts --project=chromium
```

涉及三维来源时，建议补跑：

```powershell
python -m pytest backend\tests\test_three_d_subsystem.py backend\tests\test_three_d_production.py -q
```

