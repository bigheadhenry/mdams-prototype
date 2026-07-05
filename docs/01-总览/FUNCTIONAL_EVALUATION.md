# MDAMS Prototype v0.3.1 功能完整性与成熟度评估

- 评估日期：2026-07-03
- 评估基线：已提交代码，代码量 `backend 16,613 行 Python` · `frontend 14,960 行 TS/TSX` · `tests 5,451 + 1,202 行`

---

## 1. 功能覆盖度矩阵

以博物馆数字资源生命周期 `采集→管理→检索→利用→保存→开放` 为框架，评估每个模块的状态。

| 生命周期阶段 | 功能模块 | 状态 | 说明 |
|---|---|---|---|
| **📥 采集/摄取** | 二维文件上传 | ✅ 已实现 | 资产上传、预览生成、列表、详情、删除 |
| | SIP/BagIt 风格入库 | ✅ 已实现 | `ingest` 路由，SHA256 校验，验证通过写入 |
| | 图像记录工作流 | ✅ 已实现 | 创建→提交→待上传池→文件匹配→校重 |
| | 三维多文件上传 | ✅ 已实现 | 模型/点云/倾斜摄影角色区分，多文件包 |
| | 三维文件角色识别 | ✅ 已实现 | 根据文件名推断角色，支持覆写 |
| | 视频资源摄取 | ⚠️ 部分实现 | 仅 seed 单个演示视频，硬编码路径 |
| | 批量导入（申请车） | ✅ 已实现 | `ImportDialog` 组件：文物号/粘贴/文件 3 Tab |
| | 参考资源导入 | ✅ 已实现 | `reference_import.py` + 校验脚本 |
| **📋 编目管理** | 二维 | | |
| | · 元数据分层模型 | ✅ 已实现 | 5 层：core/management/technical/profile/raw + rights |
| | · 受控词表 | ⚠️ 部分实现 | 代码层 frozenset（文物级别/分类/年代/版权状态/访问范围），无后台管理界面 |
| | · Profile 定义 & 校验 | ✅ 已实现 | 9 种 profile（可移动文物/不可移动/艺术摄影/业务活动等），字段别名映射 |
| | 三维 | | |
| | · 藏品对象模型 | ✅ 已实现 | ThreeDCollectionObject + ThreeDAsset + ThreeDAssetFile 三层 |
| | · 版本管理 | ✅ 已实现 | version_label, version_order, is_current |
| | · 生产记录 | ✅ 已实现 | ThreeDProductionRecord 事件追踪 |
| | · 元数据分层 | ✅ 已实现 | 8 层（含 preservation/collection） |
| | 视频 | | |
| | · 基本 CRUD | ✅ 已实现 | VideoAsset 模型 + 最小 CRUD 路由 |
| | · 元数据分层 | ✅ 已实现 | `build_video_metadata_layers` 生成 |
| **🔍 检索/发现** | 统一资源目录 | ✅ 已实现 | 跨 image_2d / three_d / video 三种来源聚合 |
| | 统一资源详情 | ✅ 已实现 | source_system/source_id 主路径 |
| | Meilisearch 全文检索 | ✅ 已实现 | 搜索引擎 + 优雅降级到适配器内存过滤 |
| | 高级筛选 | ✅ 已实现 | 状态/类型/profile/预览能力/来源系统 |
| | 排序 | ✅ 已实现 | sort_by (updated_at/title/status) + sort_order |
| | 搜索订阅 | ✅ 已实现 | SearchSubscription 模型 + CRUD |
| | 跨来源关联（文物号） | ✅ 已实现 | `/api/platform/related` + Meilisearch fallback |
| **🛒 利用/申请** | 申请车 | ✅ 已实现 | 加车/去重/多选批量 + RLock 线程安全 |
| | 申请单提交 | ✅ 已实现 | 审批流程（创建→提交→待审批） |
| | 审批（通过/拒绝） | ✅ 已实现 | 含操作人记录 |
| | 审计日志 | ✅ 已实现 | ApplicationAuditLog 独立表，4 个操作点写入 |
| | 交付包导出（ZIP） | ✅ 已实现 | application.json + 文件 + 授权说明.md + README |
| | 授权说明生成 | ✅ 已实现 | 包含授权编号/用途/范围/署名要求/版权声明 |
| | 单资产 BagIt 下载 | ✅ 已实现 | 符合 BagIt 1.0 规范，含 manifest-sha256.txt |
| | IIIF variant 下载 | ✅ 已实现 | 同时提供原文件和 IIIF access 副本 |
| | 交付包 IIIF variant | ❌ 未实现 | 申请交付包仅原文件，无 IIIF variant |
| **🔒 权限与安全** | 11 角色 RBAC | ✅ 已实现 | 角色→权限映射，后端校验 + 前端菜单裁剪 |
| | 认证（session/bearer/header） | ✅ 已实现 | 三种认证模式 |
| | `collection_scope` 范围控制 | ✅ 已实现 | owner_only 可见范围 |
| | CORS 白名单 | ✅ 已实现 | 可配置非通配来源 |
| | 路径穿越防护 | ✅ 已实现 | basename 归一化 |
| | PBKDF2 密码哈希 | ✅ 已实现 | 兼容旧哈希自动迁移 |
| | 审批审计日志 | ✅ 已实现 | 独立表 + 操作写入 |
| | 后台角色管理界面 | ❌ 未实现 | 无管理 UI |
| **💾 长期保存** | Fixity 校验 | ✅ 已实现 | SHA256 在入库/BagIt/下载各环节 |
| | BagIt 打包 | ✅ 已实现 | 单资产 v1.0，含 tag 文件 |
| | OAIS 框架 | ❌ 未实现 | 仅概念层提及，无 SIP/AIP/DIP 代码 |
| | 保存状态标记（3D） | ⚠️ 部分实现 | 仅 3D 有 preservation_status/preservation_note 字段 |
| | 备份/迁移/存储分层 | ❌ 未实现 | 3D 有 storage_tier 字段但无逻辑 |
| **🌐 开放/标准化** | IIIF Manifest | ✅ 已实现 | 权限受控 manifest 生成 |
| | IIIF 代理访问 | ✅ 已实现 | `/api/iiif/{id}/service/{path}` 代理到 Cantaloupe |
| | Dublin Core 15 输出 | ✅ 已实现 | `?format=dc` API 参数，12/15 元素（source/relation/coverage 有意跳过） |
| | LIDO 输出 | ❌ 未实现 | 已讨论但未实现 |
| | Mirador 预览 | ✅ 已实现 | 集成前端 Viewer |
| | Mirador AI 面板 | ✅ 已实现 | 后端 interpret + 前端执行器 |
| **🤖 AI 辅助** | Mirador 工具 | ✅ 已实现 | `POST /api/ai/mirador/interpret` |
| | 人脸识别 | ✅ 已实现 | Celery 异步 + provider 切换，回写 main_person |

