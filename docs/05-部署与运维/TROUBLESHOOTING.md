# 常见问题与排障

- 最后核对日期：2026-04-06
- 核对范围：`docker-compose.yml`、`.env.example`、`frontend/nginx.conf`、`backend/app/config.py`

## 1. 建议排查顺序

遇到问题时，建议优先按这个顺序排查：

1. 阅读 `SETUP_AND_DEPLOYMENT.md`
2. 确认 `.env` 是否与当前机器环境一致
3. 执行 `docker compose ps`
4. 检查 `health` 与 `ready`
5. 再看具体模块日志

## 2. 启动类问题

### 2.1 前端打不开

优先检查：

- `frontend` 容器是否启动
- `FRONTEND_PORT` 是否被占用
- `docker compose ps`

可进一步查看：

```powershell
docker compose logs frontend
```

### 2.2 后端健康检查不通过

先访问：

- `http://localhost:8000/health`
- `http://localhost:8000/ready`

若失败，优先检查：

- `backend` 容器是否运行
- `DATABASE_URL`
- `REDIS_URL`

日志命令：

```powershell
docker compose logs backend
```

### 2.3 数据库连不上

优先检查：

- `db` 容器是否运行
- `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB`
- `DATABASE_URL` 中主机名是否仍为 `db`

日志命令：

```powershell
docker compose logs db
```

如果你当前跑的是本机独立测试库而不是主 compose 里的 `db` 服务，请改用：
```powershell
.\manage_local_postgres.ps1 status
.\manage_local_postgres.ps1 logs
```

### 2.4 Redis 或 worker 异常

优先检查：

- `redis` 是否启动
- `REDIS_URL`
- `celery_worker` 日志

日志命令：

```powershell
docker compose logs redis
docker compose logs celery_worker
```

## 3. 资源与挂载问题

### 3.1 上传后文件找不到

优先检查：

- `HOST_MUSEUM_PATH` 是否真实存在
- 宿主机目录是否正确映射到了 `/app/uploads`
- 上传目录是否可写

如果当前用的是相对目录 `./uploads`，确认它是否在仓库根目录下。

### 3.2 预览图不显示

优先检查：

- 资产是否已有预览图
- `backend/uploads/previews` 是否有生成结果
- 后端是否能读取原始文件

### 3.3 参考资源导入异常

优先检查：

- `reference/` 目录是否完整
- 相关脚本是否在 `backend/scripts/` 下执行
- 路径是否使用了当前环境可访问的文件系统位置

## 4. IIIF 与 Mirador 问题

### 4.1 Manifest 能打开，但 Mirador 图像加载失败

这通常优先指向 IIIF 服务地址或代理配置问题。

先检查：

- `CANTALOUPE_PUBLIC_URL`
- `frontend/nginx.conf` 中 `/iiif/2/` 代理
- `cantaloupe` 容器状态

建议本地保持：

```text
CANTALOUPE_PUBLIC_URL=http://localhost:3000/iiif/2
```

### 4.2 Mirador 完全打不开

优先检查：

- Manifest 地址是否正确
- 当前用户是否具备 `image.view`
- 资产是否对当前用户可见

### 4.3 `owner_only` 资源看不到

优先检查：

- 当前用户是否是 `system_admin`
- 当前用户 `collection_scope` 是否命中资源的 `collection_object_id`
- 资源本身 `visibility_scope` 是否是 `owner_only`

## 5. 登录与权限问题

### 5.1 登录失败

先检查：

- 当前用户名是否存在于 `/api/auth/users`
- 默认密码是否仍为 `mdams123`
- 浏览器中旧 token 是否已失效

可以尝试先退出并重新登录。

### 5.2 菜单和预期不一致

优先检查：

- 当前角色是否真的具备对应权限
- 前端是否拿到了最新 `/api/auth/context`
- 是否因为 token 过期回到了未登录状态

当前菜单显示并不是按角色名硬编码，而是按权限判定。

### 5.3 能看到菜单，但按钮不能用

这是正常的第一排查点之一。

原因通常是：

- 菜单只说明“页面可进入”
- 页面内部动作还会进一步检查权限
- 后端接口也会再次兜底

## 6. 图像记录工作流问题

### 6.1 图像记录工作台没有内容

优先检查当前登录角色：

- `image_metadata_entry`
- `image_photographer_upload`
- `system_admin`

并检查：

- 是否具备 `image.record.list`
- 或是否具备 `image.record.view_ready_for_upload`

### 6.2 摄影上传人员看不到待上传池

优先检查：

- 分配给该用户的图像记录是否存在
- 记录状态是否已进入待上传阶段
- 当前登录用户是否就是被分配的摄影上传用户

## 7. 三维问题

### 7.1 三维页面进不去

优先检查：

- 当前用户是否具备 `three_d.view`
- 菜单 `7` 是否按权限正常显示

### 7.2 三维资源上传后无法查看

优先检查：

- 上传是否完整
- 文件角色是否正确识别
- 三维详情接口是否能正常返回对象信息

## 8. 申请与导出问题

### 8.1 无法提交申请

优先检查：

- 当前用户是否具备 `application.create`
- 申请车中是否真的有条目

### 8.2 无法审批或导出

优先检查：

- 当前用户是否具备 `application.review` 或 `application.export`
- `application_reviewer` 或 `system_admin` 角色是否正确生效

## 9. 推荐继续查看的文档

- `SETUP_AND_DEPLOYMENT.md`
- `../01-总览/ACCEPTANCE_CHECKLIST.md`
- `../01-总览/PROJECT_STATUS.md`
- `../02-架构设计/AUTH_AND_IIIF_INTEGRATION_PLAN.md`
