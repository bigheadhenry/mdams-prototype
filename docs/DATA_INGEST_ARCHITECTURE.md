# 数据传输与入库架构解析 (Data Ingest Architecture)

## 1. 核心策略：分离式 SIP (Unpackaged SIP)

在本项目中，从客户端（浏览器）向服务端传输数据的方式采用了 **“分离式 SIP”** 策略，而不是传统的打包好的 BagIt ZIP 包。

### 1.1 传输层结构
我们使用 `multipart/form-data` 格式进行 HTTP 传输，将 SIP (Submission Information Package) 的两个核心组成部分分开发送：

1.  **Part 1 (`file`)**: 原始的二进制数据流（Raw Data）。这是纯数据。
2.  **Part 2 (`manifest`)**: 一个 JSON 字符串，作为保存描述信息 (PDI)。

**前端实现 (`IngestDemo.tsx`)**:
```typescript
const formData = new FormData();
// 原始文件流，允许浏览器和服务器进行流式处理，避免内存溢出
formData.append('file', fileData); 
// 包含客户端计算的 SHA256 哈希和提取的元数据
formData.append('manifest', JSON.stringify(manifestData)); 
```

### 1.2 为什么不直接传输 BagIt ZIP 包？
这种设计是为了解决大文件（如 1GB+ 的 TIFF/RAW）在 Web 环境下的性能瓶颈：
*   **浏览器限制**: 在浏览器中将 1GB 的文件压缩成 ZIP 会消耗极大的 CPU 和内存，极易导致页面崩溃。
*   **传输效率**: 分离传输允许服务器一边接收文件流，一边实时计算哈希（Server-side Fixity），实现了流水线作业，比“先打包再上传再解包”快得多。

---

## 2. 逻辑 SIP 与 BagIt 的实现

虽然传输过程中没有 `.zip` 文件，但这仍然是一个完整的逻辑 SIP。BagIt 的规范和完整性要求是在 **服务端** 实现的。

### 2.1 入库阶段 (Ingest)
当数据到达服务端 (`ingest.py`) 时：
1.  **流式接收**: 服务器接收文件流。
2.  **双重校验**: 
    *   服务端计算接收到的流的哈希 (Server-side Hash)。
    *   与客户端 Manifest 中的哈希 (Client-side Hash) 进行比对。
3.  **逻辑归档**: 
    *   **物理文件**: 存入磁盘 (`uploads/` 或 NAS)。
    *   **元数据**: 存入数据库 (`metadata_info` 字段)。
    
    此时，**数据库记录 + 物理文件** 共同构成了一个“解包状态的 Bag”。这种状态对于 IIIF 图像服务（Cantaloupe）是最优的，因为它可以直接读取文件而无需解压。

### 2.2 导出阶段 (Export/Download)
当用户需要下载 BagIt 包时 (`main.py` -> `/download-bag`)，系统会 **实时动态生成** 标准包：

1.  创建一个临时目录。
2.  生成符合 BagIt 规范的结构：
    ```text
    bag_123/
    ├── bagit.txt             # BagIt 版本声明
    ├── bag-info.txt          # 打包时间、Payload-Oxum 等
    ├── manifest-sha256.txt   # 文件哈希清单
    └── data/                 # 数据载荷
        └── image.tif
    ```
3.  将物理文件复制入 `data/` 目录。
4.  将整个结构打包成 ZIP 并返回给用户。

---

## 3. 总结

*   **传输形态**: `Raw Data` + `JSON Manifest` (为了性能和稳定性)。
*   **逻辑形态**: 完整的 `SIP` (包含数据和校验信息)。
*   **存储形态**: 解包存储 (Unpacked)，数据库管理元数据。
*   **交换形态**: 标准 `BagIt ZIP` (按需动态生成)。

这种架构既保证了数据的完整性（端到端 Fixity 校验），又最大化了传输效率和在线预览（IIIF）的性能。
