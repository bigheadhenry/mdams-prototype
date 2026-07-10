# 部署与配置

- 最后核对日期：2026-05-17
- 核对口径：仅以已提交代码中的稳定实现为准，不纳入当前工作区未提交改动
- 核对范围：`.env.example`、`docker-compose.yml`、`frontend/nginx.conf`、`backend/app/config.py`

## 1. 目标

这份文档是当前仓库唯一推荐的部署与环境配置入口。

当前原则：

- 优先改 `.env`
- 尽量不改 `docker-compose.yml`
- 保持容器内路径稳定
- 区分浏览器可访问地址和容器内部服务地址

## 2. 当前容器组成

当前 `docker-compose.yml` 包含以下服务：

| 服务 | 作用 |
| :--- | :--- |
| `backend` | FastAPI API 服务 |
| `celery_worker` | 异步任务 worker |
| `redis` | Celery 和应用缓存依赖 |
| `frontend` | Nginx + 前端静态资源 |
| `db` | PostgreSQL |
| `cantaloupe` | IIIF 图像服务 |

当前 compose 中没有 `FileBrowser`，如果你在历史文档中看到它，应视为旧资料。

视频资源（`video` 路由）复用 Backend 容器的文件存储和 API 服务，无需额外的独立容器。视频文件的存储位置与二维资产共用 `HOST_MUSEUM_PATH` 挂载目录。

## 3. 当前访问路径

本地默认访问地址：

- 前端：`http://localhost:3000`
- 后端文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`
- 就绪检查：`http://localhost:8000/ready`
- Cantaloupe 直连调试：`http://localhost:8182`

浏览器正常使用时，推荐统一进入 API：

- API 基址：`http://localhost:3000/api`
- Manifest：`http://localhost:3000/api/iiif/{asset_id}/manifest`
- 图像服务代理：`http://localhost:3000/api/iiif/{asset_id}/service/...`

这是因为当前前端 `nginx.conf` 代理的是：

- `/api/` -> `backend:8000`

当前稳定代码会把 Manifest 图像服务入口写成后端 `/api/iiif/{asset_id}/service/...` 代理路径。`CANTALOUPE_INTERNAL_URL` 用于后端访问 Cantaloupe 上游；`CANTALOUPE_PUBLIC_URL` 主要作为兼容默认值和本地调试地址。

部署到服务器时，应根据运行方式调整：

- 宿主机直跑后端或调试 Cantaloupe：可使用 `http://localhost:8182/iiif/2`
- 后端在 compose 容器内访问 Cantaloupe：优先使用 `http://cantaloupe:8182/iiif/2`
- 生产网络：避免把 Cantaloupe 作为公共入口暴露给浏览器

## 4. 环境变量

### 4.1 基础数据库

| 变量 | 作用 | 默认示例 |
| :--- | :--- | :--- |
| `POSTGRES_USER` | PostgreSQL 用户 | `meam` |
| `POSTGRES_PASSWORD` | PostgreSQL 密码 | `meam_secret` |
| `POSTGRES_DB` | 数据库名 | `meam_db` |
| `DATABASE_URL` | 后端数据库连接串 | `postgresql://meam:meam_secret@db:5432/meam_db` |

### 4.2 Redis 与任务

| 变量 | 作用 | 默认示例 |
| :--- | :--- | :--- |
| `REDIS_URL` | 后端和 worker 使用的 Redis | `redis://redis:6379/0` |

### 4.3 浏览器可访问地址

| 变量 | 作用 | 本地建议值 |
| :--- | :--- | :--- |
| `API_PUBLIC_URL` | 后端生成公开 API 链接时使用 | `http://localhost:3000/api` |
| `CANTALOUPE_PUBLIC_URL` | 兼容默认值 / 本地调试用 IIIF 上游地址 | `http://localhost:8182/iiif/2` |
| `CANTALOUPE_INTERNAL_URL` | 后端访问 Cantaloupe 的内部地址 | 宿主机调试 `http://localhost:8182/iiif/2`；compose 内部建议 `http://cantaloupe:8182/iiif/2` |
| `CORS_ALLOWED_ORIGINS` | 允许访问后端的前端来源 | `http://localhost:3000,http://127.0.0.1:3000` |
| `AUTH_DEFAULT_PASSWORD` | 自动播种测试用户的默认密码 | `mdams123` |

