# Translation Between Prototype And Paper

| Engineering Expression | Paper-Oriented Expression | Note |
|---|---|---|
| 数字资源管理原型底座 | a research-oriented digital asset management prototype foundation | 用于说明系统定位，避免直接写成生产平台 |
| Asset / 数字资产 | the core managed digital asset | 作为全文核心对象术语 |
| 上传、处理、预览、导出链路 | a demonstrable end-to-end workflow from acquisition to access and export | 适合引言、方法、评估 |
| IIIF Manifest 生成 | generation of interoperable access representations via IIIF | 强调访问表示层 |
| BagIt 下载 / 导出 | packaging and export through a BagIt-aligned transfer representation | 避免夸大为完整保存打包体系 |
| 图像记录工作流 | a role-split metadata and media coordination workflow | 用于解释 ImageRecord 与文件分离协作 |
| 平台适配器 / 注册表 | a source adapter and aggregation layer for heterogeneous resource systems | 用于平台层叙述 |
| 统一资源目录 | a unified cross-source resource directory | 用于平台聚合描述 |
| 三维对象与版本管理 | management of versioned 3D resource objects | 避免写成完整 3D preservation stack |
| Web 查看器契约 | a viewer contract for web-based rendering and preview eligibility | 适合方法/实现章节 |
| collection_owner 范围过滤 | scope-aware access control based on collection responsibility | 用于权限模型讨论 |
| Playwright 回归测试 | browser-level regression validation of role-based workflows | 用于工程可信度和评估 |
| 具有保存意识 | preservation-aware rather than fully preservation-compliant | 非常关键，避免过度宣称 |
| 选择性标准对齐 | selective and layered standards alignment | 可作为论文方法论关键词 |
| 最小事件边界 / proto-event 词表 | a minimal cross-system event boundary with a shared proto-event vocabulary | 用于说明事件收口而非完整审计体系 |
| 可演示主链路 | a stable and repeatable demonstration workflow | 用于评估维度 |
| 工作日志 | an implementation evidence trail | 可用作研究证据来源说明 |

## Usage Guidance
- 写论文时优先使用右列术语，避免直接沿用过强的产品化措辞。
- 写实现说明、仓库文档或开发任务时可保留左列术语，但需要能映射到右列。
- 涉及 OAIS、PREMIS、NISO Z39.87 时，优先使用 “aligned with”, “informed by”, “partially mapped to”，避免写成 “fully implements”。
