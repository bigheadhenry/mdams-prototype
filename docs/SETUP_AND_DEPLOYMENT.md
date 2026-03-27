# 部署与配置

这份文档是当前仓库的部署和配置唯一入口。原则很简单：

- 只改 `.env`
- 尽量不改 `docker-compose.yml`
- 容器内路径保持不变
- 只把宿主机路径和对外 URL 外提出来

## 1. 你需要改哪些文件

- `.env.example`：默认示例
- `.env`：你真正使用的配置
- `docker-compose.yml`：一般不动，除非新增服务或改端口

## 2. 核心配置项

| 变量 | 作用 | 建议 |
| :--- | :--- | :--- |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | PostgreSQL 初始化账号和数据库 | 保持和 `DATABASE_URL` 一致 |
| `DATABASE_URL` | 后端连接数据库 | 容器内主机名用 `db` |
| `REDIS_URL` | Celery 和后端使用的 Redis 地址 | 默认 `redis://redis:6379/0` |
| `API_PUBLIC_URL` | 前端和后端生成公开 API 链接时使用 | 本地默认 `http://localhost:3000/api` |
| `CANTALOUPE_PUBLIC_URL` | IIIF / Manifest 中使用的公开图像服务地址 | 本地默认 `http://localhost:3000/iiif/2` |
| `HOST_MUSEUM_PATH` | 宿主机数据目录 | 本地可用 `./uploads`，正式部署改成 NAS 或数据盘挂载路径 |
| `UPLOAD_DIR` | 容器内上传目录 | 保持 `/app/uploads` |
| `VIPS_DISC_THRESHOLD` | libvips 内存阈值 | 默认 `100m` |
| `VIPS_CONCURRENCY` | libvips 并发 | 默认 `2` |
| `JAVA_OPTS` | Cantaloupe JVM 参数 | 默认 `-Xmx4g ...` |

## 3. 本地启动

1. 复制示例文件。

```powershell
Copy-Item .env.example .env
```

2. 确认 `./uploads` 目录存在，或者把 `HOST_MUSEUM_PATH` 改成你的真实数据目录。

3. 启动服务。

```powershell
docker compose up -d --build
```

4. 验证基础访问。

- 前端：`http://localhost:3000`
- 后端文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:3000/api/health`
- 就绪检查：`http://localhost:3000/api/ready`

## 4. 部署到服务器

如果你是在实验室服务器或 NAS 环境部署，只需要改三类值：

- `HOST_MUSEUM_PATH`：改成宿主机上的真实挂载目录
- `API_PUBLIC_URL`：改成浏览器可访问的前端 API 地址
- `CANTALOUPE_PUBLIC_URL`：改成浏览器可访问的 IIIF 地址

容器内部这些路径不要改：

- `/app/uploads`
- `/api`
- `/iiif/2`

## 5. 验收顺序

部署后按这个顺序验收：

1. `GET /api/health`
2. `GET /api/ready`
3. `GET /api/assets`
4. `GET /api/iiif/{id}/manifest`
5. 前端首页和资产详情页
6. Mirador 预览

## 6. 这轮不要改的东西

- 不要改 backend 里生成 Manifest 的路径结构
- 不要改 Cantaloupe 的 `/iiif/2` 前缀
- 不要把容器内部路径改成宿主机路径
- 不要为了“更统一”而先改 API URL 结构

## 7. 常见问题

- 如果前端拿不到 Manifest，先检查 `API_PUBLIC_URL`
- 如果 Mirador 里图片加载失败，先检查 `CANTALOUPE_PUBLIC_URL`
- 如果上传后文件找不到，先检查 `HOST_MUSEUM_PATH` 是否挂载正确
- 如果数据库连不上，先检查 `DATABASE_URL` 和 PostgreSQL 容器状态
