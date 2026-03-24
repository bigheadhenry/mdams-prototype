# MDAMS 统一元数据示例

## 1. 文档目的

本文档用于给 MDAMS 的统一元数据体系提供可直接参考的示例，便于后续：

- 开发数据库结构；
- 设计接口返回结构；
- 编写接入适配器；
- 组织聚合检索索引；
- 让模型和开发者快速理解字段如何使用。

本文档与 `UNIFIED_METADATA_REFERENCE.md` 配合使用：

- `UNIFIED_METADATA_REFERENCE.md` 说明原则和分层；
- 本文档给出具体示例。

---

## 2. 统一字段示例表

下面是一组适合 MDAMS 顶层统一管理的核心字段示例。

| 字段名 | 含义 | 建议层级 | 示例 |
|---|---|---|---|
| `global_resource_id` | 平台全局资源 ID | 顶层主键 | `mdams:res:00001234` |
| `source_system` | 来源系统标识 | 顶层 | `mdams-image` |
| `source_object_id` | 来源系统对象 ID | 顶层 | `asset_44` |
| `local_object_id` | 子系统本地对象 ID | 子系统 | `44` |
| `resource_type` | 资源类型 | 顶层/子系统均可保留副本 | `image_2d_cultural_object` |
| `title` | 资源标题 | 顶层主字段 | `清代山水图` |
| `summary` | 简要描述 | 顶层主字段 | `一幅清代山水图像资源` |
| `keywords` | 关键词/标签 | 顶层主字段 | `山水, 清代, 书画` |
| `creators` | 创建者/责任者 | 顶层主字段 | `["张某"]` |
| `rights` | 权利/版权说明 | 顶层主字段 | `馆藏内部使用` |
| `access_level` | 访问级别 | 顶层主字段 | `internal` |
| `status` | 统一状态 | 顶层主字段 | `ready` |
| `preview_url` | 预览地址 | 顶层主字段 | `/api/iiif/44/manifest` |
| `detail_url` | 统一详情页地址 | 顶层主字段 | `/assets/44` |
| `updated_at` | 最近更新时间 | 顶层主字段 | `2026-03-24T12:00:00Z` |

---

## 3. 顶层公共元数据示例

下面是一个顶层聚合层中的公共元数据示例。

```json
{
  "global_resource_id": "mdams:res:00001234",
  "source_system": "mdams-image",
  "source_object_id": "asset_44",
  "resource_type": "image_2d_cultural_object",
  "title": "清代山水图",
  "summary": "一幅清代山水图像资源，已完成基础处理并可预览。",
  "keywords": ["山水", "清代", "书画"],
  "creators": ["张某"],
  "rights": "馆藏内部使用",
  "access_level": "internal",
  "status": "ready",
  "preview_url": "/api/iiif/44/manifest",
  "detail_url": "/assets/44",
  "updated_at": "2026-03-24T12:00:00Z"
}
```

这个例子说明：

- 顶层存的是公共语义信息；
- 它不关心文件内部处理细节；
- 它只关心统一发现和统一展示所需的信息。

---

## 4. 子系统元数据示例

子系统应保存自身专有字段，以及与全局 ID 的映射。

```json
{
  "global_resource_id": "mdams:res:00001234",
  "local_object_id": "44",
  "source_system": "mdams-image",
  "source_object_id": "asset_44",
  "title": "清代山水图",
  "resource_type": "image_2d_cultural_object",
  "status": "ready",
  "file_path": "/app/uploads/shanshui.tiff",
  "mime_type": "image/tiff",
  "file_size": 123456789,
  "technical_metadata": {
    "width": 12000,
    "height": 8000,
    "fixity_sha256": "abc123...",
    "conversion_method": "psb_to_bigtiff"
  },
  "processing_state": {
    "ingest": "done",
    "fixity": "done",
    "preview": "done"
  }
}
```

这个例子说明：

- 子系统保存自己的处理细节；
- 子系统保留必要的展示副本；
- 子系统通过 `global_resource_id` 与顶层对齐。

---

## 5. 图像对象完整示例

下面给出一个更接近 MDAMS 当前实现的图像对象示例。

