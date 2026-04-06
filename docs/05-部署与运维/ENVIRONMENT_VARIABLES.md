# 环境变量说明

- 最后核对日期：2026-04-06
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
| `CANTALOUPE_PUBLIC_URL` | IIIF 服务地址 | `http://localhost:3000/iiif/2` |

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

## 6. 文件路径

| 变量 | 说明 | 默认示例 |
| :--- | :--- | :--- |
| `HOST_MUSEUM_PATH` | 宿主机目录 | `./uploads` |
| `UPLOAD_DIR` | 容器内上传目录 | `/app/uploads` |

## 7. 图像处理

| 变量 | 说明 | 默认示例 |
| :--- | :--- | :--- |
| `VIPS_DISC_THRESHOLD` | libvips 磁盘阈值 | `100m` |
| `VIPS_CONCURRENCY` | libvips 并发数 | `2` |
| `JAVA_OPTS` | JVM 参数 | `-Xmx4g -Djava.security.egd=file:/dev/./urandom` |

## 8. 端口

| 变量 | 默认值 |
| :--- | :--- |
| `FRONTEND_PORT` | `3000` |
| `BACKEND_PORT` | `8000` |
| `DB_PORT` | `5432` |
| `REDIS_PORT` | `6379` |
| `CANTALOUPE_PORT` | `8182` |

## 9. 使用建议

- 本地开发优先只改 `.env`
- 浏览器访问地址优先以 `3000` 代理口径为准
- 不要把容器内路径改成宿主机绝对路径
- 容器内服务继续使用 `DATABASE_URL`，主机侧 `pytest` 建议单独设置 `TEST_DATABASE_URL`

## 10. 关联文档

- `SETUP_AND_DEPLOYMENT.md`
- `TROUBLESHOOTING.md`
