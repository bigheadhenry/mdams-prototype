# 标准化演示主链路

## 目的

本文档把当前 MDAMS 最值得对外演示、对内验收、对论文复用的主链路收敛为 3 条标准化案例链。

每条链路都包含：
- 适用角色与前提条件
- 演示步骤
- 预期输出
- 验证点
- 与对象模型、事件模型和标准支撑材料的对应关系

## 选择原则

当前优先固化的链路必须同时满足：
- 已有真实前后端入口；
- 已有代码或测试支撑；
- 能体现项目的核心研究主张；
- 能被他人相对稳定复现。

基于这个标准，当前最适合固化的 3 条链路是：
1. 二维数字资产主链路
2. 图像记录协作链路
3. 三维对象与统一平台链路

---

## 链路 A：二维数字资产主链路

### 1. 演示目标
证明 MDAMS 不只是文件上传工具，而是能把二维数字资产从接收、校验、访问表示到导出打包组织为一条完整主链路。

### 2. 适用角色
- `system_admin`
- 或具备 `image.view`、`image.upload`、`image.ingest_review` 等权限的演示角色

### 3. 前提条件
- 系统已启动
- 二维资源上传入口可用
- Cantaloupe 与后端可连通
- Mirador 可正常加载 Manifest
- 若演示 BagIt，则原始文件实际存在

### 4. 推荐入口
- 前端：`二维资源`、`入库处理`
- 后端相关：`/api/assets`、`/api/iiif/{id}/manifest`、`/api/assets/{id}/download-bag`

### 5. 演示步骤
1. 以具备二维资源权限的角色登录系统
2. 上传一张二维图像或通过 ingest 入口导入一条资产
3. 在二维资源列表中确认资产出现，状态为 `ready` 或进入可处理状态
4. 打开资源详情，确认 metadata layers、结构信息、访问路径和输出动作可见
5. 打开 Manifest 或直接在 Mirador 中预览
6. 下载当前文件
7. 下载 BagIt 包

### 6. 预期输出
- 一条 `Asset` 记录
- layered metadata
- IIIF Manifest
- 可用的 Mirador 访问路径
- 可下载的原始文件
- 可下载的 BagIt ZIP

### 7. 核心验证点

| 验证点 | 通过标准 |
|---|---|
| 资产是否被系统登记 | 列表页和详情页可见 |
| metadata 是否可读 | 详情页可见 metadata layers / technical metadata |
| IIIF 是否可用 | Manifest 可打开，Mirador 可加载 |
| 访问表示与本体是否区分 | 详情页可见 Manifest / preview / access 路径 |
| BagIt 是否可导出 | `download-bag` 路由返回 ZIP |

### 8. 与研究材料的对应
- 对象模型：[统一对象模型（UNIFIED_OBJECT_MODEL）.md](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/docs/08-研究/统一对象模型（UNIFIED_OBJECT_MODEL）.md)
- 事件模型：[PREMIS事件映射（PREMIS_EVENT_MAPPING）.md](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/docs/08-研究/PREMIS事件映射（PREMIS_EVENT_MAPPING）.md)
- IIIF 支撑：[IIIF清单配置说明（IIIF_MANIFEST_PROFILE）.md](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/docs/08-研究/IIIF清单配置说明（IIIF_MANIFEST_PROFILE）.md)
- BagIt 支撑：[长期保存SIP打包说明（BAGIT_SIP_PROFILE）.md](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/docs/08-研究/长期保存SIP打包说明（BAGIT_SIP_PROFILE）.md)
- OAIS 边界：[OAIS范围对照（OAIS_SCOPE_MAP）.md](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/docs/08-研究/OAIS范围对照（OAIS_SCOPE_MAP）.md)

### 9. 论文复用价值
这是最强的“系统主链路”案例，可直接用作：
- 当前实现与演示链路章节的核心案例
- IIIF / BagIt / OAIS 分层关系的直接证据
- preservation-aware 而非普通上传工具的核心论据

---

## 链路 B：图像记录协作链路

### 1. 演示目标
证明系统已经从“先传文件再补说明”演进为“记录与文件分离协作”的双角色工作流。

### 2. 适用角色
- `image_metadata_entry`
- `image_photographer_upload`
- `system_admin` 也可用于完整演示

### 3. 前提条件
- 已播种测试用户
- 图像记录工作台可访问
- 至少有一个摄影上传人员可被分配
- 绑定上传与基础验证链路可用

### 4. 推荐入口
- 前端：`影像信息录入`
- 后端相关：`/api/image-records/*`

### 5. 演示步骤
1. 以 `image_metadata_entry` 登录
2. 创建一条 `ImageRecord`
3. 补齐必要字段并提交记录
4. 切换到 `image_photographer_upload`
5. 在待上传池中找到该记录
6. 上传文件并执行分析
7. 显式确认绑定或替换
8. 返回详情页确认记录状态、绑定状态和后续验证结果

### 6. 预期输出
- 一条 `ImageRecord`
- 一个由协作记录连接到的 `Asset`
- 绑定前后的验证信息
- 待上传池中的角色化任务视图

### 7. 核心验证点