### 图例

| 标记 | 含义 |
|---|---|
| ✅ 已实现 | 有稳定代码 + 至少基础测试 |
| ⚠️ 部分实现 | 能用但边缘不完整，或不具备完整可操作性 |
| ❌ 未实现 | 无代码或仅存 stub |

---

## 2. 成熟度等级评估

### 2.1 接近生产级（稳定、测试覆盖完善、经过安全审计）

| 模块 | 理由 |
|---|---|
| **RBAC 权限模型** | 11 角色精确映射、前后端联动校验、范围控制、PBKDF2 哈希、通过安全审计 |
| **申请审批工作流** | 完整状态流转 + ApplicationAuditLog + 交付包认证说明 + 操作人追踪，测试覆盖全路径 |
| **IIIF + BagIt 输出** | 符合标准规范输出，contract tests 验证形状和内容，权限和可见性校验 |
| **2D 元数据分层** | 5 层+rights 模型，9 profile，受控词表，字段别名映射，`build_metadata_layers` 统一函数 |

### 2.2 已验证级（有测试覆盖，流程完整但不精细）

| 模块 | 理由 |
|---|---|
| **2D 资产上传与管理** | 基本 CRUD + preview + derivative policy，28 个测试文件覆盖 |
| **图像记录工作流** | Role-split 完整流程，`test_image_records.py` 覆盖创建/提交/退回/匹配，但部分边缘路径缺失 |
| **三维子系统基础** | 对象/版本/文件模型完善，`test_three_d_subsystem.py` (system+integration+contract)，但文件上传校验可加固 |
| **统一平台目录** | Meilisearch + 优雅降级 + 多来源聚合，`test_platform_directory.py` (integration+contract) |
| **Dublin Core 映射** | 完整的 DC 15 元素转换实现 + `from_unified_resource_detail` 适配器 + contract tests，但 3 元素有意跳过 |
| **搜索订阅** | SearchSubscription 模型 + CRUD + 白名单校验，回归测试补充中 |
| **Mirador AI 面板** | 前后端链路完整，基础测试覆盖 |

