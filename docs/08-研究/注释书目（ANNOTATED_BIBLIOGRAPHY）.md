# 注释书目（工作稿）

## 目的

本文档用于把外部资料池逐步转化为可直接支撑 MDAMS 研究写作的注释书目。

每条记录尽量包含：
- 资料识别信息；
- 获取/验证状态；
- 关键观察点；
- 与 MDAMS 的相关性；
- 可能对应的研究问题。

这是工作稿，不是最终格式化参考文献表。

---

## 1. IIIF Consortium. *Presentation API 3.0*
- URL: https://iiif.io/api/presentation/3.0/
- 类型：官方技术规范
- 获取状态：已直接抓取并确认

### 关键观察点
- 稳定版本显示为 3.0.0；
- 面向复合数字对象的在线展示环境；
- 明确不以 metadata harvesting/discovery 为主要目标；
- 核心结构包括 Collection、Manifest、Canvas、Range、AnnotationPage、Annotation。

### 与 MDAMS 的相关性
- 为当前原型的 manifest 生成与访问表示层提供直接基础；
- 有助于说明“资产管理”与“面向用户展示”的概念分离；
- 也有助于说明 IIIF 很重要，但它并不能替代完整元数据架构。

### 可能对应的研究问题
- RQ3：标准如何进入系统；
- RQ5：如何把互操作访问层纳入研究表达。

---

## 2. Kunze et al. *RFC 8493: The BagIt File Packaging Format (V1.0).* RFC Editor
- URL: https://www.rfc-editor.org/rfc/rfc8493
- 类型：官方技术标准 / RFC
- 获取状态：已直接抓取并确认

### 关键观察点
- BagIt 被定义为任意数字内容的层级文件打包约定；
- bag 同时包含 payload files 与 metadata tag files；
- 强调完整性保证与直接文件访问；
- 被保存导向机构广泛采用。

### 与 MDAMS 的相关性
- 为当前原型的 BagIt ZIP 导出提供标准基础；
- 支撑把“导出”解释为保存导向打包，而不是普通下载；
- 与 fixity 和 chain-of-custody 思路天然契合。

### 可能对应的研究问题
- RQ3：标准如何进入系统；
- RQ4：如何体现保存导向。

---

## 3. OAIS Reference Model / ISO 14721 相关入口
- URLs:
  - http://www.oais.info/
  - https://www.iso.org/standard/87471.html
  - https://ccsds.org/Pubs/650x0m3.pdf
- 类型：参考模型 / 标准体系入口
- 获取状态：入口已确认，仍需更深入二次阅读

### 关键观察点
- OAIS 明确是档案信息系统/数字保存的参考模型语境；
- 官方及标准相关入口可获得；
- 当前仍需后续提炼更细节内容再用于具体论证。

### 与 MDAMS 的相关性
- 有助于为 ingest、打包、生命周期与保存导向工作流提供概念框架；
- 有助于说明 MDAMS 受保存理念影响，但并不宣称完整 OAIS 实现。

### 可能对应的研究问题
- RQ3；
- RQ4；
- RQ5。

---

## 4. PREMIS Editorial Committee. *PREMIS Data Dictionary for Preservation Metadata, version 3.0*
- 来源：用户提供 PDF 材料
- 类型：保存元数据标准 / 数据字典
- 获取状态：已提取并完成第一轮阅读

### 关键观察点
- 版本 3.0，前言时间为 2015 年；
- 结构围绕 Objects、Events、Agents、Rights；
- 包含 implementation considerations；
- 专题涉及 format information、environment、fixity、integrity、authenticity、digital signatures 等。

### 与 MDAMS 的相关性
- 与当前 ingest、fixity、处理事件、衍生生成、导出等流程高度相关；
- 非常适合用于解释系统如何逐步形成保存元数据意识；
- 即使尚未正式实现 PREMIS，也可用于说明当前 proto-PREMIS 特征。

### 可能对应的研究问题
- RQ3；
- RQ4；
- RQ5。

---

## 5. NISO. *ANSI/NISO Z39.87-2006 (R2017): Data Dictionary – Technical Metadata for Digital Still Images*
- 来源：用户提供 PDF 材料
- 类型：技术元数据标准
- 获取状态：已提取并完成第一轮阅读

### 关键观察点
- 面向 raster digital images 的技术元数据；
- 强调开发、交换、解释、互操作、长期管理与持续访问；
- 前部内容涉及 digital object information、identifiers、file size、format designation 等。

### 与 MDAMS 的相关性
- 为 still image 资产的技术元数据设计提供了强标准基础；
- 特别适合支撑大图像与图像导向资产处理场景；
- 有助于把当前“图像元数据提取”提升为“标准映射可能性”。

### 可能对应的研究问题
- RQ3；
- RQ5；
- RQ6。

---

## 6. Moore, Rountrey, and Scates Kettler (eds.). *3D Data Creation to Curation: Community Standards for 3D Data Preservation*
- 来源：用户提供 PDF 材料
- 类型：社区标准 / 编辑文集
- 获取状态：已提取并完成第一轮阅读

### 关键观察点
- 覆盖 best practices、storage、metadata、legal issues、access；
- 以从 creation 到 curation 的全生命周期视角组织；
- 对复杂数字对象的保存与访问具有方法论启发。

### 与 MDAMS 的相关性
- 当前不是最核心标准，但对未来扩展到复杂数字对象或 3D 资产很有启发；
- 也有助于说明保存、元数据、权利、访问本身就是连在一起的工作流。

### 可能对应的研究问题
- RQ3；
- RQ6。

---

## 当前综合观察

当前注释书目已经能支撑一个更稳的研究表达：
- **IIIF** 负责访问表示与互操作；
- **BagIt** 负责导出打包；
- **OAIS** 提供概念性保存框架；
- **PREMIS** 提供保存元数据框架；
- **NISO Z39.87** 提供图像技术元数据基础；
- **CS3DP** 提供未来复杂对象扩展视角。

这说明 MDAMS 的研究表达可以不再停留于“系统做了哪些功能”，而能进一步讨论：
- 为什么这些标准以不同层级进入系统；
- 为什么当前原型应采用选择性对齐而不是全面合规；
- 为什么这条路径对研究型原型是合理的。
