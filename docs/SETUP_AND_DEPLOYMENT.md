# 部署与配置

这份文档是当前仓库的部署与环境配置入口。原则很简单：

- 只改 `.env`
- 尽量不改 `docker-compose.yml`
- 容器内路径保持稳定
- 只把宿主机路径和对外 URL 配出来

## 1. 需要修改哪些文件

- `.env.example`：默认示例
- `.env`：你真正使用的配置
- `docker-compose.yml`：一般不需要改，除非新增服务或调整端口

## 2. 核心配置项

| 变量 | 作用 | 建议 |
| :--- | :--- | :--- |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | PostgreSQL 初始化账号与数据库 | 与 `DATABASE_URL` 保持一致 |
| `DATABASE_URL` | 后端连接数据库 | 容器内主机名使用 `db` |
| `REDIS_URL` | Celery 与后端使用的 Redis 地址 | 默认 `redis://redis:6379/0` |
| `API_PUBLIC_URL` | 前端和后端生成公开 API 链接时使用 | 本地可用 `http://localhost:3000/api` |
| `CANTALOUPE_PUBLIC_URL` | IIIF / Mirador 使用的公开图像服务地址 | 本地可用 `http://localhost:3000/iiif/2` |
| `HOST_MUSEUM_PATH` | 宿主机上的资源目录 | 本地可用 `./uploads`，正式部署建议改成 NAS 或数据盘挂载路径 |
| `UPLOAD_DIR` | 容器内上传目录 | 保持 `/app/uploads` |
| `VIPS_DISC_THRESHOLD` | libvips 内存阈值 | 默认 `100m` |
| `VIPS_CONCURRENCY` | libvips 并发数 | 默认 `2` |
| `JAVA_OPTS` | Cantaloupe JVM 参数 | 默认已按低内存场景配置 |
| `FRONTEND_PORT` | 前端端口 | 默认 `3000` |
| `BACKEND_PORT` | 后端端口 | 默认 `8000` |
| `CANTALOUPE_PORT` | Cantaloupe 端口 | 默认 `8182` |

## 3. 本地启动

1. 复制示例文件：

```powershell
Copy-Item .env.example .env
```

2. 根据本机环境调整以下内容：

- `HOST_MUSEUM_PATH`
- `API_PUBLIC_URL`
- `CANTALOUPE_PUBLIC_URL`
- `DATABASE_URL`
- `REDIS_URL`

3. 启动服务：

```powershell
docker compose up -d --build
```

4. 检查常用地址：

- 前端：`http://localhost:3000`
- 后端接口文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`
- 就绪检查：`http://localhost:8000/ready`
- Cantaloupe：`http://localhost:8182`

## 4. 部署到服务器或 NAS

如果要部署到真实服务器，只需要优先确认这三项：

- `HOST_MUSEUM_PATH`：改成宿主机真实挂载目录
- `API_PUBLIC_URL`：改成浏览器可以访问的 API 地址
- `CANTALOUPE_PUBLIC_URL`：改成浏览器可以访问的 IIIF 地址

容器内部路径不要改：

- `/app/uploads`
- `/api`
- `/iiif/2`

## 5. 验收顺序

建议部署后按这个顺序验收：

1. `GET /health`
2. `GET /ready`
3. 前端首页是否可以打开
4. 登录是否正常
5. 资源列表是否正常
6. IIIF Manifest 是否可访问
7. Mirador 是否可加载图像
8. 申请车和申请管理是否可用
9. 三维管理页和 Web 查看器是否可用

## 6. 常见问题

- 前端拿不到 Manifest：先检查 `API_PUBLIC_URL`
- Mirador 里图像加载失败：先检查 `CANTALOUPE_PUBLIC_URL`
- 上传后文件找不到：先检查 `HOST_MUSEUM_PATH` 是否真的挂载到了宿主机目录
- 数据库连不上：先检查 `DATABASE_URL` 和 PostgreSQL 容器状态
- Cantaloupe 启动失败：先检查配置文件编码和图片目录路径

## 7. 不要随意改的内容

- 不要随意改 backend 里生成 Manifest 的路径结构
- 不要随意改 Cantaloupe 的 `/iiif/2` 前缀
- 不要把容器内路径改成宿主机路径
- 不要为了“统一”先改坏当前已经可用的 URL 约定