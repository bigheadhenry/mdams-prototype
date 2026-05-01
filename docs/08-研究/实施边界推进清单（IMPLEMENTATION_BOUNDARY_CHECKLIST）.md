# 实施边界推进清单（IMPLEMENTATION_BOUNDARY_CHECKLIST）

## 用途

本文档用于把当前已经成型的研究语义进一步压缩为“下一轮可以直接进入实现或测试补强”的边界清单。

它不再重复解释对象模型、标准映射或样本结构，而是回答四个更实际的问题：
- 哪些研究语义已经有实现锚点；
- 哪些语义仍主要停留在文档层；
- 哪些差距最适合继续 formalize；
- 下一轮最值得优先推进哪 1 到 2 项。

## 当前判断

截至 **2026-04-08**，MDAMS 已经具备：
- 可解释的统一对象模型；
- 一版 PREMIS 风格最小事件模型；
- 二维与三维的最小 metadata/profile 说明；
- IIIF、BagIt、OAIS 与演示链路材料；
- 样本级 IIIF / BagIt 证据。

当前最真实的缺口，不是“没有研究表达”，而是**研究表达与实施边界之间仍有几处关键断层**。

这些断层已经足够具体，适合继续推进到代码约束、测试契约或更明确的实现边界说明。

## 评估标准

本清单按以下标准筛选优先项：
1. 能直接映射到当前代码结构，而不是纯概念补写；
2. 能为后续实现或测试补强提供明确入口；
3. 能减少论文叙述与系统真实行为之间的落差；
4. 不要求当前立刻做大规模架构重构。

## 边界清单总览

| 项目 | 当前状态 | 主要锚点 | 当前断层 | 推荐动作 | 优先级 |
| --- | --- | --- | --- | --- | --- |
| 统一对象模型 | 文档层稳定，代码层分散 | `backend/app/models.py`、`backend/app/services/asset_detail.py`、`backend/app/services/platform_*` | `Asset` 与 `ThreeDAsset` 仍通过适配层聚合，没有更明确共享契约 | 先补共享字段/行为契约说明或平台级 contract tests，而不是强行统一数据库模型 | P1 |
| PREMIS 风格事件模型 | 文档层明确，局部实现存在 | `backend/app/models.py` 中 `ThreeDProductionRecord`、`backend/app/services/three_d_production.py`、`backend/app/services/asset_detail.py` | 只有三维链路有近似事件表；二维、申请、IIIF、BagIt 仍主要依赖状态字段或派生说明 | 先定义跨子系统最小事件边界和测试入口，再考虑是否新增通用事件持久化 | P1 |
| 二维 profile 完整性 | 已有 metadata 分层与提交校验 | `backend/app/services/metadata_layers.py`、`backend/app/services/image_record_validation.py`、`backend/app/services/reference_import.py` | profile 必填语义分散在构建、提交校验、参考导入完整性检查三处，规则未完全统一 | 先统一 profile 必填规则来源，并补 contract tests | P0 |
| 三维 profile 最小约束 | 已有 metadata 分层与字典 | `backend/app/services/three_d_metadata.py`、`backend/app/services/three_d_dictionary.py`、`backend/tests/test_three_d_dictionary.py` | 当前更像“字段词典存在”，但缺少覆盖上传/详情/平台链路的最小 profile 契约 | 增加工作流级 contract tests，明确哪些字段/角色组合构成“最小可展示三维对象” | P1 |
| 访问表示与导出表示 | 已有真实输出与样本级证据 | `backend/app/routers/iiif.py`、`backend/app/routers/downloads.py`、`backend/app/services/asset_detail.py`、`backend/tests/test_iiif_access_phase1.py` | IIIF Manifest 与 BagIt 已稳定存在，但仍是派生输出，不是第一类持久对象 | 明确“保持派生对象”还是“进入更强结构契约”，并补输出层 contract tests | P1 |

## 优先项详解

### P0. 统一二维 profile 必填规则来源

这是当前最适合进入实现或测试补强的项。

#### 为什么它优先级最高

- 它已经有稳定代码入口，不需要大改架构；
- 它直接影响 `ImageRecord` 提交、参考资源导入与后续论文中的“最小 profile”说法；
- 当前规则存在轻度分叉，已经不是抽象问题，而是实现一致性问题。

#### 现有证据

- `backend/app/services/metadata_layers.py` 定义了二维 profile 与字段集合；
- `backend/app/services/image_record_validation.py` 通过 `PROFILE_REQUIRED_FIELDS` 执行提交前阻断校验；
- `backend/app/services/reference_import.py` 通过 `PROFILE_COMPLETENESS_RULES` 做导入完整性检查；
- `backend/tests/test_image_records.py` 与 `backend/tests/test_reference_import.py` 已经覆盖部分行为。

#### 当前断层

- profile 语义并没有单一来源；
- `movable_artifact` 在不同链路中的“最低完整度”判断并不完全一致；
- 文档里已经把 profile 说成相对稳定的最小配置，但代码层仍更像多处局部规则。

#### 推荐动作

1. 抽出统一的二维 profile 完整性规则来源；
2. 让提交校验与参考导入完整性检查都引用同一组最小约束；
3. 新增 contract tests，覆盖至少 `business_activity`、`movable_artifact`、`immovable_artifact` 三类。

#### 适合落地的文件入口

- `backend/app/services/metadata_layers.py`
- `backend/app/services/image_record_validation.py`
- `backend/app/services/reference_import.py`
- `backend/tests/test_image_records.py`
- `backend/tests/test_reference_import.py`

