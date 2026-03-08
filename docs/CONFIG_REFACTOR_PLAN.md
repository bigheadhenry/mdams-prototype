# CONFIG_REFACTOR_PLAN

## 目标

本文件用于记录 **MDAMS Prototype** 当前阶段的最小配置整理改造方案。

本轮改造的唯一原则是：

> 只整理 `.env.example` 和 `docker-compose.yml` 的配置来源，不主动改 IIIF / Manifest / Nginx 已跑通逻辑。

这不是一次部署体系重构，也不是一次 URL 结构优化，而是一次**低风险、保守型的配置归拢**。

---

## 一、改造目标

本轮改造的目标不是“重写 compose”，而是让项目未来切换环境时，优先修改：

- `.env`

而不是频繁修改：

- `docker-compose.yml`
- 后端代码
- Nginx 规则
- Manifest 生成逻辑

### 本轮希望达成的结果

- 将 `docker-compose.yml` 中写死的关键值改为 `${变量名}` 形式
- 补齐并规范 `.env.example`
- 为变量增加用途说明
- 保持当前已跑通的 URL 结构、代理结构、IIIF 路径结构不变

### 本轮明确边界

#### 做

- 把 compose 里写死的值改成环境变量引用
- 补齐 `.env.example`
- 为关键变量增加注释
- 将宿主机路径从 compose 中抽离出来
- 保持当前 API / IIIF 的外部访问结构不变

#### 不做

- 不改 `frontend/nginx.conf`
- 不改后端 Manifest URL 生成逻辑
- 不改 `/api` 与 `/iiif/2` 访问前缀
- 不改 Cantaloupe 实际 IIIF 路径格式
- 不改前端 axios 相对路径调用方式

---

## 二、当前仓库现状（基于现有文件）

### 当前 `.env.example`

当前仓库根目录下的 `.env.example` 已包含以下内容：

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `DATABASE_URL`
- `API_PUBLIC_URL`
- `CANTALOUPE_PUBLIC_URL`
- `HOST_UPLOAD_PATH`
- `HOST_NAS_PATH`
- `JAVA_OPTS`

但与当前 `docker-compose.yml` 实际使用相比，仍存在以下问题：

1. 变量命名与实际挂载路径不完全一致
2. compose 中仍大量硬编码
3. `REDIS_URL`、`VIPS_*`、`UPLOAD_DIR` 等关键运行参数未在 `.env.example` 中完整体现
4. 当前 `.env.example` 的默认 URL 为 `localhost`，而 compose 中实际使用的是 `192.168.5.13:3000`

### 当前 `docker-compose.yml`

当前 compose 里仍直接硬编码了：

- `DATABASE_URL`
- `REDIS_URL`
- `VIPS_DISC_THRESHOLD`
- `VIPS_CONCURRENCY`
- `API_PUBLIC_URL`
- `CANTALOUPE_PUBLIC_URL`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- 宿主机挂载路径 `/sunjing/project/文物库`
- 宿主机挂载路径 `/sunjing/project`
- 若干服务端口
- `JAVA_OPTS`

因此本轮改造的重点非常明确：

> 只把“值来源”从 compose 挪到 `.env`，不改现有运行逻辑。

---

## 三、建议的 `.env.example` 草案

以下是针对当前项目的**最小化、低风险**配置清单建议。