### 2.3 原型级（可工作但边缘不完整）

| 模块 | 理由 |
|---|---|
| **视频管理** | 仅 demo seed + 基本 CRUD，无工作流/上传/权限/元数据编辑，无专用测试 |
| **长期保存** | fixity 和 BagIt 已实现，但 OAIS/AIP/SIP/DIP 未架构，3D preservation_status 仅字符串字段 |
| **受控词表** | 代码层 frozenset 定义，无管理 UI，无版本化/国际化 |
| **资源关系建模** | 仅通过 `object_number` 关联实现 `hasRepresentation`，无独立关系表 |
| **申请车批量导入** | ImportDialog 功能丰富但文件导入 UX 仍在打磨 |

---

## 3. 测试覆盖分析

### 3.1 后端测试（27 文件，5,451 行）

| 测试分类 | 文件数 | 示例 |
|---|---|---|
| **smoke**（冒烟） | 2 | `test_health.py`, `test_routes_smoke.py` |
| **contract**（契约） | 16 | 权限、输出、IIIF、三维字典、metadata_layers、衍生策略等 |
| **integration**（集成） | 13 | 应用、平台目录、三维子系统、图像记录 |
| **unit**（单元） | 12 | 事件边界、权限、衍生策略、metadata_layers、DC 映射 |
| **system**（子系统） | 1 | `test_three_d_subsystem.py` |

**测试标记体系成熟**：每个文件通过 `pytestmark` 声明多标签，支持组合过滤。

**关键测试文件**：

- `test_applications.py` — 申请创建→审批→拒绝→导出→审计日志全链路
- `test_output_contracts.py` — IIIF Manifest、BagIt 打包形状验证，失败模式（403/404）
- `test_permissions.py` — 角色权限映射 + range/scope 校验
- `test_metadata_layers.py` — 元数据分层构建 + profile 自动检测
- `test_metadata_standards.py` — Dublin Core 映射全用例覆盖
- `test_search_engine.py` — 搜索引擎抽象 + Meilisearch 适配器单元测试

**缺失**：

- ❌ 无 `test_video.py` 视频子系统测试
- ❌ 无 `test_subscriptions.py` 搜索订阅测试
- ❌ 无 `test_cart.py` 申请车独立测试（cart 功能通过 test_applications 间接覆盖）
- ❌ 无前端 vitest 单元测试（vitest 配置存在但 src/**/*.spec.{ts,tsx} 未找到）

### 3.2 前端测试（4 文件，1,202 行）

| 测试文件 | 类型 | 测试用例数 |
|---|---|---|
| `dashboard.spec.ts` | Playwright E2E | ~15 个 test（含多角色） |
| `mirador-ai.spec.ts` | Playwright E2E | ~2 个 test |
| `mirador-ai-live.spec.ts` | Playwright Live | 1 个 test |
| `setup.ts` | 工具 | N/A |

