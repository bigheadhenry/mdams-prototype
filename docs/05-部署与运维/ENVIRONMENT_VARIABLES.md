# 环境变量说明

- 最后核对日期：2026-05-17
- 核对口径：仅以已提交代码中的稳定实现为准，不纳入当前工作区未提交改动
- 核对范围：`.env.example`、`backend/app/config.py`、`docker-compose.yml`

## 1. 目标

本文件用于解释当前项目实际使用的环境变量、默认值和推荐配置方式。

## 2. 数据库

| 变量 | 说明 | 默认示例 |
| :--- | :--- | :--- |
| `POSTGRES_USER` | PostgreSQL 用户名 | `meam` |
| `POSTGRES_PASSWORD` | PostgreSQL 密码 | `meam_secret` |
| `POSTGRES_DB` | PostgreSQL 数据库名 | `meam_db` |
| `DATABASE_URL` | 后端连接串 | `postgresql://meam:meam_secret@db:5432/meam_db` |
| `TEST_DATABASE_URL` | 主机侧测试库连接串 | `postgresql://meam:meam_secret@localhost:5432/meam_db_test` |

## 3. Redis 与任务

| 变量 | 说明 | 默认示例 |
| :--- | :--- | :--- |
| `REDIS_URL` | Redis 连接串 | `redis://redis:6379/0` |

## 4. 浏览器可访问地址

| 变量 | 说明 | 本地建议值 |
| :--- | :--- | :--- |
| `API_PUBLIC_URL` | 后端生成公开 API 链接时使用 | `http://localhost:3000/api` |
| `CANTALOUPE_PUBLIC_URL` | 兼容默认值 / 本地调试用 IIIF 上游地址 | `http://localhost:8182/iiif/2` |
| `CANTALOUPE_INTERNAL_URL` | 后端访问 Cantaloupe 的内部地址；未设置时回退到 `CANTALOUPE_PUBLIC_URL` | 宿主机调试 `http://localhost:8182/iiif/2`；compose 内部建议 `http://cantaloupe:8182/iiif/2` |
| `CORS_ALLOWED_ORIGINS` | CORS 允许来源，逗号分隔 | `http://localhost:3000,http://127.0.0.1:3000` |
| `AUTH_DEFAULT_PASSWORD` | 自动播种测试用户的默认密码 | `mdams123` |

## 5. AI 相关

| 变量 | 说明 | 默认示例 |
| :--- | :--- | :--- |
| `MOONSHOT_API_KEY` | Moonshot API key | 空 |
| `MOONSHOT_BASE_URL` | Moonshot 基础地址 | `https://api.moonshot.cn/v1` |
| `MOONSHOT_MODEL` | Moonshot 模型名 | `kimi-k2.5` |
| `OPENAI_API_KEY` | OpenAI 兼容变量 | 空 |
| `OPENAI_BASE_URL` | OpenAI 兼容变量 | 空 |
| `OPENAI_MODEL` | OpenAI 兼容变量 | 空 |
| `OPENAI_TIMEOUT_SECONDS` | 超时秒数 | `30` |

说明：

- 当前后端把 Moonshot 视为 OpenAI 兼容提供方
- 如果没有显式设置 `OPENAI_*`，会优先回退到 `MOONSHOT_*`

## 6. 人脸识别

| 变量 | 说明 | 默认示例 |
| :--- | :--- | :--- |
| `FACE_RECOGNITION_ENABLED` | 是否启用人脸识别链路，`1` 为启用 | `0` |
| `FACE_RECOGNITION_PROVIDER` | provider，可取 `local`、`remote`、`auto` | `local` |
| `FACE_RECOGNITION_BASE_URL` | 远程识别服务地址 | `http://host.docker.internal:8010` |
| `FACE_RECOGNITION_TIMEOUT_SECONDS` | 识别请求超时秒数 | `30` |
| `FACE_RECOGNITION_THRESHOLD` | 人脸识别阈值 | `0.5` |
| `FACE_RECOGNITION_MODEL_ROOT` | 本地识别模型根目录 | `/app/runtime/face_recognition` |
| `FACE_RECOGNITION_MODEL_NAME` | 本地识别模型名 | `buffalo_l` |
| `FACE_RECOGNITION_INDEX_DIR` | 本地识别索引目录 | `/app/runtime/face_recognition/index` |
| `FACE_RECOGNITION_STRICT_LOCAL_MODELS` | 本地模型缺失时是否严格失败 | `1` |

说明：

- 默认关闭人脸识别，避免部署环境缺少模型或索引时影响主链路
- `local` 模式依赖容器内运行时目录和模型文件
- `remote` 模式依赖外部识别服务
- `auto` 模式可先尝试本地能力，再按实现逻辑回退

## 7. 文件路径

| 变量 | 说明 | 默认示例 |
| :--- | :--- | :--- |
| `HOST_MUSEUM_PATH` | 宿主机目录 | `./uploads` |
| `UPLOAD_DIR` | 容器内上传目录 | `/app/uploads` |

## 8. 图像处理

| 变量 | 说明 | 默认示例 |
| :--- | :--- | :--- |
| `VIPS_DISC_THRESHOLD` | libvips 磁盘阈值 | `100m` |
| `VIPS_CONCURRENCY` | libvips 并发数 | `2` |
| `JAVA_OPTS` | JVM 参数 | `-Xmx4g -Djava.security.egd=file:/dev/./urandom` |

## 9. 安全/演示模式

| 变量 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `MDAMS_DEMO_MODE` | 设为 `1` 时允许 X-MDAMS-User Header 绕过真实认证（仅开发/演示用）；生产环境必须设为 `0` | `0` |

说明：

- 生产部署必须设置 `MDAMS_DEMO_MODE=0`，此时仅接受 Authorization（Bearer Token）和 mdams.session Cookie 两种认证方式
- 设为 `1` 时，任意客户端可通过设置 `X-MDAMS-User: system-admin` 等 Header 模拟任意用户，存在安全风险
- 默认 `0`（安全默认值），确保新部署默认不暴露此后门

## 10. 端口

| 变量 | 默认值 |
| :--- | :--- |
| `FRONTEND_PORT` | `3000` |
| `BACKEND_PORT` | `8000` |
| `DB_PORT` | `5432` |
| `REDIS_PORT` | `6379` |
| `CANTALOUPE_PORT` | `8182` |

## 11. 使用建议

- 本地开发优先只改 `.env`
- 浏览器侧应通过 Manifest 中的 `/api/iiif/{asset_id}/service/...` 访问图像服务代理
- 后端访问 Cantaloupe 时优先使用 `CANTALOUPE_INTERNAL_URL`
- 生产环境避免把 Cantaloupe 作为公共入口暴露给浏览器
- 不要把容器内路径改成宿主机绝对路径
- 容器内服务继续使用 `DATABASE_URL`，主机侧 `pytest` 建议单独设置 `TEST_DATABASE_URL`
- 人脸识别默认关闭，需要模型、索引或远程服务准备好后再启用

## 12. 关联文档

- `SETUP_AND_DEPLOYMENT.md`
- `TROUBLESHOOTING.md`
