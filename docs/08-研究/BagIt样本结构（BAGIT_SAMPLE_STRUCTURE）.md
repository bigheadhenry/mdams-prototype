# BagIt样本结构（BAGIT_SAMPLE_STRUCTURE）

## 目的

本文档提供一个基于当前 `backend/app/routers/downloads.py` 打包逻辑的代表性 BagIt 样本结构，并对目录、关键文件和当前边界进行注释。

它的用途是：
- 作为论文中的样本级证据；
- 作为演示时的结构说明；
- 与 [长期保存SIP打包说明（BAGIT_SIP_PROFILE）.md](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/docs/08-研究/长期保存SIP打包说明（BAGIT_SIP_PROFILE）.md) 配套。

## 样本来源

本样本根据以下实现锚点整理：
- [downloads.py](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/backend/app/routers/downloads.py)
- [AssetDetail.tsx](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/frontend/src/components/AssetDetail.tsx)
- [UnifiedResourceDetail.tsx](/Users/sunjing/Library/CloudStorage/OneDrive-Personal/AI/Codex/mdams-prototype/frontend/src/components/UnifiedResourceDetail.tsx)

## 代表性 Bag 目录样本

当前 `download-bag` 返回 ZIP。解压后目录结构可代表性理解为：

```text
bag_2001/
├─ bagit.txt
├─ bag-info.txt
├─ manifest-sha256.txt
└─ data/
   ├─ hidden.jpg
   └─ iiif-access.pyramidal.tiff
```

说明：
- `iiif-access.pyramidal.tiff` 仅在存在独立 IIIF access 文件时出现；
- 如果访问层直接回退原始文件，则 `data/` 下可能只有原件。

## 当前关键文件样本

### 1. `bagit.txt`

```text
BagIt-Version: 1.0
Tag-File-Character-Encoding: UTF-8
```

### 2. `bag-info.txt`

```text
Source-Organization: MEAM Prototype
Bagging-Date: 2026-04-08
Payload-Oxum: 128.1
Original-File: hidden.jpg
IIIF-Access-File: iiif-access.pyramidal.tiff
```

### 3. `manifest-sha256.txt`

```text
7f83b1657ff1fc53b92dc18148a1d65dfa135014...  data/hidden.jpg
0f7d0d088b6ea936fb25b477722d734706fe8b40...  data/iiif-access.pyramidal.tiff
```

## 目录与文件注释

| 路径 | 当前作用 | 当前实现来源 |
|---|---|---|
| `bagit.txt` | 标识 BagIt 版本与编码 | `downloads.py` 固定写入 |
| `bag-info.txt` | 提供基础打包说明 | `downloads.py` |
| `manifest-sha256.txt` | payload 文件的 SHA256 清单 | `downloads.py` |
| `data/<original>` | 原始文件对象 | `downloads.py` copy2 |
| `data/<iiif access>` | 独立访问副本对象 | `downloads.py` 条件加入 |

## 当前可以从样本直接看出的事实

- 当前导出并非普通 ZIP，而是至少具备 tag files、payload 目录和 SHA256 manifest
- 当前 bag 以单个二维 `Asset` 为中心组织
- 当前保存导向对象与访问对象可以共存于包内
- 当前 bag 仍是 SIP-like，而非完整 OAIS 信息包

## 当前边界

这是代表性目录样本，不是从实际运行时解压后复制出来的单次实例。

如需更强证据，后续仍建议补：
- 一份真实导出的 bag 目录截图或文本树
- 一份 payload 纳入规则表
- 一份 bag profile 级说明