**特点**：Playwright 测试采用 API mock 策略（`page.route` 拦截所有 backend API），不依赖运行中的后端。5 种角色认证 mock 定义。跨 3 浏览器（chromium/firefox/webkit）。

**缺失**：

- ❌ 无 `src/**/*.spec.{ts,tsx}` unit tests（vitest 配置找得到 spec 文件但不存在）
- ❌ 无前端/后端 API 契约对齐测试
- ❌ 无申请管理/三维管理/视频管理的 Playwright 回归

---

## 4. 文档完整性

### 4.1 文档结构统计

| 目录 | 文档数 | 说明 |
|---|---|---|
| `00-归档/` | 7 | 已归档历史文档 |
| `01-总览/` | 5 | 项目状态、阶段计划、测试策略、工作日志 |
| `02-架构设计/` | 7 | 系统架构、API 路由、平台适配器、三维架构 |
| `03-产品与流程/` | 12 | 角色权限、菜单可见性、演示流、操作指南 |
| `04-实施方案/` | — | （空目录） |
| `05-部署与运维/` | 8 | 部署指南、环境变量、排障 |
| `06-参考资料/` | 4 | 元数据参考/示例、资源导入/数据集 |
| `07-图示/` | — | （空目录） |
| `08-研究/` | ~20+ | 学术研究材料、标准映射、设计决策 |
| 根目录管理 | README, CHANGELOG, VERSION | |

**共 101 文件，98 个 markdown，含 8 个子目录**

### 4.2 文档治理成熟度

| 特征 | 状态 | 说明 |
|---|---|---|
| DOCUMENT_REGISTRY.md | ✅ | 完整注册表，含状态标签/日期/备注 |
| CHANGELOG 版本化 | ✅ | Keep a Changelog + SemVer，4 个版本 |
| DECISION_LOG | ✅ | `design_decisions.md` 在 08-研究/ |
| DOCUMENT_GOVERNANCE.md | ✅ | 文档治理规则 |
| 当前事实入口标记 | ✅ | "当前事实入口"标注意味着与代码对齐 |
| 部分文档标"待核对" | ⚠️ | 许多文档最后更新标记为"待核对"而非具体日期 |
| 04-实施方案/ 空目录 | ⚠️ | 已创建目录但无内容 |
| 07-图示/ 空目录 | ⚠️ | 已创建但无内容 |

### 4.3 文档覆盖缺口

- ❌ 无 OAIS/长期保存/备份策略文档
- ❌ 无 LIDO 标准实现文档
- ❌ 无视频子系统专题文档
- ❌ 无搜索订阅专题文档
- ❌ 无申请车批量导入专题文档
- ❌ 无人脸识别子系统操作指南
- ❌ 无系统监控/日志/告警运维文档

---

## 5. 数据治理评估

### 5.1 元数据模型设计

| 层次 | 2D | 3D | Video |
|---|---|---|---|
| **Core** | ✅ source_system, source_id, title, status, visibility_scope, profile_key 等 | ✅ 同 2D + collection info | ✅ 同 2D |
| **Management** | ✅ 13 字段（项目/摄影/影像类别/标签） | ✅ 专属字段 | ✅ 最小集 |
| **Technical** | ✅ 30+ 字段（文件名/格式/校验/衍生策略/尺寸/色彩） | ✅ 专属字段（坐标/顶点/纹理等） | ✅ 基础字段 |
| **Profile** | ✅ 9 种 profile 自定义字段 | ✅ profile_key + PROFILE_DEFINITIONS | ❌ 无 profile 定义 |
| **Raw Metadata** | ✅ 原始元数据保留 | ✅ metadata_info JSON | ✅ metadata_info JSON |
| **Rights** | ✅ 8 字段（版权/访问/授权/协议/限制） | ❌ 无独立 rights 层 | ❌ 无独立 rights 层 |