```env
# =========================
# Database
# =========================
POSTGRES_USER=meam
POSTGRES_PASSWORD=meam_secret
POSTGRES_DB=meam_db
DATABASE_URL=postgresql://meam:meam_secret@db:5432/meam_db

# =========================
# Redis / Worker
# =========================
REDIS_URL=redis://redis:6379/0

# =========================
# Public URLs
# 注意：这两个值直接影响 Manifest 和 IIIF 访问
# 不要随意改成容器内部地址
# 必须是浏览器可访问的外部地址
# =========================
API_PUBLIC_URL=http://192.168.5.13:3000/api
CANTALOUPE_PUBLIC_URL=http://192.168.5.13:3000/iiif/2

# =========================
# File Paths (Host)
# 宿主机路径，不是容器内路径
# =========================
HOST_MUSEUM_PATH=/sunjing/project/文物库
HOST_PROJECT_ROOT=/sunjing/project

# =========================
# File Paths (Container/App)
# 当前建议保持和现有逻辑一致
# =========================
UPLOAD_DIR=/app/uploads

# =========================
# Image / Processing
# =========================
VIPS_DISC_THRESHOLD=100m
VIPS_CONCURRENCY=2
JAVA_OPTS=-Xmx4g -Djava.security.egd=file:/dev/./urandom

# =========================
# Ports (optional for future cleanup)
# 当前可先保留默认值
# =========================
FRONTEND_PORT=3000
BACKEND_PORT=8000
DB_PORT=5432
REDIS_PORT=6379
CANTALOUPE_PORT=8182
FILEBROWSER_PORT=8081
```

### 说明

#### 1. 保留当前已跑通值

最关键的是以下两个配置：

- `API_PUBLIC_URL=http://192.168.5.13:3000/api`
- `CANTALOUPE_PUBLIC_URL=http://192.168.5.13:3000/iiif/2`

本方案**不主张**在本轮改造中将其替换为更“抽象”或更“优雅”的示例值。

原因是这两个值与以下链路耦合较深：

- 后端 Manifest 生成
- 前端读取 Manifest
- Mirador 加载 image service
- Nginx 代理路径
- Cantaloupe 对外访问方式

换句话说：

> 这两个变量不是普通展示配置，而是带强约束的运行配置。

#### 2. 将宿主机路径单独配置化

建议使用：

- `HOST_MUSEUM_PATH=/sunjing/project/文物库`
- `HOST_PROJECT_ROOT=/sunjing/project`

这样以后若 NAS 路径、项目根路径发生变化，只需要修改 `.env`，无需修改 compose 文件本体。

#### 3. 容器内路径先保持不动

建议保留：

- `UPLOAD_DIR=/app/uploads`

当前阶段不建议同时改动：

- 宿主机路径
- 容器内路径语义
- 后端内部读写逻辑

这样可以减少变量迁移带来的理解负担与联动风险。

---

## 四、`docker-compose.yml` 改造思路

本节只描述建议替换方式，不代表已经执行修改。

### 1. backend 服务

#### 当前问题

backend 中写死了：

- `DATABASE_URL`
- `REDIS_URL`
- `VIPS_DISC_THRESHOLD`
- `VIPS_CONCURRENCY`
- `API_PUBLIC_URL`
- `CANTALOUPE_PUBLIC_URL`

#### 建议改法

从：

```yaml
environment:
  - DATABASE_URL=postgresql://meam:meam_secret@db:5432/meam_db
  - REDIS_URL=redis://redis:6379/0
  - VIPS_DISC_THRESHOLD=100m
  - VIPS_CONCURRENCY=2
  - API_PUBLIC_URL=http://192.168.5.13:3000/api
  - CANTALOUPE_PUBLIC_URL=http://192.168.5.13:3000/iiif/2
```

改为：

```yaml
environment:
  - DATABASE_URL=${DATABASE_URL}
  - REDIS_URL=${REDIS_URL}
  - VIPS_DISC_THRESHOLD=${VIPS_DISC_THRESHOLD}
  - VIPS_CONCURRENCY=${VIPS_CONCURRENCY}
  - API_PUBLIC_URL=${API_PUBLIC_URL}
  - CANTALOUPE_PUBLIC_URL=${CANTALOUPE_PUBLIC_URL}
  - UPLOAD_DIR=${UPLOAD_DIR}
```

### 2. backend volume 挂载

#### 当前问题

宿主机路径写死为：

```yaml
- /sunjing/project/文物库:/app/uploads
```

#### 建议改法

