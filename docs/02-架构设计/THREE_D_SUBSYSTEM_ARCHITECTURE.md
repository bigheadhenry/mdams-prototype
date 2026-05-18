# 三维子系统架构说明

- 最后核对日期：2026-05-17
- 核对口径：仅以已提交代码中的稳定实现为准，不纳入当前工作区未提交改动
- 核对范围：`backend/app/routers/three_d.py`、`backend/app/services/three_d_*`、`backend/app/platform/three_d_source.py`、`frontend/src/components/ThreeDManagement.tsx`、`frontend/src/components/ThreeDViewer.tsx`

## 1. 目标

本文件用于说明当前三维子系统已经落地的对象模型、文件组织、展示状态和平台接入方式。

## 2. 当前三维子系统定位

三维子系统当前不是“单个模型文件上传页”，而是一个围绕对象、版本、文件角色和 Web 预览状态组织的资源管理子系统。

但需要注意：当前 `ThreeDAsset` 在实现上仍同时承担了“三维对象”“模型等级/表现”“版本”“文件包”等多重语义。后续目标模型应收敛为：

```text
藏品对象 Collection Object
  -> 三维数字对象 Three-D Digital Object
      -> 模型表现 / 表现版本 Representation
          -> 文件包 Files
```

截至当前稳定实现，同一件藏品下的原始保存级模型、Web 展示级模型、移动端轻量模型、高精度研究模型，已经在前端管理页和统一平台来源适配器中按对象级分组展示；但数据库层仍主要复用 `ThreeDAsset` 等现有结构，并未新增独立 `ThreeDDigitalObject` 表。

## 3. 当前核心概念

### 3.1 三维资源对象

当前三维资源的核心是对象而不是单文件。

对象层负责承载：

- 资源标题
- 资源组
- 版本信息
- 关联藏品或对象信息
- 预览状态

当前前端与统一平台已经把“三维数字对象”作为对象级展示单元；当前 `ThreeDAsset` 更适合被过渡理解为某个三维数字对象下的“模型表现/资源包”。完整规范见 `../03-产品与流程/THREE_D_OBJECT_MODEL_AND_PLATFORM_VIEW.md`。

### 3.2 多文件资源包

当前三维资源支持多文件组织，常见角色包括：

- 模型
- 点云
- 倾斜摄影
- 其他补充文件

这意味着一个三维对象可以由多个文件共同组成。

在目标模型中，多文件资源包属于某一个模型表现。例如同一藏品三维数字对象下可以同时存在：

- 原始保存级表现：模型、点云、贴图、采集报告、质检报告
- Web 展示级表现：轻量化 GLB、压缩贴图
- 高精度研究级表现：高精度模型、点云、处理报告

### 3.3 版本与展示状态

当前系统把版本信息与 Web 预览状态分开表达。

这有助于区分：

- 原始保存对象
- 当前展示版本
- 是否已具备 Web 预览能力

后续需要进一步区分 `representation_type` 与 `version_label`：

- `representation_type` 表示模型用途或等级，例如 `original_master`、`web_display`、`mobile_lightweight`、`research_detail`
- `version_label` 表示该用途/等级下的真实版本，例如 `v1`、`v2`、`2026-05`

## 4. 当前后端结构

后端三维能力主要分散在以下部分：

- `routers/three_d.py`
- `services/three_d_detail.py`
- `services/three_d_metadata.py`
- `services/three_d_dictionary.py`
- `services/three_d_production.py`
- `services/three_d_storage.py`

它们分别覆盖：

- 路由入口
- 详情构建
- 元数据层
- 字典输出
- 生产链路记录
- 存储与文件角色处理

## 5. 当前前端结构

前端三维相关入口主要包括：

- `ThreeDManagement.tsx`
- `ThreeDViewer.tsx`
- `ThreeDTurntablePreview.tsx`

它们当前承担：

- 三维资源管理
- 数字对象概览
- 对象分组与模型表现展开
- 资源包上传
- 对象详情抽屉
- Web 预览入口
- 轻量旋转预览

## 6. 当前统一平台接入

三维子系统当前已经通过来源适配器接入统一平台。

这意味着三维对象可以：

- 出现在统一资源目录
- 被统一详情接口聚合
- 与二维资源一同参与平台筛选

统一平台当前默认展示粒度已经是“三维数字对象”，而不是每一个模型表现或每一个文件。平台来源适配器会按 `collection_object_id + resource_group` 聚合 `ThreeDAsset` 记录，并输出：

- `resource_type = three_d_digital_object`
- `source_id = object-{anchor_asset_id}`
- 对象级 `preview_enabled`
- 默认预览表现
- 表现列表
- 文件数与表现数摘要
- 对象级 actions

旧的数字 `source_id` 仍可被适配器兼容解析。

## 7. 当前已实现范围

按当前代码结构，三维子系统已具备：

- 三维对象读取与详情返回
- 多文件角色建模
- 版本标签与排序信息
- 预览状态判断
- 元数据层输出
- 轻量预览数据输出
- 生产链记录
- 平台来源适配
- 平台侧三维数字对象级聚合

## 8. 当前边界

当前三维子系统虽然已具备主骨架，但仍有边界：

- Web 预览格式兼容性还可继续增强
- 更复杂的生产过程和长期保存语义仍可继续细化
- 三维对象与二维对象之间的统一模型仍在平台层逐步收敛
- 当前资源记录与三维数字对象之间还缺少独立数据库实体，同一藏品下不同等级模型仍主要依赖 `collection_object_id + resource_group` 聚合
- `representation_type` 主要从元数据或 `version_label` 推断，尚未成为稳定表字段

## 9. 关联文档

- `PLATFORM_SOURCE_ADAPTERS.md`
- `API_ROUTE_MAP.md`
- `../03-产品与流程/WORKFLOW_GUIDE.md`
- `../03-产品与流程/THREE_D_OBJECT_MODEL_AND_PLATFORM_VIEW.md`
