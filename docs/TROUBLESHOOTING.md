# MDAMS Prototype 故障排查指南

## 1. 文档目标

本文档用于为 **MDAMS Prototype** 提供一份偏实战的故障排查入口，重点解决以下问题：

- 系统启动后为什么访问不了
- 上传成功后为什么资产没有出现
- 为什么转换任务没有执行
- 为什么 manifest 打不开
- 为什么 Mirador 预览失败
- 出问题后应该先查哪里

本文档优先服务于当前主链路：

> **上传 → 入库 → 转换 → Manifest → IIIF → Mirador 预览**

---

## 2. 排查总原则

出现问题时，建议不要同时改很多地方，而是按链路顺序逐层检查：

1. **环境是否起来了**
2. **入口是否通了**
3. **后端是否工作**
4. **异步任务是否执行**
5. **IIIF 资源是否可访问**
6. **Manifest 引用是否正确**
7. **前端预览是否正确加载**

建议优先使用以下基础命令：

```bash
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 worker
docker compose logs --tail=100 cantaloupe
```

---

## 3. 启动后页面打不开

## 症状

- 浏览器无法打开前端页面
- 页面报 502 / 504
- 页面空白或请求失败

## 优先检查

### 3.1 容器是否正常运行

```bash
docker compose ps
```

检查：

- frontend 是否在运行
- backend 是否在运行
- nginx 是否在运行（如当前链路依赖）

### 3.2 前端日志

```bash
docker compose logs --tail=100 frontend
```

### 3.3 反向代理日志或配置

如果前端入口通过 nginx 暴露，应检查：

- nginx 是否正常启动
- 代理目标端口是否正确
- `/api` 和 `/iiif/2` 路由是否仍与当前系统约定一致

### 3.4 端口占用或映射问题

检查当前实际暴露端口是否和文档一致。

---

## 4. 前端打开了，但接口报错

## 症状

- 页面可打开，但资产列表加载失败
- 浏览器开发者工具中看到 `/api/...` 请求报错
- 出现 404 / 500 / 502

## 优先检查

### 4.1 backend 是否正常运行

```bash
docker compose logs --tail=100 backend
```

### 4.2 `/api` 代理路径是否正确

重点确认：

- 前端调用路径是否仍为相对路径 `/api`
- nginx 是否将 `/api` 正确转发到 backend
- backend 路由前缀是否与当前代理配置一致

### 4.3 数据库连接是否正常

backend 若启动时报数据库连接错误，接口通常会直接失败。

可从 backend 日志中查找：

- connection refused
- authentication failed
- database does not exist

### 4.4 环境变量是否正确

尤其关注：

- 数据库 URL
- Redis URL
- API public URL
- 其他 backend 依赖配置

---

## 5. 上传成功了，但资产列表里没有

## 症状

- 前端提示上传成功
- 但资产列表中看不到记录
- 或后端没有对应资产信息

## 优先检查

### 5.1 上传成功到底代表什么

先确认当前“上传成功”是：

- 文件已写入磁盘
- 还是资产已完成数据库入库
- 还是仅接口返回成功

### 5.2 backend 日志

```bash
docker compose logs --tail=100 backend
```

重点看：

- 上传后是否有创建资产记录
- 是否有数据库写入错误
- 是否有路径/权限错误

### 5.3 数据目录挂载是否正确

检查：

- host path 是否真实存在
- 容器内挂载点是否正确
- backend / worker / cantaloupe 是否访问同一批数据

### 5.4 列表查询逻辑

如果数据库中已有记录但页面不显示，问题可能在：

- 列表接口返回字段
- 前端展示逻辑
- 状态筛选条件

---

## 6. 上传后没有触发转换任务

## 症状

- 资产已出现
- 但衍生文件未生成
- 预期的异步任务没有执行

## 优先检查

### 6.1 worker 是否在运行

```bash
docker compose ps
```

确认：

- worker 容器是否运行
- 无持续重启

### 6.2 worker 日志

```bash
docker compose logs --tail=100 worker
```

重点看：

- worker 是否已连接 Redis
- 是否有收到任务
- 是否有处理异常

### 6.3 Redis 是否正常

如果 Redis 不可用，Celery 往往无法正常收发任务。

可从 backend / worker 日志中观察：

- connection refused
- timeout
- broker unavailable

### 6.4 转换依赖是否齐全

若任务已触发但转换失败，应检查：

