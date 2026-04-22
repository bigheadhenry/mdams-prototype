# 跨子系统最小事件边界（CROSS_SYSTEM_EVENT_BOUNDARY）

## 用途

本文档用于把 MDAMS Prototype 中“事件”这一层的边界正式化。

它不讨论完整 PREMIS 实现，也不直接设计统一事件表，而是回答四个更实际的问题：
- 当前系统里哪些行为已经足以算作事件；
- 哪些行为仍应只保留为状态、派生说明或输出结果；
- 二维、三维、访问/导出、申请交付之间，最小共享事件边界应该怎样划分；
- 下一步应优先把事件边界落到哪里。

## 当前立场

截至 **2026-04-10**，MDAMS 最合理的做法不是直接引入跨子系统统一事件持久化，而是先建立一套**跨子系统最小事件边界**，并优先落到：

1. detail 层的统一事件摘要表达；
2. contract tests 的行为边界；
3. 局部已存在事件对象的术语和分类收口。

当前实现中，这一边界已经有一个轻量共享词表锚点：

- `backend/app/services/event_boundary.py`

它不尝试替代现有的 `asset_detail`、`three_d_production` 或工作流路由，而是把当前可复用的最小事件词汇、二维生命周期步骤、三维生产事件和协作/申请/输出事件边界集中到一处，便于测试和写作同步引用。

这是因为当前系统已经存在足够多的 proto-event 行为，但这些行为仍分散在不同层级：
- 状态字段；
- lifecycle / timeline 描述；
- 三维 `production_records`；
- 访问表示与导出表示的 detail 说明；
- 路由返回中的行为性输出。

如果不先澄清这些层级，后续不论是写论文还是补实现，都很容易把“状态”误写成“事件体系”，或把“输出动作”误做成“必须持久化的领域对象”。

## 一、当前实现中的 4 类“事件相关表达”

### 1. 状态字段

这类表达说明对象现在处于什么状态，但不天然等于“已记录事件”。

当前典型例子：
- `Asset.status`
- `ThreeDAsset.status`
- `ThreeDAsset.web_preview_status`
- `ThreeDAsset.preservation_status`
- `ImageRecord.status`
- `Application.status`

这类字段适合回答：
- 现在对象处于什么阶段？

但并不完整回答：
- 它是如何进入这个阶段的？
- 由谁触发？
- 是否失败、重试或跳过？

### 2. detail 层 lifecycle / timeline 说明

二维 detail 已经有较强的事件化表达，但它目前仍属于**派生解释层**，不是正式事件存储。

当前实现锚点：
- `backend/app/services/asset_detail.py`

当前已经表达的步骤包括：
- `object_created`
- `ingest_completed`
- `fixity_recorded`
- `metadata_extracted`
- `iiif_access_ready`
- `access_derivative_generated`
- `preview_ready`
- `output_ready`

这些步骤非常适合作为**最小事件边界的二维基线**。

### 3. 局部正式事件对象

三维子系统已经有最接近正式事件对象的实现：
- `backend/app/models.py` 中的 `ThreeDProductionRecord`
- `backend/app/services/three_d_production.py`
- `backend/app/services/three_d_detail.py`
- `backend/tests/test_three_d_production.py`

它当前已经记录：
- `stage`
- `event_type`
- `status`
- `actor`
- `description`
- `evidence`
- `metadata_info`
- `occurred_at`

这说明项目并不是“完全没有事件对象”，而是已经在三维链路中形成了一个可用原型。

### 4. 输出层和结果层说明

IIIF Manifest、BagIt 包、交付包这类内容目前更适合被理解为：
- 输出表示；
- 输出结果；
- 可触发事件的对象角色；

而不是天然等于“事件本身”。

当前实现锚点：
- `backend/app/routers/iiif.py`
- `backend/app/routers/downloads.py`
- `backend/app/services/asset_detail.py`

这意味着：
- `manifest_generate` 可以是事件；
- Manifest 不是事件；
- `export_generate` 可以是事件；
- BagIt ZIP 不是事件。

## 二、最小事件边界的总体原则

