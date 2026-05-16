# 三维对象模型与统一平台展示规范

## 1. 背景

当前三维子系统已经支持三维资源上传、多文件资源包、版本字段、Web 预览状态和统一平台接入。但在业务语义上，现有 `ThreeDAsset` 同时承担了“完整三维对象”“某个模型等级”“某个版本”“一组具体文件包”等多重含义。

这种结构在测试和原型阶段可用，但在真实藏品管理场景中会带来一个明显问题：同一件藏品下的原始模型、展示级模型、轻量模型、高精度研究模型会在列表和统一检索中被拆成多个平级资源，用户无法直接看到它们属于同一个藏品三维数字对象。

因此，后续三维模块需要从“资源记录列表”升级为“藏品三维数字对象管理”。

## 2. 目标对象层级

三维模块推荐采用四层结构：

```text
藏品对象 Collection Object
  -> 三维数字对象 Three-D Digital Object
      -> 模型表现 / 表现版本 Representation
          -> 文件包 Files
```

### 2.1 藏品对象

藏品对象是三维数据关联的业务根对象，承载藏品号、藏品名称、藏品类型、收藏单位等信息。

当前系统已有 `ThreeDCollectionObject`，后续应继续强化它与正式藏品库或统一对象库的关系。

### 2.2 三维数字对象

三维数字对象表示“某件藏品的一组三维数字化成果”，而不是某一个具体模型文件。

它应承载：

- 所属藏品对象
- 三维对象标题
- 三维项目或采集批次
- 对象级摘要、关键词、责任部门
- 当前默认展示表现
- 对象级保存状态
- 对象级生产链摘要

示例：

```text
陶罐 A 三维数字对象
藏品号：DEMO-3D-VASE-0001
采集批次：3D-DEMO-2026-001
包含：原始保存级、Web 展示级、高精度研究级
```

### 2.3 模型表现 / 表现版本

模型表现是同一三维数字对象下不同用途、等级或发布形态的资源包。

推荐使用 `representation_type` 区分用途：

| 类型 | 含义 | 是否默认展示 |
|---|---|---|
| `original_master` | 原始保存级模型或原始采集包 | 通常否 |
| `web_display` | Web 展示级模型 | 通常是 |
| `mobile_lightweight` | 移动端或低带宽轻量模型 | 视场景 |
| `research_detail` | 高精度研究/内部使用模型 | 视权限 |
| `derivative` | 其他派生模型 | 视规则 |

`representation_type` 与 `version_label` 不能混用：

- `representation_type` 回答“这是哪种用途或等级的模型？”
- `version_label` 回答“这个用途/等级下的第几个版本？”

例如：

```text
original_master / v1
web_display / v2
mobile_lightweight / v1
research_detail / 2026-05
```

### 2.4 文件包

文件包属于某一个模型表现，按文件角色组织具体文件。

常见文件角色包括：

- `model`：模型文件，如 GLB、glTF、OBJ、FBX、STL、USDZ
- `point_cloud`：点云文件，如 PLY、LAS、LAZ、XYZ、PTS
- `texture`：贴图文件
- `oblique_photo`：倾斜摄影或参考图像
- `support`：采集说明、处理报告、质检报告等辅助文件
- `other`：其他文件

一个模型表现可以包含多个文件角色。例如 Web 展示级可能只有一个 GLB 和压缩贴图，原始保存级可能包含 glTF、BIN、贴图、点云、采集报告和质检报告。

## 3. 当前实现到目标模型的映射

当前代码中可按以下方式过渡理解：

| 当前结构 | 过渡语义 | 目标结构 |
|---|---|---|
| `ThreeDCollectionObject` | 藏品或对象线索 | 藏品对象 |
| `resource_group` | 临时数字对象分组 | 三维数字对象标识 |
| `ThreeDAsset` | 某一资源记录 | 模型表现 / 资源包 |
| `version_label` | 版本标签，当前混合了用途和版本 | 真实版本号 |
| `is_web_preview` / `web_preview_status` | Web 预览状态 | 表现级发布状态 |
| `ThreeDAssetFile` | 文件记录 | 文件包明细 |

短期内可以继续复用 `ThreeDAsset`，但在文档和界面语义上应把它称为“模型表现”或“资源包”，避免继续把它称为完整的三维对象。

中期建议新增实体：

```text
ThreeDDigitalObject
  id
  collection_object_id
  digital_object_key
  title
  project_name
  capture_batch
  summary
  keywords
  default_representation_id
  preservation_status
```

并将 `ThreeDAsset` 改造或重命名为：

```text
ThreeDRepresentation
  id
  digital_object_id
  representation_type
  version_label
  version_order
  is_current
  is_web_preview
  web_preview_status
  storage_tier
  preservation_status
```

## 4. 三维管理页展示规则

三维管理页默认不应展示平铺的资源记录列表，而应采用对象树或分组视图。

推荐层级：

```text
藏品对象
  三维数字对象
    模型表现 / 版本
      文件包
```

列表首屏建议展示“三维数字对象”级别信息：

- 标题
- 藏品号 / 藏品名称
- 采集批次或项目
- 模型表现数量
- 文件总数
- 当前 Web 展示级
- 保存状态
- 最近更新时间

展开后展示模型表现：