注意：

- `API_PUBLIC_URL` 应从浏览器视角出发
- `CANTALOUPE_PUBLIC_URL` 当前主要作为兼容默认值和本地调试地址
- `CANTALOUPE_INTERNAL_URL` 影响后端到 Cantaloupe 的服务端访问

### 4.4 AI 与人脸识别

当前后端 AI 配置以 Moonshot / Kimi 为默认 OpenAI 兼容提供方：

| 变量 | 作用 | 默认示例 |
| :--- | :--- | :--- |
| `MOONSHOT_API_KEY` | Moonshot API Key | 空 |
| `MOONSHOT_BASE_URL` | Moonshot OpenAI 兼容地址 | `https://api.moonshot.cn/v1` |
| `MOONSHOT_MODEL` | 默认模型 | `kimi-k2.5` |
| `OPENAI_API_KEY` | OpenAI 兼容覆盖变量 | 空 |
| `OPENAI_BASE_URL` | OpenAI 兼容覆盖变量 | 空 |
| `OPENAI_MODEL` | OpenAI 兼容覆盖变量 | 空 |
| `OPENAI_TIMEOUT_SECONDS` | AI 请求超时秒数 | `30` |

当前人脸识别链路是可开关能力：

| 变量 | 作用 | 默认示例 |
| :--- | :--- | :--- |
| `FACE_RECOGNITION_ENABLED` | 是否启用人脸识别 | `0` |
| `FACE_RECOGNITION_PROVIDER` | provider：`local`、`remote` 或 `auto` | `local` |
| `FACE_RECOGNITION_BASE_URL` | 远程识别服务地址 | `http://host.docker.internal:8010` |
| `FACE_RECOGNITION_TIMEOUT_SECONDS` | 识别请求超时秒数 | `30` |
| `FACE_RECOGNITION_THRESHOLD` | 识别阈值 | `0.5` |
| `FACE_RECOGNITION_MODEL_ROOT` | 本地模型运行时目录 | `/app/runtime/face_recognition` |
| `FACE_RECOGNITION_MODEL_NAME` | 本地模型名 | `buffalo_l` |
| `FACE_RECOGNITION_INDEX_DIR` | 本地索引目录 | `/app/runtime/face_recognition/index` |
| `FACE_RECOGNITION_STRICT_LOCAL_MODELS` | 本地模型缺失时是否严格失败 | `1` |

### 4.5 文件路径

| 变量 | 作用 | 默认示例 |
| :--- | :--- | :--- |
| `HOST_MUSEUM_PATH` | 宿主机实际目录 | `./uploads` |
| `UPLOAD_DIR` | 容器内上传目录 | `/app/uploads` |

当前挂载关系：

- 宿主机 `HOST_MUSEUM_PATH` -> 后端容器 `/app/uploads`
- 宿主机 `HOST_MUSEUM_PATH` -> Cantaloupe `/var/lib/cantaloupe/images`

### 4.6 图像处理

| 变量 | 作用 | 默认示例 |
| :--- | :--- | :--- |
| `VIPS_DISC_THRESHOLD` | libvips 磁盘阈值 | `100m` |
| `VIPS_CONCURRENCY` | libvips 并发数 | `2` |
| `JAVA_OPTS` | Cantaloupe JVM 参数 | `-Xmx4g -Djava.security.egd=file:/dev/./urandom` |

### 4.7 端口

| 变量 | 默认值 |
| :--- | :--- |
| `FRONTEND_PORT` | `3000` |
| `BACKEND_PORT` | `8000` |
| `DB_PORT` | `5432` |
| `REDIS_PORT` | `6379` |
| `CANTALOUPE_PORT` | `8182` |

## 5. 本地启动步骤

### 5.1 复制配置

```powershell
Copy-Item .env.example .env
```

### 5.2 检查重点变量

至少检查：

- `HOST_MUSEUM_PATH`
- `DATABASE_URL`
- `REDIS_URL`
- `API_PUBLIC_URL`
- `CANTALOUPE_PUBLIC_URL`
- `CANTALOUPE_INTERNAL_URL`
- `CORS_ALLOWED_ORIGINS`

推荐本地保持：

```text
API_PUBLIC_URL=http://localhost:3000/api
CANTALOUPE_PUBLIC_URL=http://localhost:8182/iiif/2
CANTALOUPE_INTERNAL_URL=http://cantaloupe:8182/iiif/2
HOST_MUSEUM_PATH=./uploads
```

