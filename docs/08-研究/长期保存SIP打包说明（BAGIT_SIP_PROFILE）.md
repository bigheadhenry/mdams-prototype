# 长期保存SIP打包说明（BAGIT_SIP_PROFILE）

## 目的

本文档用于明确 MDAMS Prototype 中 BagIt 的角色边界、当前实现锚点、包结构事实和研究表达边界。

截至 **2026-04-08**，它优先回答：
- BagIt 在 MDAMS 中到底承担什么角色；
- 当前代码真实生成了什么样的 bag 结构；
- 它与访问层和一般业务导出层有什么区别；
- 当前可以稳定宣称什么，哪些仍不应过度宣称。

## 一、实现锚点

当前 BagIt 导出最直接的实现锚点是：
- `backend/app/routers/downloads.py`
- `frontend/src/components/AssetDetail.tsx`
- `frontend/src/components/UnifiedResourceDetail.tsx`
- `frontend/src/components/IngestDemo.tsx`
- `docs/08-研究/输出层边界说明（EXPORT_BOUNDARIES）.md`

从 `downloads.py` 可以直接确认：
- 存在 `/assets/{asset_id}/download-bag` 路由；
- 打包对象基于 `Asset`；
- bag 中会创建 `bagit.txt`、`bag-info.txt`、`manifest-sha256.txt`；
- payload 放在 `data/` 目录；
- 若存在独立 IIIF access 副本，会一并进入 payload；
- 最终输出为 ZIP。

这说明当前 BagIt 不是仅停留在研究表述，而是已经落实到可下载、可运行的导出功能。

## 二、当前定位

在 MDAMS 当前设计语境中，BagIt 最适合被限定为：

> **面向长期保存移交语境的、具有真实实现的 SIP-like 打包机制。**

这里故意使用 “SIP-like” 而不是直接宣称“完整 OAIS SIP”，原因是：
- 当前已存在真实打包与校验结构；
- 但尚未把 OAIS 的 SIP / AIP / DIP 体系完整 formalize；
- 也尚未对某个特定接收端 profile 做正式适配声明。

## 三、当前 BagIt 在系统中的位置

从系统分层角度，当前更适合区分以下几层：

1. **资产管理层**：`Asset`、文件、metadata、状态
2. **处理与校验层**：ingest、fixity、metadata extraction、iiif access derivative
3. **访问表示层**：IIIF Manifest、图像服务、Mirador
4. **长期保存移交层**：BagIt ZIP
5. **业务交付层**：申请交付、普通下载、未来通用导出

在这条分层里，BagIt 明确位于：

> **长期保存移交层**

这也是它与 IIIF、普通下载和未来通用导出层的核心区别。

## 四、当前代码事实：Bag 中包含什么

根据 `backend/app/routers/downloads.py`，当前 BagIt ZIP 至少包括：

### 1. Payload
- `data/<original file>`
- 如果存在独立 IIIF access 文件：`data/<iiif access file>`

### 2. Tag files
- `bagit.txt`
- `bag-info.txt`
- `manifest-sha256.txt`

### 3. 当前 bag-info.txt 中稳定出现的字段
- `Source-Organization`
- `Bagging-Date`
- `Payload-Oxum`
- `Original-File`
- `IIIF-Access-File`（条件存在）

### 4. 当前 manifest-sha256.txt 的行为
- 记录原始文件的 SHA256
- 如果存在独立 IIIF access 文件，也会记录其 SHA256

这说明当前实现已经超出“下载一个 ZIP”的程度，而是具有最基本的 bag 结构和 fixity 语义。

## 五、当前最合适的研究表达

在研究与系统说明中，当前最适合写成：

> MDAMS 已实现一个以数字资产为中心的 BagIt ZIP 导出能力，用于将原始对象及其必要访问衍生和校验信息组织为 preservation-aware 的移交包。

如果需要更强调边界，可写成：

> 当前 BagIt 在 MDAMS 中被实现为长期保存移交语境下的 SIP-like 打包机制，而不是访问层输出、内部主对象模型或所有业务导出的统一封装层。

## 六、BagIt 当前不是什么

为避免研究表达混乱，必须明确当前 BagIt 不应被理解为：

### 1. 访问层输出
BagIt 不服务 Mirador 或前端查看体验。

### 2. 所有业务导出的统一答案
它不应默认等同于：
- 普通用户下载；
- 所有交付包；
- 任意批量导出；
- 未来通用业务交换包。

### 3. 系统内部对象总模型
BagIt 是输出层结构，不是内部数据模型。

### 4. 完整 OAIS SIP/AIP/DIP 体系
当前实现有 SIP-like 倾向，但未形成完整 OAIS 信息包体系。

## 七、当前稳定可宣称的能力

### 1. 真实 BagIt ZIP 导出
系统当前有可调用的 BagIt 导出接口，而不是纸面设计。

### 2. fixity 已进入 bag
当前至少会生成 `manifest-sha256.txt`，说明完整性信息已进入包结构。

### 3. 原始对象与访问副本可共同进入包
当前实现允许在独立 access 文件存在时一并打包，这为“保存对象与访问对象的关系”提供了现实证据。

### 4. 包结构边界较清晰
当前至少区分了：
- payload
- tag files
- 原件与 access 衍生的关系

## 八、当前不宜过度宣称的部分

### 1. 不宜宣称已实现完整长期保存系统
BagIt 导出存在，不等于 MDAMS 已是完整长期保存系统。

### 2. 不宜宣称已形成完整 SIP/AIP/DIP 架构
当前更准确的说法是：
- 在 SIP-like 打包上已有实现；
- 但 OAIS 全部信息包与职能域未 formalize。

### 3. 不宜宣称已有接收端 profile 适配
当前尚未明确面向某类长期保存系统的正式接收规范。

### 4. 不宜把所有导出场景都归并到 BagIt
未来业务交付层可能参考 BagIt，但不应直接等同。

## 九、当前缺口

### 1. 真实 bag 样本仍未逐项样本化
虽然代码结构清楚，但文档还没有配一个真实 bag 样例树。

### 2. Payload 范围仍需更清楚边界
当前已知至少包含原件和条件性的 IIIF access 文件，但更多衍生对象、事件摘要和关系文件是否入包仍未 formalize。

### 3. 接收端语境仍偏通用
当前更像通用 preservation-aware bag，而不是某机构明确接收规范下的 bag profile。

## 十、对项目推进的建议

1. 生成一个真实 bag 样本并列出目录树
2. 明确“哪些对象必须入包、哪些对象可选入包、哪些对象不入包”
3. 视需要补一个 bag profile 级说明
4. 在论文中把 BagIt 写成“输出层证据”，而不是“完整保存体系已实现”

## 十一、当前结论

当前 MDAMS 中 BagIt 的最准确定位是：

> 一个以数字资产为中心、具有真实 ZIP 导出、tag files、payload 组织和 SHA256 manifest 的 preservation-aware SIP-like 打包机制。

它已经足以支撑“系统具备保存移交意识”的研究表述，但当前仍应避免把它表述为完整 OAIS 信息包体系或所有导出场景的统一封装方案。
