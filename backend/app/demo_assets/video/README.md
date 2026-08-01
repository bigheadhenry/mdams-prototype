# NASA 视频测试数据

本目录包含 5 个来自 NASA Image and Video Library 的真实视频测试样例，供系统的视频管理、统一目录、元数据、检索、海报预览、在线播放和下载功能使用。

| 本地文件 | NASA 资源 | 类型 |
| --- | --- | --- |
| `nasa-gateway-lunar-station.mp4` | Gateway - Lunar Space Station Trailer | 航天任务纪实 |
| `nasa-how-big-is-space.mp4` | How Big is Space \| We Asked a NASA Expert | 科普教育 |
| `nasa-olympics-iss.mp4` | Olympics on the International Space Station | 载人航天 |
| `nasa-webb-journey-ep2.mp4` | Webb Journey to Space Ep2 | 航天任务纪实 |
| `nasa-space-dangers.mp4` | What Are the Dangers of Going to Space \| We Asked a NASA Expert | 科普教育 |

每个样例均包含：

- NASA 官方 `mobile MP4` 表示文件；
- JPEG 海报；
- `source_metadata/*-record.json` 原始检索响应；
- `source_metadata/*-assets.json` 完整资产清单；
- 启动入库时生成的 SHA-256、时长、分辨率、帧率、帧数、编码和完整分层元数据。

应用启动会幂等地复制资源至 `UPLOAD_DIR/videos/nasa-open-media/` 并创建或更新对应 `VideoAsset`，不会重复生成记录。

来源：[NASA Image and Video Library](https://images.nasa.gov/)。NASA 媒体通常不受美国版权保护，但 NASA 标识、商业背书、人物肖像及单项第三方署名仍可能受限制；使用时应遵循 [NASA Images and Media Usage Guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/)。