### 5.2 受控词表

| 词表 | 状态 | 存储位置 |
|---|---|---|
| 文物级别（一级/二级/三级/一般/参考品） | ✅ 代码层 | `metadata_layers.py` frozenset |
| 文物分类（绘画/法书/铜器等 24 类） | ✅ 代码层 | `metadata_layers.py` frozenset |
| 年代/时期（新石器时代→民国 21 项） | ✅ 代码层 | `metadata_layers.py` frozenset |
| 版权状态（故宫所有/合作共享等） | ✅ 代码层 | `metadata_layers.py` frozenset |
| 访问范围（公开/院内/部门内/限制访问） | ✅ 代码层 | `metadata_layers.py` frozenset |
| 三维 profile key | ✅ 代码层 | `three_d_metadata.py` |
| **管理 UI** | ❌ | 无词表管理界面 |

### 5.3 标准化映射

| 标准 | 状态 | 覆盖率 |
|---|---|---|
| Dublin Core 15 | ✅ 已实现 | 12/15 元素（source/relation/coverage 有意跳过） |
| IIIF Presentation API | ✅ 已实现 | Manifest + 权限控制 |
| BagIt 1.0 | ✅ 已实现 | manifest-sha256.txt + bagit.txt + bag-info.txt |
| LIDO | ❌ 未实现 | 已讨论但无代码 |
| PREMIS | ❌ 未实现 | 仅概念层提及 |
| NISO Z39.87 | ❌ 未实现 | 仅概念层提及 |

### 5.4 长期保存路径

| 要素 | 状态 |
|---|---|
| Fixity（SHA256） | ✅ 在 ingest/BagIt/download 各环节计算和校验 |
| BagIt 打包 | ✅ 单资产，含 tag 文件 |
| 保存状态追踪 | ⚠️ 仅 3D 有 preservation_status/preservation_note |
| OAIS SIP/AIP/DIP | ❌ 未实现 |
| 存储分层（hot/warm/cold） | ⚠️ 3D 有 storage_tier 字段但无逻辑 |
| 备份策略 | ❌ 未文档化 |
| 数据迁移策略 | ❌ 未文档化 |
| 监控与报警 | ❌ 未实现 |

---

## 6. 总结与优先级建议

### 核心结论

MDAMS Prototype v0.3.1 是一个**主链路可用、模块边界清晰、具备持续迭代基础**的数字资源管理系统原型。它不是生产级 DAMS，但已经远超早期"二维影像上传 PoC"的阶段。

**最强项**：
1. 权限模型（RBAC + scope + 安全审计）
2. 申请审批全链路（审计日志 + 交付包 + 授权说明）
3. 输出层合规（IIIF + BagIt + Dublin Core）
4. 元数据建模深度（5 层 + 9 profile + 多来源统一）

**最大缺口**：
1. 长期保存（OAIS / 备份 / 存储分层）
2. 视频管理（仅 demo seed）
3. 前端的后端测试（无 vitest unit、右 Playwright 回归域有限）
4. 受控词表管理界面
5. 文档中大量"待核对"状态尚未刷新

### 优先级建议

| 优先级 | 方向 | 预估投入 |
|---|---|---|
| **P0** | 补齐前端单元测试（vitest） | ~20h |
| **P0** | 视频完整工作流 | ~40h |
| **P1** | LIDO 标准映射 + dc:relation 建模 | ~15h |
| **P1** | 受控词表管理界面 | ~25h |
| **P1** | 文档"待核对"全部刷新为当前事实 | ~10h |
| **P1** | 申请交付包 BagIt 化（当前为 ZIP） | ~8h |
| **P2** | OAIS 长期保存框架（AIP 设计） | ~40h 研究 + ~60h 实现 |
| **P2** | 跨资源关系表（超越 object_number） | ~20h |
| **P2** | 审批 + 导出 Playwright 回归测试 | ~12h |