改为：

```yaml
- ${HOST_MUSEUM_PATH}:/app/uploads
```

如需进一步统一，也可以写成：

```yaml
- ${HOST_MUSEUM_PATH}:${UPLOAD_DIR}
```

但从风险控制角度看，本轮更保守的做法是：

> 只外提宿主机路径，容器内路径先维持 `/app/uploads` 不变。

### 3. celery_worker 服务

#### 原则

worker 与 backend 必须共享同一文件视图，因此应保持相同的：

- 数据库配置
- Redis 配置
- 上传目录配置
- pyvips 相关参数
- 宿主机文件挂载

#### 建议改法

```yaml
environment:
  - DATABASE_URL=${DATABASE_URL}
  - REDIS_URL=${REDIS_URL}
  - VIPS_DISC_THRESHOLD=${VIPS_DISC_THRESHOLD}
  - VIPS_CONCURRENCY=${VIPS_CONCURRENCY}
  - UPLOAD_DIR=${UPLOAD_DIR}
```

并同步：

```yaml
volumes:
  - ${HOST_MUSEUM_PATH}:/app/uploads
```

### 4. db 服务

#### 当前问题

数据库初始化参数写死。

#### 建议改法

从：

```yaml
environment:
  - POSTGRES_USER=meam
  - POSTGRES_PASSWORD=meam_secret
  - POSTGRES_DB=meam_db
```

改为：

```yaml
environment:
  - POSTGRES_USER=${POSTGRES_USER}
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
  - POSTGRES_DB=${POSTGRES_DB}
```

### 5. cantaloupe 服务

这是另一个必须特别谨慎的部分。

#### 原则

> 只改“值来源”，不改“路径和逻辑”。

#### 建议只做以下调整

将 Java 参数外提：

```yaml
environment:
  - CANTALOUPE_CONFIG=/etc/cantaloupe.properties
  - JAVA_OPTS=${JAVA_OPTS}
  - LANG=C.UTF-8
  - LC_ALL=C.UTF-8
```

将宿主机路径外提：

```yaml
volumes:
  - ${HOST_MUSEUM_PATH}:/var/lib/cantaloupe/images
  - ./cantaloupe.properties:/etc/cantaloupe.properties
  - /dev/urandom:/dev/random:ro
```

#### 本轮不建议改动

- 不改 Cantaloupe 容器内 image 根目录
- 不改 `/iiif/2` 服务前缀
- 不改前端 Nginx 对其代理方式

### 6. frontend 服务

frontend 当前前端代码使用相对路径，请求风险相对较低。

#### 建议

如果 compose 当前只是：

```yaml
ports:
  - "3000:80"
```

则本轮可先保持不动。

如果希望顺手做极轻量配置化，可以改为：

```yaml
ports:
  - "${FRONTEND_PORT}:80"
```

但这不是本轮必须项。

### 7. filebrowser / 其他服务

如果 filebrowser 依赖宿主机路径，建议同样只外提 volume：

```yaml
volumes:
  - ${HOST_PROJECT_ROOT}:/srv
```

并保留其容器内工作方式不变。

---

## 五、compose 改造策略

这部分是本方案的核心风险控制原则。

### 策略 1：只替换硬编码值，不改字段结构

允许做的事情：

- `API_PUBLIC_URL=xxx` → `${API_PUBLIC_URL}`
- `/sunjing/project/文物库:/app/uploads` → `${HOST_MUSEUM_PATH}:/app/uploads`
- `POSTGRES_USER=meam` → `${POSTGRES_USER}`

不建议顺手做的事情：

- 不改容器名
- 不改端口方案
- 不改服务名
- 不改内部路径
- 不改 nginx upstream 名称
- 不改 depends_on 结构
- 不改 build / image 策略

### 策略 2：IIIF 相关值必须照搬当前已跑通值

特别是：

- `API_PUBLIC_URL`
- `CANTALOUPE_PUBLIC_URL`

