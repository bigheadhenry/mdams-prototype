# 部署与配置

- 最后核对日期：2026-04-06
- 核对范围：`.env.example`、`docker-compose.yml`、`frontend/nginx.conf`、`backend/app/config.py`

## 1. 目标

这份文档是当前仓库唯一推荐的部署与环境配置入口。

当前原则：

- 优先改 `.env`
- 尽量不改 `docker-compose.yml`
- 保持容器内路径稳定
- 让浏览器统一访问前端代理出来的 API 和 IIIF 地址

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

## 3. 当前访问路径

本地默认访问地址：

- 前端：`http://localhost:3000`
- 后端文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`
- 就绪检查：`http://localhost:8000/ready`
- Cantaloupe 直连调试：`http://localhost:8182`

但浏览器正常使用时，推荐统一走前端代理：

- API 基址：`http://localhost:3000/api`
- IIIF 基址：`http://localhost:3000/iiif/2`

这是因为前端 `nginx.conf` 已经代理了：

- `/api/` -> `backend:8000`
- `/iiif/2/` -> `meam-cantaloupe:8182/iiif/2/`

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
| `CANTALOUPE_PUBLIC_URL` | IIIF / Mirador 使用的图像服务地址 | `http://localhost:3000/iiif/2` |

注意：

- 这里的值应从浏览器视角出发，而不是容器内部视角
- 如果把 `CANTALOUPE_PUBLIC_URL` 写成 `http://localhost:8182/iiif/2`，浏览器直连调试可以工作，但在统一代理策略下不推荐

### 4.4 文件路径

| 变量 | 作用 | 默认示例 |
| :--- | :--- | :--- |
| `HOST_MUSEUM_PATH` | 宿主机实际目录 | `./uploads` |
| `UPLOAD_DIR` | 容器内上传目录 | `/app/uploads` |

当前挂载关系：

- 宿主机 `HOST_MUSEUM_PATH` -> 后端容器 `/app/uploads`
- 宿主机 `HOST_MUSEUM_PATH` -> Cantaloupe `/var/lib/cantaloupe/images`

### 4.5 图像处理

| 变量 | 作用 | 默认示例 |
| :--- | :--- | :--- |
| `VIPS_DISC_THRESHOLD` | libvips 磁盘阈值 | `100m` |
| `VIPS_CONCURRENCY` | libvips 并发数 | `2` |
| `JAVA_OPTS` | Cantaloupe JVM 参数 | `-Xmx4g -Djava.security.egd=file:/dev/./urandom` |

### 4.6 端口

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

推荐本地保持：

```text
API_PUBLIC_URL=http://localhost:3000/api
CANTALOUPE_PUBLIC_URL=http://localhost:3000/iiif/2
HOST_MUSEUM_PATH=./uploads
```

### 5.3 启动服务

```powershell
docker compose up -d --build
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
8. 验证 Mirador 预览

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
- `CANTALOUPE_PUBLIC_URL` 能从浏览器访问到

不要改这些容器内固定路径：

- `/app/uploads`
- `/api`
- `/iiif/2`

## 8. 常见问题

### 8.1 前端能打开，但预览失败

优先检查：

- `CANTALOUPE_PUBLIC_URL`
- `frontend/nginx.conf` 的 `/iiif/2/` 代理
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

## 9. 不建议随意修改的内容

当前不建议随意改动：

- `docker-compose.yml` 中的服务名
- `frontend/nginx.conf` 中的 `/api/` 与 `/iiif/2/` 代理前缀
- 后端对外生成链接时使用的 URL 约定
- 容器内上传路径 `/app/uploads`

## 10. 关联文档

- `TROUBLESHOOTING.md`
- `CANTALOUPE_DEPLOY_NOTES.md`
- `GIT_DEPLOY_GUIDE.md`
- `../01-总览/ACCEPTANCE_CHECKLIST.md`
