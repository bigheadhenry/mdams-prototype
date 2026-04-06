# 脚本与批处理说明

- 最后核对日期：2026-04-06
- 核对范围：`backend/scripts/`

## 1. 目标

本文件用于说明当前后端脚本的用途，帮助开发者理解哪些脚本用于导入、回填、校验与生成。

## 2. 当前脚本列表

| 脚本 | 主要用途 |
| :--- | :--- |
| `backfill_pyramidal_tiffs.py` | 回填大图访问副本或相关派生处理 |
| `backfill_reference_business_activity.py` | 回填参考资源的业务活动字段 |
| `generate_reference_manifests.py` | 为参考资源生成导入 manifest |
| `import_2d_images.py` | 导入二维图像 |
| `import_reference_manifests.py` | 将参考资源包导入当前二维入库链路 |
| `report_reference_completeness.py` | 输出参考资源完整性报告 |
| `validate_reference_imports.py` | 校验导入后的 Manifest、下载和 BagIt 能力 |

## 3. 当前主要用途分类

### 3.1 导入类

- `import_2d_images.py`
- `import_reference_manifests.py`

这类脚本用于把外部或参考数据导入当前系统。

### 3.2 生成类

- `generate_reference_manifests.py`

这类脚本用于在导入前准备结构化描述文件。

### 3.3 校验与报告类

- `report_reference_completeness.py`
- `validate_reference_imports.py`

这类脚本用于核对导入质量与可用性。

### 3.4 回填类

- `backfill_pyramidal_tiffs.py`
- `backfill_reference_business_activity.py`

这类脚本用于在已有数据基础上补充衍生信息或元数据。

## 4. `import_reference_manifests.py`

这是当前最值得重点理解的参考导入脚本之一。

它会：

- 读取参考资源根目录
- 准备导入文件名
- 调用当前二维 SIP 入库链路
- 将参考资源导入现有系统

常见参数包括：

- `--source-root`
- `--database-url`
- `--upload-dir`
- `--visibility-scope`
- `--limit`
- `--dry-run`

## 5. `validate_reference_imports.py`

这是当前导入后的验证脚本之一。

它会检查：

- Manifest 是否可返回
- 下载链接是否存在
- BagIt 链路是否可用
- 输出 JSON 和 Markdown 校验结果

## 6. 使用建议

- 先 dry-run，再正式导入
- 导入后立即跑校验脚本
- 对参考数据相关脚本，优先使用测试数据库或明确的数据副本

## 7. 当前边界

当前脚本文档主要覆盖“它们做什么”，还没有为每个脚本提供完整逐参数教程。后续如果导入与回填工作成为日常操作，可以继续把这份文档扩展成运行手册。

## 8. 关联文档

- `../06-参考资料/REFERENCE_DATASET_GUIDE.md`
- `SETUP_AND_DEPLOYMENT.md`
