# IIIF清单样本（IIIF_MANIFEST_SAMPLE）

## 目的

本文档提供一个基于当前 `backend/app/routers/iiif.py` 组装逻辑的代表性 IIIF Manifest 样本，并对关键字段进行注释。

它的用途是：
- 作为论文中的样本级证据；
- 作为演示时的结构说明；
- 与 [IIIF清单配置说明（IIIF_MANIFEST_PROFILE）.md](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/docs/08-研究/IIIF清单配置说明（IIIF_MANIFEST_PROFILE）.md) 配套。

## 样本来源

本样本根据以下实现锚点整理：
- [iiif.py](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/backend/app/routers/iiif.py)
- [iiif_access.py](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/backend/app/services/iiif_access.py)
- [test_asset_visibility.py](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/backend/tests/test_asset_visibility.py)

## 代表性 Manifest 样本

```json
{
  "@context": "http://iiif.io/api/presentation/3/context.json",
  "id": "http://localhost:3000/api/iiif/2001/manifest",
  "type": "Manifest",
  "label": {
    "en": ["hidden.jpg"],
    "zh-cn": ["hidden.jpg"]
  },
  "summary": {
    "en": ["MDAMS asset 2001"],
    "zh-cn": ["MDAMS asset 2001"]
  },
  "homepage": [
    {
      "id": "http://localhost:3000/api/assets/2001",
      "type": "Text",
      "label": {
        "en": ["MDAMS Asset Detail"],
        "zh-cn": ["MDAMS Asset Detail"]
      },
      "format": "text/html"
    }
  ],
  "metadata": [
    {
      "label": {"en": ["Asset ID"]},
      "value": {"en": ["2001"]}
    },
    {
      "label": {"en": ["Resource ID"]},
      "value": {"en": ["image_2d:2001"]}
    },
    {
      "label": {"en": ["Title"]},
      "value": {"en": ["hidden.jpg"]}
    },
    {
      "label": {"en": ["File Size"]},
      "value": {"en": ["128 bytes"]}
    },
    {
      "label": {"en": ["MIME Type"]},
      "value": {"en": ["image/jpeg"]}
    },
    {
      "label": {"en": ["Uploaded At"]},
      "value": {"en": ["2026-04-08T10:00:00Z"]}
    }
  ],
  "items": [
    {
      "id": "http://localhost:3000/api/iiif/2001/canvas/1",
      "type": "Canvas",
      "label": {"en": ["Page 1"]},
      "height": 1000,
      "width": 1000,
      "items": [
        {
          "id": "http://localhost:3000/api/iiif/2001/page/1",
          "type": "AnnotationPage",
          "items": [
            {
              "id": "http://localhost:3000/api/iiif/2001/annotation/1",
              "type": "Annotation",
              "motivation": "painting",
              "target": "http://localhost:3000/api/iiif/2001/canvas/1",
              "body": {
                "id": "http://localhost:8182/iiif/2/hidden.jpg/full/max/0/default.jpg",
                "type": "Image",
                "format": "image/jpeg",
                "service": [
                  {
                    "id": "http://localhost:8182/iiif/2/hidden.jpg",
                    "type": "ImageService2",
                    "profile": "level2"
                  }
                ]
              }
            }
          ]
        }
      ]
    }
  ]
}
```

## 关键字段注释

| 字段 | 当前含义 | 当前实现来源 |
|---|---|---|
| `@context` | IIIF Presentation 3 context | `iiif.py` 固定值 |
| `id` | Manifest 公共地址 | `API_PUBLIC_URL` 或请求上下文 |
| `type` | 固定为 `Manifest` | `iiif.py` |
| `label` | 资产标题或文件名 | layered metadata / `asset.filename` |
| `summary` | 基础摘要 | `iiif.py` |
| `homepage` | MDAMS 资产详情入口 | `iiif.py` |
| `metadata` | 基础系统字段 + layered metadata | `build_iiif_metadata_entries` |
| `Canvas` | 单页图像访问容器 | `iiif.py` |
| `AnnotationPage` | viewer 兼容结构 | `iiif.py` |
| `Annotation` | painting annotation | `iiif.py` |
| `body.id` | 实际图像请求地址 | Cantaloupe IIIF path |
| `body.service` | 图像服务入口 | `CANTALOUPE_PUBLIC_URL` / 请求上下文 |

## 当前可以从样本直接看出的事实

- Manifest 是动态组装的，而不是静态文件
- 当前输出是单资产、单 Canvas 导向
- 图像服务地址与查看器路径已真实连通
- metadata 当前已承载基础对象识别信息

## 当前边界

这是代表性样本，不是从某次运行时导出的冻结 JSON。

如果后续需要更强证据，仍建议补：
- 一份真实运行时导出的 Manifest 文件
- 一张字段级 capability matrix
- 一次查看器兼容性截图或验证记录