后续讨论与实现应遵循以下原则：

1. 先区分“状态”“事件”“输出对象”
2. 先统一事件分类和 detail/test 表达，再考虑持久化
3. 只把真正影响对象生命周期、责任边界、保存意识或输出结果的动作定义为事件
4. 不把所有接口动作都抬升为正式事件
5. 保持研究型原型边界，避免过早构建生产级审计体系

## 三、什么应该算事件，什么不应该

### 应优先算事件的动作

满足以下任一条件的动作，应优先进入最小事件边界：

1. 明显改变了对象生命周期
2. 生成了新的访问/导出表示
3. 对后续保存、访问或交付有影响
4. 需要在论文或答辩中作为“关键链路证据”复述
5. 已经在某个子系统中存在稳定实现锚点

### 暂不需要算事件的内容

以下内容当前不应优先做成正式事件：

1. 纯展示型 detail 字段
2. 单纯的过滤、搜索、列表查询
3. 仅表示当前状态但没有过程意义的静态属性
4. 纯前端交互细节，且不影响系统对象生命周期

## 四、按子系统划分的最小事件边界

### A. 二维资产链路

#### 建议纳入最小事件边界

| 类别 | 事件 | 当前锚点 | 建议落点 |
| --- | --- | --- | --- |
| 对象建立 | `object_created` / `asset_register` | `asset_detail.py` lifecycle | detail + contract tests |
| 入库 | `ingest_completed` / `file_receive` | `asset_detail.py` lifecycle | detail + contract tests |
| fixity | `fixity_recorded` | `asset_detail.py` lifecycle、metadata layers | detail + contract tests |
| 元数据 | `metadata_extracted` | `asset_detail.py` lifecycle | detail + contract tests |
| 转换 | `access_derivative_generated` / `conversion_execute` | IIIF access 处理链 | detail + contract tests |
| 访问 | `preview_ready` / `manifest_generate` | Manifest 路由与 detail | detail + output contract tests |
| 导出 | `output_ready` / `export_generate` | 下载与 BagIt 输出 | detail + output contract tests |

#### 暂不建议独立事件化

- 普通列表查看
- 仅用于展示的 metadata 字段读取
- 未改变对象状态的无副作用访问

### B. 图像记录协作链路

#### 建议纳入最小事件边界

| 类别 | 事件 | 当前锚点 | 建议落点 |
| --- | --- | --- | --- |
| 协作提交 | `image_record_submit` | `ImageRecord.status` 与路由动作 | detail / validation tests |
| 协作退回 | `image_record_return` | `ImageRecord.status` 与 `return_note` | detail / behavior tests |
| 绑定确认 | `image_record_bind_confirm` | 绑定/替换流程 | detail / behavior tests |
| 替换确认 | `image_record_replace_confirm` | 替换流程 | detail / behavior tests |

#### 当前边界说明

图像记录链路现在更像“协作流程事件”，不是保存事件。
因此最合适的做法是：
- 先在 detail 和 tests 中统一这些动作语义；
- 暂不先引入单独事件表。

### C. 三维对象链路

#### 建议纳入最小事件边界

| 类别 | 事件 | 当前锚点 | 当前状态 |
| --- | --- | --- | --- |
| 登记 | `register` | `three_d_production.py` | 已有局部事件对象 |
| 文件保存 | `files_saved` | `three_d_production.py` | 已有局部事件对象 |
| 清单生成 | `manifest_built` | `three_d_production.py` | 已有局部事件对象 |
| 发布 | `web_preview` | `three_d_production.py` | 已有局部事件对象 |
| 保存层登记 | `storage_tier` | `three_d_production.py` | 已有局部事件对象 |

#### 当前边界说明

三维链路是当前最接近“正式事件层”的部分。

因此后续最合理的方向不是重做一套，而是：
- 把三维现有事件词汇提升为跨子系统讨论参考；
- 再决定二维和申请/导出是否采用类似表达。

### D. 访问表示与导出表示

#### 建议纳入最小事件边界