```text
陶罐三维数字对象
  [原始保存级] original_master / v1
    模型 1、点云 1、贴图 1、报告 1
    Web 展示：否
  [Web 展示级] web_display / v1
    GLB 1、贴图 1
    Web 展示：已就绪
  [高精度研究级] research_detail / v2
    GLB 1、点云 1、报告 1
    Web 展示：内部可预览
```

操作规则：

- “打开预览”默认打开当前 `web_display` 且 `web_preview_status=ready` 的表现。
- “下载资源包”应允许选择某个表现下载，不能默认把所有表现混成一个包。
- “查看对象详情”展示对象级元数据、表现列表、文件构成和生产链摘要。
- “查看表现详情”展示某个表现的技术元数据、文件包、预览状态和保存状态。

## 5. 统一平台展示规则

统一检索平台默认显示粒度应为“三维数字对象”，而不是每一个模型表现或每一个文件。

### 5.1 默认检索结果

搜索结果主项建议对应一个三维数字对象：

```text
陶罐三维数字对象
藏品号：DEMO-3D-VASE-0001
资源类型：三维数字对象
可预览：是
包含：原始保存级、Web 展示级、高精度研究级
文件：11 个
来源：三维数据子系统
```

默认动作：

- `打开预览`：打开默认 Web 展示表现
- `查看详情`：进入统一详情页
- `查看来源`：进入三维模块对象详情
- `下载`：进入表现选择或按权限下载默认展示包

### 5.2 统一详情页

统一详情页应在对象级详情中嵌入表现层：

```text
三维表现
- Web 展示级：web_display / v1，可在线预览
- 原始保存级：original_master / v1，不开放 Web 展示，可下载归档包
- 高精度研究级：research_detail / v2，内部研究/对比浏览

文件构成
- 模型文件
- 点云
- 贴图
- 倾斜摄影图像
- 采集/处理/质检报告
```

统一详情的 `preview_enabled` 应取决于对象下是否存在可预览的默认表现，而不是取决于对象下所有表现是否都可预览。

### 5.3 高级检索粒度

为了兼顾管理和审计，统一平台可以提供粒度切换：

| 粒度 | 使用场景 |
---|---|
| 数字对象 | 默认检索、普通浏览、利用申请 |
| 模型表现 | 三维管理员、研究人员比较不同等级模型 |
| 文件 | 审计、质检、下载、保存校验 |

默认粒度必须是“数字对象”，避免同一藏品在检索结果中被拆散。

## 6. API 与适配器建议

统一平台适配器应从当前的：

```text
ThreeDAsset -> UnifiedResourceSummary
```

逐步调整为：

```text
ThreeDDigitalObject -> UnifiedResourceSummary
```

推荐对象级摘要结构：

```json
{
  "source_system": "three_d",
  "resource_type": "three_d_digital_object",
  "title": "陶罐三维数字对象",
  "preview_enabled": true,
  "default_preview_representation_id": 5,
  "representation_count": 3,
  "file_count": 11,
  "representations": [
    {
      "id": 4,
      "representation_type": "original_master",
      "label": "原始保存级",
      "version_label": "v1",
      "preview_enabled": false,
      "file_count": 5
    },
    {
      "id": 5,
      "representation_type": "web_display",
      "label": "Web 展示级",
      "version_label": "v1",
      "preview_enabled": true,
      "file_count": 3
    }
  ]
}
```

## 7. 实施规划

### 阶段一：不改表的语义收敛

目标是在现有表结构上先修正展示与文档语义。

- 将管理页首屏改为按 `collection_object_id + resource_group` 聚合。
- 在前端把 `ThreeDAsset` 展示为“模型表现/资源包”，而不是完整三维对象。
- 在 seed 示例数据中继续保留同一 `resource_group` 下多表现样本。
- 在统一平台适配器中先按 `resource_group` 聚合为对象级结果。
- 在详情中列出同组下全部表现。

### 阶段二：补充表现类型字段

目标是消除 `version_label` 混用。

- 增加 `representation_type` 字段。
- 增加表现类型字典：原始保存级、Web 展示级、移动轻量级、高精度研究级、其他派生。
- 将现有 `original`、`v1-web`、`v2-detail` 等示例迁移为 `representation_type + version_label`。
- 统一 Web 展示选择规则：优先 `web_display`，其次允许人工指定默认展示表现。

### 阶段三：新增三维数字对象实体

目标是形成稳定的数据模型。

- 新增 `ThreeDDigitalObject`。
- 将 `ThreeDAsset` 关联到 `digital_object_id`。
- 将对象级元数据从表现记录中上移到 `ThreeDDigitalObject`。
- 统一平台 `source_id` 指向三维数字对象，而不是具体表现。
- 三维管理页、统一详情页、下载和预览动作都基于对象级聚合重构。

### 阶段四：治理与长期保存完善

目标是支撑生产级管理。

- 对原始保存级、展示级、轻量级、研究级分别制定保存策略。
- 补全采集、处理、发布、质检、保存事件链。
- 支持对象级申请、表现级交付、文件级审计。
- 支持归档包校验、迁移记录和长期保存系统对接。

## 8. 结论

三维模块的核心管理单元应是“藏品三维数字对象”，不同等级的模型应作为该对象下的模型表现，而每个表现再组织自己的模型、点云、贴图和说明文件。

统一平台默认也应展示三维数字对象，而不是平铺所有表现和文件。这样既能保持用户浏览时的对象完整性，也能保留管理员需要的模型等级、版本和文件包管理精度。
