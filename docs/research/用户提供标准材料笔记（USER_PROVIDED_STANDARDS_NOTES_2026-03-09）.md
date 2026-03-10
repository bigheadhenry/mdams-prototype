# 用户提供标准材料整理笔记（2026-03-09）

## 来源压缩包

用户提供附件：
- `元数据标准规范文档.zip`

该压缩包已成功解压并检查。

## 已识别文档

1. `CS3DP/Community Standards for 3D Data Preservation.pdf`
2. `NISO/ANSI-NISO Z39.87-2006 (R2017), Data Dictionary - Technical Metadata for Digital Still Images.pdf`
3. `PREMIS/PREMIS 3 Ontology - LC Linked Data Services and Vocabularies.pdf`
4. `PREMIS/premis-3-0-final.pdf`
5. `PREMIS/understanding-premis.pdf`

---

## 1. PREMIS 3.0 数据字典

### 基本识别信息
- 标题：*PREMIS Data Dictionary for Preservation Metadata, version 3.0*
- 责任主体：PREMIS Editorial Committee
- 封面/前言可见时间：2015 年 6 月，后修订为 2015 年 11 月
- 文档内可见标准页面：http://www.loc.gov/standards/premis

### 当前已提取到的关键点
- 文档明确是一个较完整、可实施的保存元数据资源；
- 结构包括：
  - Introduction
  - Background
  - PREMIS Data Model
  - General Topics on Structure and Use
  - Implementation Considerations
  - The PREMIS Data Dictionary Version 3.0
  - Special Topics
  - Glossary
- 核心实体明确包括：
  - Objects
  - Events
  - Agents
  - Rights
- 专题中明确涉及：
  - format information
  - environment
  - object characteristics and composition level
  - fixity, integrity, authenticity
  - digital signatures
  - non-core metadata

### 对 MDAMS 的直接意义
- 非常适合用作保存元数据层的参考框架；
- 与当前原型中的 fixity、ingest、处理事件、衍生生成、导出等行为高度相关；
- 有助于把当前系统进一步解释为“具有保存意识的数字资产原型”。

### 当前工作判断
当前不应宣称 MDAMS 已完整实现 PREMIS，但可以认为：
- 当前系统已具备较明显的 proto-PREMIS 特征；
- 后续可通过事件模型与对象状态建模进一步 formalize。

---

## 2. NISO Z39.87 数字静态图像技术元数据标准

### 基本识别信息
- 标题：*ANSI/NISO Z39.87-2006 (R2017): Data Dictionary – Technical Metadata for Digital Still Images*
- 标准机构：NISO
- 文档可见信息：2006 年批准，2017 年 reaffirmed

### 当前已提取到的关键点
- 标准明确面向 raster digital images；
- 目标包括支持：
  - 开发数字图像文件；
  - 交换；
  - 解释；
  - 系统与服务之间的互操作；
  - 长期管理；
  - 持续访问。
- 前部目录/摘要可见内容包括：
  - digital object information
  - identifiers
  - file size
  - format designation
  - format registry information

### 对 MDAMS 的直接意义
- 对当前 still image 导向工作流极具价值；
- 尤其适合用于：
  - 图像技术元数据 profile；
  - ingest 阶段技术元数据采集；
  - 大图像与衍生图像的技术特征记录。

### 当前工作判断
NISO Z39.87 可作为 MDAMS 图像技术元数据 formalization 的优先标准参照。

---

## 3. CS3DP：3D 数据保存社区标准

### 基本识别信息
- 标题：*3D Data Creation to Curation: Community Standards for 3D Data Preservation*
- 编辑：Jennifer Moore, Adam Rountrey, Hannah Scates Kettler
- 出版信息：Association of College and Research Libraries / American Library Association
- 文档可见年份：2022

### 当前已提取到的关键点
- 内容覆盖：
  - best practices；
  - management and storage；
  - metadata requirements；
  - copyright and legal issues；
  - access。
- 目录显示其从 creation 到 curation 组织 3D 数据生命周期。

### 对 MDAMS 的直接意义
- 当前不是最核心的直接对齐标准；
- 但对未来扩展到复杂数字对象/3D 资产非常有启发；
- 也有助于说明 metadata、rights、preservation、access 本身应被视作一个连贯链条。

### 当前工作判断
CS3DP 当前更适合作为未来导向参考，而不是当前核心实现标准。

---

## 4. PREMIS Ontology PDF

### 当前状态
- 文件已识别：`PREMIS 3 Ontology - LC Linked Data Services and Vocabularies.pdf`
- 第一轮文本提取效果一般，尚未充分整理其内容。

### 初步判断
- 它更可能与 linked data / ontology 语境下的 PREMIS 表达相关；
- 若后续研究扩展到语义化建模，可再深入使用。

### 后续动作
- 需要二次提取或改从其他来源补充解释。

---

## 5. understanding-premis.pdf

### 当前状态
- 文件已确认存在；
- 本轮尚未深入阅读。

### 初步判断
- 适合作为 PREMIS 的解释性/导入性材料；
- 对把 PREMIS 转化为论文中的可读叙述可能很有帮助。

### 后续动作
- 后续可做单独提炼。

---

## 跨材料总体判断

这一包用户提供材料显著增强了 MDAMS 研究线在“元数据标准/保存标准”上的基础。

当前可以更清晰地把 MDAMS 的标准基础概括为：
- **IIIF**：访问/展示互操作；
- **BagIt**：保存导向打包/导出；
- **OAIS**：概念性保存框架；
- **PREMIS**：保存元数据框架；
- **NISO Z39.87**：数字静态图像技术元数据标准；
- **CS3DP**：面向复杂数字对象/3D 扩展的社区参考。

## 建议后续用途

1. 在 `标准映射（STANDARDS_MAPPING）.md` 中持续强化 PREMIS 与 NISO 的位置；
2. 新增 PREMIS 事件映射；
3. 新增图像技术元数据 crosswalk；
4. 将 `understanding-premis.pdf` 作为后续解释性材料继续整理。