- ImageMagick / VIPS / Java / 其他依赖路径
- 输入文件路径是否存在
- 输出目录是否可写

---

## 7. 转换完成了，但 Manifest 打不开

## 症状

- 资产存在
- 衍生物可能也已生成
- 但 manifest URL 返回 404 或内容不正确

## 优先检查

### 7.1 manifest 路由是否存在

检查 backend 是否暴露了相应 manifest 接口。

### 7.2 public URL 是否配置正确

重点确认：

- `API_PUBLIC_URL`
- `CANTALOUPE_PUBLIC_URL`

如果这些值与当前对外访问地址不一致，manifest 里可能会生成错误链接。

### 7.3 资产 ID / 路径拼接是否正确

manifest 生成逻辑通常依赖：

- 资产标识
- 文件标识
- 预览资源路径

其中任一部分错误，都可能导致 manifest 可返回但内部引用失效。

### 7.4 nginx / 路由转发是否与 manifest 中 URL 一致

manifest 中生成的 URL 必须与当前真实可访问入口一致，否则浏览器端会继续失败。

---

## 8. Manifest 可以打开，但 Mirador 预览失败

## 症状

- manifest 地址可访问
- 但 Mirador 中图像无法显示
- 或显示空白 / 加载失败

## 优先检查

### 8.1 IIIF 图像服务地址是否真实可访问

从 manifest 中找到图像服务 URL，直接在浏览器中测试。

### 8.2 Cantaloupe 日志

```bash
docker compose logs --tail=100 cantaloupe
```

重点观察：

- 是否找不到源图像
- 是否权限不足
- 是否路径映射错误
- 是否返回图像解码错误

### 8.3 backend / worker / cantaloupe 是否使用一致的数据路径

很多预览失败本质上是：

- backend 认为文件存在
- worker 生成了结果
- 但 cantaloupe 实际读取不到对应路径

### 8.4 浏览器控制台错误

检查是否存在：

- 404
- 403
- CORS 问题
- 路径拼接错误

---

## 9. IIIF 图像服务失败

## 症状

- 访问 `/iiif/2/...` 返回 404 / 500
- 缩略图无法生成
- Mirador 一直加载不出来

## 优先检查

### 9.1 nginx 到 cantaloupe 的转发

确认 `/iiif/2` 是否正确代理到 cantaloupe。

### 9.2 Cantaloupe 自身配置

重点检查：

- 数据源路径
- 访问权限
- 路由前缀
- 缓存目录

### 9.3 输入文件是否存在且格式可读

若源文件损坏、路径错误或衍生文件未生成，IIIF 服务也会失败。

---

## 10. 下载/导出失败

## 症状

- 下载按钮存在但无法下载
- 返回 404 / 500
- 导出结果为空或结构错误

## 优先检查

### 10.1 导出文件路径是否存在
### 10.2 backend 下载接口是否正常
### 10.3 打包任务是否完成
### 10.4 临时目录或输出目录是否可写

---

## 11. 最常见根因清单

在当前项目阶段，最常见的问题通常集中在以下几类：

1. **Docker 服务未完全启动**
2. **数据库或 Redis 未就绪**
3. **worker 未实际处理任务**
4. **数据目录挂载不一致**
5. **manifest public URL 配置错误**
6. **nginx `/api` 或 `/iiif/2` 代理不一致**
7. **Cantaloupe 读取不到源文件或衍生文件**

---

## 12. 推荐的最小排查路径

如果时间有限，建议按以下最小路径排查：

### 第一步
```bash
docker compose ps
```

### 第二步
```bash
docker compose logs --tail=100 backend
```

### 第三步
```bash
docker compose logs --tail=100 worker
```

### 第四步
```bash
docker compose logs --tail=100 cantaloupe
```

### 第五步
手动检查：

- 前端入口是否可访问
- `/api/assets` 是否返回
- manifest URL 是否可访问
- manifest 中图像服务 URL 是否可访问

---

## 13. 与其他文档的关系

建议本文件与以下文档配合使用：

- `docs/DEMO_FLOW.md`
- `docs/ACCEPTANCE_CHECKLIST.md`
- `docs/SETUP_AND_DEPLOYMENT.md`
- `docs/WORKFLOW_GUIDE.md`

其中：

- `DEMO_FLOW.md` 用于标准演示路径
- `ACCEPTANCE_CHECKLIST.md` 用于最小验收标准
- `TROUBLESHOOTING.md` 用于故障定位入口