### P1. 明确跨子系统最小事件边界

这是下一轮第二优先项，但不建议直接跳到“新增通用事件表”。

#### 现有证据

- `backend/app/models.py` 中只有 `ThreeDProductionRecord` 接近正式事件对象；
- `backend/app/services/three_d_production.py` 已为三维写入顺序化事件；
- `backend/app/services/asset_detail.py` 能表达 IIIF / BagIt 等输出动作的派生证据；
- 研究线已经有 `PREMIS事件映射（PREMIS_EVENT_MAPPING）.md`。

#### 当前断层

- 二维、申请、导出和访问链路缺少统一事件边界；
- 同一系统内部同时存在“状态字段”“动作说明”“局部事件表”，语义层级不完全一致；
- 论文中若直接把当前系统写成“已有统一事件体系”会过度表述。

#### 推荐动作

1. 先定义“哪些动作必须算事件，哪些只保留为状态或派生说明”；
2. 优先从 detail 层和测试层收口事件词表；
3. 只有在需要跨子系统审计或保存追踪时，再评估是否引入通用事件持久化。

#### 适合落地的文件入口

- `backend/app/models.py`
- `backend/app/services/three_d_production.py`
- `backend/app/services/asset_detail.py`
- `backend/tests/test_three_d_production.py`
- 后续新增跨子系统 detail / contract tests

### P1. 为三维最小 profile 建立工作流级契约

#### 现有证据

- `backend/app/services/three_d_metadata.py` 已有分层 metadata 构建；
- `backend/app/services/three_d_dictionary.py` 与 `backend/tests/test_three_d_dictionary.py` 已定义字段词典；
- 三维详情与统一平台链路已经存在真实消费路径。

#### 当前断层

- 目前更偏向“字段可列举”，而不是“工作流级最小 profile 已被系统约束”；
- 还缺“某类三维对象在上传、详情、平台聚合时应至少稳定暴露哪些字段/文件角色”的契约测试。

#### 推荐动作

1. 以 `model` 和 `package` 两类 profile 为主，先定义最小工作流约束；
2. 补 detail / platform 级 contract tests，而不是先扩更多字段；
3. 保持“研究原型可解释”优先，不追求过度 formalization。

### P1. 为访问表示与导出表示建立更强输出契约

#### 现有证据

- IIIF Manifest 已由 `backend/app/routers/iiif.py` 动态生成；
- BagIt 导出已由 `backend/app/routers/downloads.py` 输出；
- `backend/tests/test_iiif_access_phase1.py` 已覆盖部分 IIIF / BagIt 行为；
- `docs/08-研究/IIIF清单样本（IIIF_MANIFEST_SAMPLE）.md` 与 `BagIt样本结构（BAGIT_SAMPLE_STRUCTURE）.md` 已提供样本级证据。

#### 当前断层

- 访问表示与导出表示在对象模型中已经被清楚区分，但代码里仍主要停留在 route/detail 派生层；
- 这不是错误，但需要更明确写成“受控派生输出”，并在测试上把边界钉住。

#### 推荐动作

1. 明确 IIIF / BagIt 保持派生对象而非持久化对象；
2. 围绕输出字段、文件选择、权限与失败模式补更强 contract tests；
3. 在论文里把它表述为“可重复生成的访问/导出表示”，而不是“独立对象仓储”。

### P1. 为统一对象模型增加共享契约而非共享表

#### 当前判断

统一对象模型已经足够支撑研究叙述，但当前不值得为了“看起来统一”而重构 `Asset` 与 `ThreeDAsset`。

更合适的推进方式是：
- 维持分子系统模型；
- 在平台聚合层明确共享字段和动作契约；
- 用平台/detail 层测试去固化这种“语义统一、存储分治”的结构。

## 下一轮最推荐推进的 2 项

1. **二维 profile 必填规则统一**
   - 最容易直接进入服务层和测试层；
   - 能立刻减少研究语义与实现行为的分叉；
   - 对论文里“最小 profile”表达最有帮助。

2. **访问表示 / 导出表示 contract tests**
   - 当前实现已经稳定，补强成本低；
   - 能把 IIIF / BagIt 从“有样本说明”推进到“有测试边界”；
   - 对演示、论文和后续重构都最稳。

PREMIS 风格跨子系统事件边界应作为紧随其后的第三项，而不是抢在前两项之前大动数据库结构。

## 下一轮实现或测试摘要

如果下一轮进入代码层，建议按以下顺序推进：

1. 统一二维 profile 完整性规则来源；
2. 补二维提交校验与参考导入共享 contract tests；
3. 补 IIIF / BagIt 输出层 contract tests；
4. 再决定是否需要跨子系统事件词表或 detail 层事件对象。

这个顺序的好处是：
- 先固化“当前已经存在但语义分散”的部分；
- 再补“当前已经稳定输出但测试边界不足”的部分；
- 最后才碰“潜在需要结构演进”的事件层。

## 可直接进入论文讨论/局限章节的表述

当前 MDAMS Prototype 已经形成统一对象模型、最小事件模型、二维与三维 metadata/profile 框架以及 IIIF / BagIt 输出证据，但这些语义并未全部以统一持久化模型或完整契约测试的形式固化到系统内部。更准确的说法是：该原型已经建立了足够稳定的研究表达与局部实现锚点，下一步工作的重点不是继续横向扩展功能，而是把 profile 约束、输出层契约和跨子系统事件边界进一步推进到更明确的实施与验证层。