### 5.3 启动服务

```powershell
docker compose up -d --build
```

如需仅在本机启动 PostgreSQL 测试环境，可使用仓库根目录脚本：
```powershell
.\manage_local_postgres.ps1 up
```

配套测试连接串建议为：
```text
TEST_DATABASE_URL=postgresql://meam:meam_secret@localhost:5432/meam_db_test
```

### 5.4 启动后验证

建议按以下顺序检查：

1. `docker compose ps`
2. `http://localhost:8000/health`
3. `http://localhost:8000/ready`
4. 打开前端首页
5. 登录测试账号
6. 打开二维列表
7. 打开统一平台目录
8. 检查 `/api/platform/sources` 是否返回二维、三维、视频三个来源
9. 验证 Mirador 预览
10. 打开三维或视频资源的统一详情，确认多模态来源可进入详情页

## 6. 默认测试账号

当前后端会自动播种测试用户，默认密码：

```text
mdams123
```

常用账号包括：

- `system_admin`
- `resource_user`
- `collection_owner`
- `image_metadata_entry`
- `image_photographer`
- `three_d_operator`

## 7. 服务器部署注意事项

如果部署到服务器或 NAS 环境，优先确认以下三项：

- `HOST_MUSEUM_PATH` 指向宿主机真实挂载目录
- `API_PUBLIC_URL` 能从浏览器访问到
- Manifest 中的图像服务入口是 `/api/iiif/{asset_id}/service/...`
- `CANTALOUPE_INTERNAL_URL` 能从后端运行环境访问到
- `FACE_RECOGNITION_*` 仅在确实需要识别能力时启用和配置

不要改这些容器内固定路径：

- `/app/uploads`
- `/app/runtime/face_recognition`
- `/api`
- `/iiif/2`

## 8. 常见问题

### 8.1 前端能打开，但预览失败

优先检查：

- `CANTALOUPE_PUBLIC_URL`
- `CANTALOUPE_INTERNAL_URL`
- Manifest 中的 `/api/iiif/{asset_id}/service/...` 代理入口
- Cantaloupe 是否已正常启动

### 8.2 Manifest 地址不对

优先检查：

- `API_PUBLIC_URL`
- 后端配置是否重新加载

### 8.3 上传后文件找不到

优先检查：

- `HOST_MUSEUM_PATH` 是否真实存在
- 挂载目录是否被正确映射到 `/app/uploads`

### 8.4 数据库连不上

优先检查：

- `DATABASE_URL`
- `db` 容器状态
- 端口占用

### 8.5 Cantaloupe 启动慢或异常

优先检查：

- `JAVA_OPTS`
- `cantaloupe.properties`
- 图像目录是否可读
- 熵源映射 `/dev/urandom:/dev/random:ro`

### 8.6 AI / Mirador 没有调用外部模型

优先检查：

- `MOONSHOT_API_KEY` 或 `OPENAI_API_KEY`
- `MOONSHOT_BASE_URL` / `OPENAI_BASE_URL`
- `MOONSHOT_MODEL` / `OPENAI_MODEL`
- 后端日志中的超时或鉴权错误

如果没有配置 API Key，后端仍可走启发式计划逻辑，但不会调用外部模型。

### 8.7 人脸识别没有结果

优先检查：

- `FACE_RECOGNITION_ENABLED` 是否为 `1`
- `FACE_RECOGNITION_PROVIDER` 是否符合预期
- 本地模型和索引目录是否存在
- 远程识别服务是否可从容器访问

## 9. 不建议随意修改的内容

当前不建议随意改动：

- `docker-compose.yml` 中的服务名
- `frontend/nginx.conf` 中的 `/api/` 代理前缀
- 后端 `/api/iiif/{asset_id}/service/...` 图像服务代理约定
- 后端对外生成链接时使用的 URL 约定
- 容器内上传路径 `/app/uploads`
- 人脸识别运行时目录中的模型与索引文件结构

## 10. 关联文档

- `TROUBLESHOOTING.md`
- `CANTALOUPE_DEPLOY_NOTES.md`
- `GIT_DEPLOY_GUIDE.md`
- `../01-总览/ACCEPTANCE_CHECKLIST.md`