```json
{
  "global_resource_id": "mdams:res:00001234",
  "source_system": "mdams-image",
  "source_object_id": "asset_44",
  "local_object_id": "44",
  "resource_type": "image_2d_cultural_object",
  "title": "清代山水图",
  "summary": "二维文物图片资源，已完成入库、Fixity 校验、基础元数据提取和 IIIF 预览。",
  "keywords": ["山水", "清代", "图像"],
  "creators": ["张某"],
  "rights": "馆藏内部使用",
  "access_level": "internal",
  "status": "ready",
  "preview_url": "/api/iiif/44/manifest",
  "detail_url": "/assets/44",
  "updated_at": "2026-03-24T12:00:00Z",
  "technical_metadata": {
    "width": 12000,
    "height": 8000,
    "fixity_sha256": "abc123...",
    "ingest_method": "sip_upload",
    "conversion_method": "psb_to_bigtiff"
  },
  "structure": {
    "primary_file": {
      "filename": "shanshui.tiff",
      "mime_type": "image/tiff",
      "file_size": 123456789
    },
    "original_file": {
      "filename": "shanshui.psb",
      "mime_type": "image/vnd.adobe.photoshop",
      "file_size": 234567890
    }
  },
  "process_timeline": [
    "object_created",
    "ingest_completed",
    "fixity_recorded",
    "metadata_extracted",
    "preview_ready"
  ]
}
```

---

## 6. 跨系统关联示例

统一资源 ID 的意义之一，是把不同系统里的资源串起来。

### 示例：图像与文档关联

```json
{
  "relationship_type": "related_document",
  "from_global_resource_id": "mdams:res:00001234",
  "to_global_resource_id": "mdams:doc:00000987",
  "relation_label": "相关研究文档",
  "confidence": 0.95,
  "source": "manual_mapping"
}
```

### 示例：图像与视频关联

```json
{
  "relationship_type": "related_video",
  "from_global_resource_id": "mdams:res:00001234",
  "to_global_resource_id": "mdams:video:00000321",
  "relation_label": "展览视频",
  "confidence": 0.88,
  "source": "connector_sync"
}
```

这些关系可用于：

- 聚合展示；
- 推荐；
- 资源编排；
- 研究关联；
- 跨模态检索。

---

## 7. 接口返回示例

统一元数据也可以用于接口返回。

### 7.1 列表接口返回示例

```json
{
  "items": [
    {
      "global_resource_id": "mdams:res:00001234",
      "resource_type": "image_2d_cultural_object",
      "title": "清代山水图",
      "summary": "已完成基础处理并可预览",
      "status": "ready",
      "preview_url": "/api/iiif/44/manifest",
      "detail_url": "/assets/44"
    }
  ],
  "total": 1
}
```

### 7.2 详情接口返回示例

```json
{
  "global_resource_id": "mdams:res:00001234",
  "resource_type": "image_2d_cultural_object",
  "title": "清代山水图",
  "summary": "二维文物图片资源，已完成入库、Fixity 校验和 IIIF 预览。",
  "technical_metadata": {
    "width": 12000,
    "height": 8000
  },
  "structure": {
    "primary_file": {
      "filename": "shanshui.tiff"
    }
  },
  "access": {
    "preview_url": "/api/iiif/44/manifest"
  }
}
```

---

## 8. 项目当前使用建议

在 MDAMS 当前阶段，建议优先做到以下几点：

1. 新增资源时，同时生成 `global_resource_id`；
2. 顶层与子系统都保存统一 ID；
3. 顶层保存公共字段，子系统保存专有字段；
4. 接口返回统一资源摘要；
5. 所有新增模态都尽量遵循本文件的字段风格。

---

## 9. 后续可继续补充的内容

后续如果项目在元数据方向有新的进展，可以继续补充：

- 更多字段示例；
- 图像/视频/文档/音频的专有字段模板；
- 更细的关系类型；
- 权限字段示例；
- 标签体系示例；
- 多来源同步示例；
- 迁移和映射案例。

---

## 10. 结论

这个示例文档的目标是让 MDAMS 的统一元数据设计不仅“有原则”，而且“可落地、可扩展、可让模型继续理解和生成”。

它是一个面向实际开发的参考模板，而不是静态说明。