| 验证点 | 通过标准 |
|---|---|
| 记录是否可提交 | 不完整记录被拒绝，补齐后可提交 |
| 摄影角色是否能看到任务池 | 待上传池中能看到已分配记录 |
| 上传是否需要显式确认 | 不是自动吞并，而是确认绑定/替换 |
| 记录与资产是否分离协作 | `ImageRecord` 先存在，`Asset` 后绑定 |
| 绑定后是否进入后续处理语义 | 详情中可见 validation / pending upload / binding state |

### 8. 与研究材料的对应
- 对象模型：[统一对象模型（UNIFIED_OBJECT_MODEL）.md](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/docs/08-研究/统一对象模型（UNIFIED_OBJECT_MODEL）.md)
- 事件模型：[PREMIS事件映射（PREMIS_EVENT_MAPPING）.md](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/docs/08-研究/PREMIS事件映射（PREMIS_EVENT_MAPPING）.md)
- 工作台说明：[IMAGE_RECORD_WORKBENCH_GUIDE.md](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/docs/03-产品与流程/IMAGE_RECORD_WORKBENCH_GUIDE.md)

### 9. 论文复用价值
这条链路能直接说明：
- 为什么 `ImageRecord` 不是资产本体，而是协作对象
- 为什么当前系统已具备比“上传系统”更强的业务语义
- 为什么后续 PREMIS 事件模型需要覆盖提交、退回、绑定与替换

---

## 链路 C：三维对象与统一平台链路

### 1. 演示目标
证明 MDAMS 不只是二维图像原型，而是已经具备三维对象、版本、多文件资源包和统一平台聚合能力。

### 2. 适用角色
- `three_d_operator`
- 或具备 `three_d.view` / `three_d.upload` / `platform.view` 的角色
- `system_admin` 也可用于完整演示

### 3. 前提条件
- 三维管理页可访问
- 三维上传接口可用
- 至少支持一个模型文件或一个多文件资源包
- 统一平台目录可访问

### 4. 推荐入口
- 前端：`三维管理`、`统一资源目录`
- 后端相关：`/api/three-d/resources`、`/api/platform/resources`

### 5. 演示步骤
1. 以三维角色登录
2. 上传一个三维模型，或上传一个包含模型/点云/倾斜摄影的资源包
3. 在三维管理页查看对象、版本和文件角色
4. 打开详情页，确认 profile、viewer、packaging、production/preservation 信息
5. 对可展示版本打开预览
6. 进入统一平台目录，确认三维来源已被聚合
7. 从统一资源目录进入统一详情或来源详情

### 6. 预期输出
- `ThreeDAsset`
- `ThreeDAssetFile` 集合
- 版本信息、viewer 契约、packaging 信息
- 统一平台中的三维来源摘要与资源记录

### 7. 核心验证点

| 验证点 | 通过标准 |
|---|---|
| 是否存在对象/版本语义 | `resource_group`、`version_label`、`is_current` 等字段可见 |
| 是否支持多文件角色 | `model`、`point_cloud`、`oblique_photo` 等角色可见 |
| viewer 契约是否成立 | viewer summary 或预览入口可见 |
| 平台聚合是否成立 | 统一资源目录可见三维来源 |
| 三维不是独立 demo | 可从平台层进入统一视图 |

### 8. 与研究材料的对应
- 对象模型：[统一对象模型（UNIFIED_OBJECT_MODEL）.md](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/docs/08-研究/统一对象模型（UNIFIED_OBJECT_MODEL）.md)
- 三维 profile：[三维元数据最小配置说明（THREE_D_METADATA_MINIMUM_PROFILE）.md](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/docs/08-研究/三维元数据最小配置说明（THREE_D_METADATA_MINIMUM_PROFILE）.md)
- 工作流指南：[WORKFLOW_GUIDE.md](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/docs/03-产品与流程/WORKFLOW_GUIDE.md)

### 9. 论文复用价值
这条链路可直接支撑：
- “系统已经不是单一二维影像 PoC”的论断
- “统一平台不是空壳，而是多来源聚合层”的论断
- 三维子系统为何应被解释为 minimum viable object/version/file-package framework

---

## 简化验收清单

### 链路 A：二维数字资产
- [ ] 资产可创建并在列表页可见
- [ ] 详情页可见 metadata layers
- [ ] Manifest 可访问
- [ ] Mirador 可加载
- [ ] BagIt 可下载

### 链路 B：图像记录协作
- [ ] 记录可创建
- [ ] 不完整记录不能提交
- [ ] 补齐后可提交
- [ ] 摄影上传角色能看到任务池
- [ ] 上传后需要确认绑定/替换

### 链路 C：三维对象与统一平台
- [ ] 三维对象可上传
- [ ] 版本与文件角色可见
- [ ] viewer/preview 入口可见
- [ ] 统一平台可聚合三维来源
- [ ] 可从平台视图跳转到详情

## 当前工作结论

截至 **2026-04-08**，这 3 条链路已经足够构成 MDAMS 当前最稳定的演示骨架：
- 链路 A 负责证明系统主链路和标准支撑
- 链路 B 负责证明系统具备真实协作语义
- 链路 C 负责证明系统已具有多来源资源底座与平台化趋势
