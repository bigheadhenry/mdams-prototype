# MDAMS 认证与 IIIF 访问控制整合方案

## 目的

本文档用于明确 MDAMS 应用认证、资源权限控制、Mirador 展示与 IIIF 图像服务之间的关系，并给出当前阶段与后续阶段的实现路线。

当前重点不是新建第二套 IIIF 用户体系，而是让 IIIF 访问控制建立在 MDAMS 现有认证与权限框架之上。

## 核心结论

1. MDAMS 应用认证与 IIIF 访问控制不是同一个层面的能力，但必须共享同一套身份与权限来源。
2. 当前阶段应以 MDAMS 应用认证作为主认证体系。
3. IIIF 访问控制应作为 MDAMS 资源权限控制的延伸能力，而不是独立权限系统。
4. 当前最稳的方案是：先由 MDAMS 后端作为 IIIF 权限入口，再将底层图像访问代理到 Cantaloupe。

## 当前项目中的两个层次

### 1. 应用层认证

当前项目已经具备应用层认证骨架：

- 用户/角色/会话模型
- 登录与退出
- 角色权限解析
- 前端菜单裁剪
- 后端关键接口保护

对应代码：

- [auth.py](C:\Users\bighe\OneDrive\AI\Codex\mdams-prototype\backend\app\routers\auth.py)
- [permissions.py](C:\Users\bighe\OneDrive\AI\Codex\mdams-prototype\backend\app\permissions.py)
- [auth.py](C:\Users\bighe\OneDrive\AI\Codex\mdams-prototype\backend\app\services\auth.py)

### 2. IIIF 资源分发层

当前 IIIF 主要由：

- MDAMS 后端生成 Manifest
- Cantaloupe 提供图像服务
- Mirador 发起展示请求

对应代码：

- [iiif.py](C:\Users\bighe\OneDrive\AI\Codex\mdams-prototype\backend\app\routers\iiif.py)

目前 Manifest 生成与图像访问仍然偏“开放式路由”，尚未正式接入基于用户上下文的权限控制。

## 为什么必须统一

如果认证和 IIIF 不统一，会出现以下问题：

1. 页面能看到资源，但 Mirador 打不开图。
2. 页面无权限，但 IIIF 直链还能访问。
3. `owner_only` 资源在业务接口受限，但底层图像仍可被直接读取。
4. 用户退出登录后，IIIF URL 仍可长期使用。

对 MDAMS 这类馆内系统来说，这些都属于高风险问题。

## 统一原则

### 原则 1：身份统一

系统只保留一套身份体系：

- 登录用户
- 用户角色
- 用户权限
- collection scope

IIIF 不应再单独维护第二套用户或第二套角色。

### 原则 2：权限来源统一

IIIF 是否可访问，必须依赖与业务接口相同的权限判断基础：

- `RBAC`
- `visibility_scope`
- `collection_owner` 的责任范围
- 资源业务状态

### 原则 3：服务职责分离

MDAMS 负责回答：

- 谁能看
- 谁能申请
- 谁能导出
- 哪些资源属于什么可见范围

Cantaloupe 负责回答：

- 图怎么切
- 图怎么缩放
- 图怎么缓存

也就是：

- MDAMS 负责权限
- Cantaloupe 负责图像处理

## 当前阶段推荐方案

## 方案 A：MDAMS 后端作为 IIIF 权限入口

这是当前项目最推荐的方案。

### 访问路径

1. 用户先登录 MDAMS
2. 前端通过 `/api/auth/context` 获取当前用户上下文
3. Mirador 请求 Manifest 时，仍然请求 MDAMS 后端
4. MDAMS 后端检查：
   - 是否具备 `image.view`
   - 资源是否为 `open`
   - 若为 `owner_only`，是否在责任范围内
5. 检查通过后，再由后端返回 Manifest
6. 图像访问阶段，前端不直接公开底层真实资源地址，而是通过 MDAMS 的受控路径访问图像或 info.json，再由后端代理到 Cantaloupe

### 当前阶段的优点

- 权限逻辑集中
- Mirador 与业务页面使用同一套登录态
- 不需要让 Cantaloupe 自己理解应用权限模型
- 便于先把 `visibility_scope`、`collection_scope` 和 `RBAC` 做实

### 当前阶段的缺点

- MDAMS 后端会多承担一层代理职责
- 后续高并发场景下需要进一步拆分

## 后续演进方案

## 方案 B：统一身份，IIIF 走独立权限代理层

当系统进入更成熟阶段，可以演进为：

- MDAMS 仍然负责主认证
- IIIF 前增加一个专门的 auth proxy 或 gateway
- 该代理层根据 MDAMS 的 token 或会话结果校验权限
- Cantaloupe 继续专注于图像处理

此时架构变为：

- MDAMS：认证、权限、资源状态
- IIIF Proxy：IIIF 权限放行
- Cantaloupe：图像切片与缓存

这个阶段比当前复杂得多，不建议在原型阶段一步到位。

## Mirador 的处理建议

Mirador 是 IIIF 消费者，不应承担权限判断逻辑。

Mirador 只负责：

- 请求 Manifest
- 打开 Canvas
- 渲染图像

权限判断应发生在：

- Manifest 返回前
- info.json 返回前
- 图像切片返回前

因此后续接 IIIF 权限时，不应尝试在 Mirador 前端做“假限制”，而应在 MDAMS 后端或其代理层真正拦截。

## 对当前代码的具体建议

### 第一阶段

1. 为 [iiif.py](C:\Users\bighe\OneDrive\AI\Codex\mdams-prototype\backend\app\routers\iiif.py) 加入认证上下文
2. 在 Manifest 生成前校验 `image.view`
3. 引入 `visibility_scope`
4. 对 `owner_only` 资源增加责任范围判断

### 第二阶段

1. 为图像级访问增加受控代理入口
2. 不再让前端直接依赖裸 Cantaloupe 地址
3. 将 Mirador 的图像访问改为通过 MDAMS 受控路径

### 第三阶段

1. 再考虑是否拆出独立 IIIF 权限代理
2. 再考虑是否让 Cantaloupe delegate 读取应用层鉴权结果

## 与资源权限模型的关系

IIIF 权限控制依赖于后续资源模型中至少两项信息：

- `workflow_status`
- `visibility_scope`

推荐约束如下：

- `draft` / `pending_ingest_review`
  不允许进入 IIIF 展示

- `ingested` / `published`
  可根据 `visibility_scope` 判断是否允许展示

- `open`
  具备浏览权限的馆内用户可看

- `owner_only`
  仅责任范围内角色可看

这意味着 IIIF 权限整合不能独立完成，它需要和资源范围控制同步推进。

## 当前阶段的实施顺序

1. 先完成真实用户与登录上下文
2. 再补资源级 `visibility_scope`
3. 再把 Manifest 路由接入权限校验
4. 再做图像访问代理
5. 最后才考虑独立 IIIF 权限层

## 当前结论

对 MDAMS 当前阶段而言，最合适的策略是：

- 认证体系统一
- 权限来源统一
- IIIF 访问由 MDAMS 后端受控放行
- Cantaloupe 继续专注图像处理

一句话概括：

MDAMS 决定“谁能看”，Cantaloupe 决定“图怎么给”。