这两个值不是自由配置项，而是与整个展示链路强耦合的配置。

未来当然可以调整，但必须伴随完整链路验证，而不是在本轮最小配置整理时顺手优化。

### 策略 3：先不删除后端 fallback

如果后端代码中已有 `localhost:8000`、`localhost:8182` 之类 fallback，本轮建议先不主动清理。

原因不是它们“完美”，而是：

- 当前重点是“值来源整理”
- 不是“运行逻辑收口”
- 贸然清理 fallback 可能引入隐藏回归风险

---

## 六、明确禁改项清单

以下内容应视为**本轮禁止改动项**。

### 1. `frontend/nginx.conf` 中以下内容禁止改动

- `/api/` 路由代理
- `/iiif/2/` 路由代理
- `proxy_pass` 指向关系
- `X-Forwarded-Prefix` 相关头

### 2. 后端 Manifest 生成逻辑中以下内容禁止改动

- manifest id 规则
- canvas id 规则
- annotation id 规则
- image service id 规则

### 3. 前端以下行为禁止改动

- `/api/...` 相对路径请求方式
- Mirador 读取 manifest 的方式

### 4. Cantaloupe 以下内容禁止改动

- 容器内 image 根目录逻辑
- `/iiif/2` URL 前缀
- 现有路径结构

### 5. 本轮不做的附带优化

- 不重命名环境变量以追求“更统一但不兼容”
- 不引入新的反向代理层
- 不将外部 URL 改为容器服务名
- 不在本轮合并 frontend / backend / cantaloupe 的访问策略

---

## 七、验收标准

如果后续正式执行本方案，建议只按以下关键链路验收。

### 验收 1：页面能正常打开

- 前端首页可访问
- 无明显白屏或关键报错

### 验收 2：普通资产列表正常

- `/api/assets` 返回正常
- 基本列表读取不受影响

### 验收 3：Manifest 仍正常

访问某个：

- `/api/iiif/{id}/manifest`

重点确认返回中的：

- `id`
- image service
- canvas 引用

仍保持当前结构。

### 验收 4：Mirador 预览正常

这是最关键的展示验收项。

### 验收 5：PSB → BigTIFF 流程不受影响

- 上传正常
- 转换正常
- 预览正常

即：

> 上传、转换、IIIF、预览整条链路均不受本轮配置整理影响。

---

## 八、建议执行顺序

如果未来正式落地本方案，建议严格按以下顺序执行：

1. 先备份当前 `docker-compose.yml`
2. 只修改 `.env.example`
3. 再修改 `docker-compose.yml` 的变量引用
4. 不改其他文件
5. 启动前人工检查 `API_PUBLIC_URL` / `CANTALOUPE_PUBLIC_URL`
6. 启动后先测试 assets 接口
7. 再测试 manifest
8. 最后测试 Mirador 预览

即：

> 先测接口，再测 IIIF，再测前端预览。

---

## 九、结论

这份草案的核心思路是：

> 把“值”从 compose 挪出去，但不动“逻辑”。

它适合当前项目的原因在于：

- 当前系统已经有一条跑通的 API / Manifest / IIIF / Mirador 链路
- IIIF 相关路径与代理规则存在明显耦合
- 当前最重要的是降低未来环境迁移的修改成本
- 不是在此时追求架构层面的“更优雅”重构

因此，本轮最稳妥的策略应当是：

- 优先落文档
- 明确变量边界
- 明确禁改项
- 后续再基于文档进行逐项替换与验证

---

## 十、建议的后续动作

下一步建议二选一：

### 选项 A：按本文档执行最小改造

范围仅限：

- `.env.example`
- `docker-compose.yml`

### 选项 B：先输出逐行修改清单

即在不实际改文件的情况下，先标明：

- compose 哪一段建议改成什么
- 哪一段必须保持不动

对于当前项目，建议优先采用：

> 先留档，再执行。