| 类别 | 事件 | 当前锚点 | 建议落点 |
| --- | --- | --- | --- |
| 访问表示生成 | `manifest_generate` | `iiif.py`、detail、output tests | detail + contract tests |
| 访问副本生成 | `iiif_access_generate` | IIIF access 处理链 | detail + contract tests |
| 导出包生成 | `export_generate` | `downloads.py`、BagIt tests | detail + contract tests |
| 交付包生成 | `delivery_export` | application/export 链路 | 后续 detail / tests |

#### 边界重点

这里必须明确：
- Manifest / BagIt / 交付包是**对象角色或输出结果**
- `generate` 才是事件

### E. 申请与交付链路

#### 建议纳入最小事件边界

| 类别 | 事件 | 当前锚点 | 建议落点 |
| --- | --- | --- | --- |
| 申请提交 | `application_submit` | `Application.status` / 路由 | detail / behavior tests |
| 审批处理 | `application_review` | 审批路由与状态 | detail / behavior tests |
| 交付导出 | `delivery_export` | 导出链路 | detail / contract tests |

#### 当前边界说明

申请链路最重要的不是先建完整事件表，而是先明确：
- 哪些审批动作是系统关键事件；
- 哪些只是状态迁移的表现。

## 五、建议的跨子系统最小共享词表

### 1. 共享事件分类

建议后续跨子系统统一收口到以下事件分类层：

1. `register`
2. `ingest`
3. `validate`
4. `extract`
5. `convert`
6. `bind`
7. `publish`
8. `export`
9. `review`
10. `preserve`

### 2. 共享事件状态

建议当前只保留最小集合：

1. `pending`
2. `success`
3. `failed`

只有当某链路确实出现重试、跳过、取消的稳定场景时，再继续扩到：
- `retried`
- `skipped`
- `cancelled`

### 3. 共享目标对象类型

建议当前使用：

1. `asset`
2. `image_record`
3. `three_d_asset`
4. `three_d_file`
5. `application`
6. `access_representation`
7. `export_package`

## 六、为什么当前不建议直接引入统一事件表

当前不建议直接上统一事件表，理由有 4 个：

1. **系统语义还没完全统一**
   现在二维、三维、申请、输出层的行为还处在不同成熟度。

2. **detail 层和 tests 还有更高性价比的工作没做完**
   在没有统一 detail 语义之前，先做统一持久化容易把分歧直接固化进表结构。

3. **研究型原型当前更需要“边界诚实”**
   先说明“已有最小事件边界”，比过早声称“已有统一事件系统”更稳。

4. **当前已有局部成功样本**
   三维 `production_records` 已经证明局部事件对象是可行的，但还不足以直接推广为全局统一模型。

## 七、建议的下一步落地顺序

### Step 1
- 把二维 detail、三维 detail、输出层 detail 中涉及事件的术语收口
- 形成统一“事件摘要”表达习惯

### Step 2
- 为二维 lifecycle、三维 production records、IIIF / BagIt 输出结果补更强 contract tests
- 让 tests 先固定“哪些行为应被视为事件边界”

### Step 3
- 再评估是否需要在某个共享 detail schema 或 service 层引入事件摘要对象

### Step 4
- 最后才讨论是否值得把事件摘要推进为跨子系统统一持久化

## 八、对论文的建议表述

如果把这部分写进论文或答辩材料，更准确的说法是：

> MDAMS 当前尚未实现一个跨子系统统一持久化的事件审计层，但已经具备建立最小事件边界的现实基础。二维资产链路通过 lifecycle/detail 表达关键处理步骤，三维链路通过生产记录对象显式保存阶段性事件，而 IIIF 与 BagIt 等输出层则通过可重复生成的访问/导出表示体现结果边界。下一步工作的重点不是直接引入统一事件表，而是先把这些行为在 detail 层与测试层收口为可复用、可验证的最小事件模型。

## 九、当前结论

当前最稳妥、最符合项目原则的结论是：

1. 先定义跨子系统最小事件边界；
2. 先把事件边界落实到 detail / test 层；
3. 暂不直接引入统一事件持久化；
4. 以三维 `production_records` 为局部参考，而不是立即推广为全局标准实现。
