# 认证与 IIIF 访问控制整合方案

## 1. 目的

这份文档用于说明 MDAMS 应用认证、资源权限与 IIIF 访问控制之间的关系，并明确当前阶段的实现方式。

当前项目的原则很明确：

- **认证体系统一**
- **权限来源统一**
- **IIIF 访问控制挂在 MDAMS 应用认证之下**
- **Cantaloupe 只负责图像处理，不负责业务权限判断**

这意味着：

> MDAMS 决定“谁能看”，Cantaloupe 决定“图怎么切”。

## 2. 当前已经具备的能力

### 2.1 应用层认证

当前仓库已经具备一套应用层认证骨架：

- 用户、角色、会话模型
- 登录与退出
- 当前用户上下文
- 前端菜单裁剪
- 后端关键接口保护

对应代码主要在：

- `backend/app/routers/auth.py`
- `backend/app/services/auth.py`
- `backend/app/permissions.py`
- `frontend/src/auth/permissions.ts`

### 2.2 IIIF 资源分发

当前 IIIF 仍然主要由两层组成：

- MDAMS 后端负责生成 Manifest
- Cantaloupe 负责提供图像服务
- Mirador 负责发起展示请求

对应代码主要在：

- `backend/app/routers/iiif.py`
- `backend/app/routers/assets.py`

## 3. 为什么必须统一

如果认证和 IIIF 不统一，会出现以下问题：

1. 页面能看到资源，但 Mirador 打不开图
2. 页面没有权限，但 IIIF 直链还能访问
3. `owner_only` 资源在业务接口里受限，但图像层仍可直接读取
4. 用户退出登录后，旧的 IIIF URL 仍可长期使用

对馆内系统来说，这些都属于高风险问题。

## 4. 当前阶段的推荐方案

### 方案 A：MDAMS 后端作为 IIIF 权限入口

这是当前阶段最推荐的实现方式。

流程如下：

1. 用户先登录 MDAMS
2. 前端通过 `/api/auth/context` 获取当前用户上下文
3. Mirador 请求 Manifest 时仍然访问 MDAMS 后端
4. MDAMS 后端检查：
   - 用户是否有对应权限
   - 资源是否处于可见范围
   - 用户是否属于责任范围
5. 通过后再返回 Manifest
6. 图像请求也通过 MDAMS 后端受控路径发往 Cantaloupe

### 优点

- 权限逻辑集中
- Mirador 与业务页面使用同一套登录上下文
- 不需要让 Cantaloupe 理解业务角色
- 方便先把 `visibility_scope` 和 `collection_scope` 做实

### 缺点

- MDAMS 后端会承担一层代理职责
- 后续如果并发更高，可能需要再拆分独立代理层

## 5. 资源权限与 IIIF 的关系

IIIF 可访问与否，不能只看“是否登录”，还要看资源本身的业务属性。

建议至少结合以下字段判断：

- `workflow_status`
- `visibility_scope`
- `collection_object_id`
- 用户角色
- 用户责任范围

推荐规则：

- `draft` / `pending_ingest_review`：不开放 IIIF 展示
- `ingested` / `published`：可按可见范围判断是否开放
- `open`：馆内可见用户可访问
- `owner_only`：仅责任范围内角色可访问

## 6. 当前阶段建议

当前阶段建议按下面顺序推进：

1. 先统一应用认证
2. 再统一资源可见范围
3. 再把 Manifest 生成接入权限校验
4. 再把图像访问收口到受控路径
5. 最后再考虑是否拆出独立 IIIF 代理层

## 7. 后续演进方向

如果未来项目变得更大，可以再考虑：

- 单独的 IIIF gateway / auth proxy
- 更细的 token 校验
- 更复杂的并发代理与缓存

但这些都应该放在当前原型稳定之后再做。

## 8. 当前结论

当前最稳妥的做法仍然是：

- **MDAMS 负责身份与权限**
- **MDAMS 负责可见范围判断**
- **MDAMS 负责 Manifest 入口**
- **Cantaloupe 继续专注图像服务**

一句话总结：

> **MDAMS 决定“谁能看”，Cantaloupe 决定“图怎么给”。**