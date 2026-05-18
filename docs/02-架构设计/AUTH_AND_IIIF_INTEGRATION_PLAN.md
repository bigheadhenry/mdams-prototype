# 认证与 IIIF 访问控制

- 最后核对日期：2026-05-17
- 核对范围：`backend/app/routers/auth.py`、`backend/app/permissions.py`、`backend/app/routers/iiif.py`、`backend/app/routers/assets.py`、`frontend/src/MiradorViewer.tsx`、`frontend/nginx.conf`

## 1. 目标

本文件用于说明当前 MDAMS 中认证、资源可见范围和 IIIF 访问的真实关系。

重点是区分：

- 当前已经实现了什么
- 当前还没有完全实现什么
- 下一步应如何收口

## 2. 当前已经实现的认证能力

当前项目已经具备应用层认证骨架：

- `/api/auth/users`：列出可用测试用户
- `/api/auth/login`：登录并返回 token
- `/api/auth/context`：返回当前用户上下文
- `/api/auth/logout`：退出登录

当前登录成功后：

- 前端把 token 写入 `localStorage`
- Axios 默认带上 `Authorization: Bearer ...`
- 后端根据 session token 解析当前用户

## 3. 当前已经实现的权限能力

后端当前已经实现：

- 角色到权限的映射
- `require_permission()` 和 `require_any_permission()`
- `collection_scope` 责任范围判断
- `open` / `owner_only` 可见范围判断

这意味着当前权限已经不仅用于菜单裁剪，也用于接口保护。

## 4. 当前 IIIF 链路的真实状态

### 4.1 已经实现的部分

当前 Manifest 访问已经受应用权限控制：

- 接口：`/api/iiif/{asset_id}/manifest`
- 要求权限：`image.view`
- 同时会检查资源是否对当前用户可见

当前后端会基于：

- `visibility_scope`
- `collection_object_id`
- 当前用户权限
- 当前用户 `collection_scope`

来决定是否允许返回 Manifest。

### 4.2 当前图像服务地址

当前 Manifest 中写入的图像服务地址已经是后端受控代理地址：

- `/api/iiif/{asset_id}/service/{image_path}`

后端代理会先复用资产可见性判断，再转发到 Cantaloupe 上游服务。`CANTALOUPE_INTERNAL_URL` 用于后端访问上游；`CANTALOUPE_PUBLIC_URL` 仍作为兼容配置和本地默认值存在。

本地推荐值通常是：

```text
API_PUBLIC_URL=http://localhost:3000/api
CANTALOUPE_PUBLIC_URL=http://localhost:8182/iiif/2
CANTALOUPE_INTERNAL_URL=http://localhost:8182/iiif/2
```

Manifest 的 `body.service.id` 应由 `API_PUBLIC_URL` 生成，而不是直接暴露为前端 Nginx 下的 `/iiif/2` 路径。

### 4.3 当前已经收口的部分

后端已经提供并使用：

- `/api/iiif/{asset_id}/service/{image_path:path}`

该接口会：

- 校验当前用户是否具备 `image.view`
- 校验资源是否对当前用户可见
- 解析允许访问的 IIIF 源文件
- 代理 Cantaloupe 的 `info.json` 与切片请求
- 对未 ready 的资源返回 `no-store` 缓存策略

因此，当前稳定状态是：

- Manifest 入口已受控
- 资产详情和列表入口已受控
- IIIF `info.json` 和切片访问已通过后端代理进入同一套可见性判断

## 5. 当前风险判断

当前主要风险不再是“Manifest 受控但切片绕过”，而是“部署时上游 Cantaloupe 是否仍被不必要地暴露给外部网络”。

如果不进一步收口，理论上会存在以下风险：

1. Cantaloupe 端口如果在生产网络直接暴露，仍可能形成旁路访问面
2. `.env` 中的 `CANTALOUPE_INTERNAL_URL` 如果配置到错误地址，后端代理会失败
3. 部署文档、反向代理和 Manifest 样例必须保持与 `/api/iiif/.../service/...` 契约一致

因此，当前最准确的表述是：

> 当前已经完成 Manifest 与图像服务代理级别的应用鉴权收口；生产部署仍应避免把 Cantaloupe 作为公共访问入口。

## 6. 当前推荐配置

为了让当前实现尽量稳定，建议本地保持：

```text
API_PUBLIC_URL=http://localhost:3000/api
CANTALOUPE_PUBLIC_URL=http://localhost:8182/iiif/2
CANTALOUPE_INTERNAL_URL=http://localhost:8182/iiif/2
```

这样至少可以保证：

- 前端统一走代理
- Manifest 与 IIIF 服务地址在浏览器视角下统一进入 `/api/iiif/...`

## 7. 推荐的下一步收口方向

建议下一步按以下顺序推进：

1. 生产环境不直接向公网暴露 Cantaloupe
2. 保持 Manifest 样例、部署配置和前端查看器都以 `/api/iiif/...` 为主入口
3. 补充代理层性能和缓存策略测试
4. 再评估是否需要单独的 IIIF auth gateway 或边缘缓存

## 8. 当前结论

当前最准确的结论是：

- MDAMS 已经负责登录、会话和资源可见性判断
- Manifest 访问已经进入应用权限控制
- 资源列表和详情也已经进入权限控制
- IIIF 图像切片访问已经通过后端代理进入应用权限控制

一句话总结：

> 当前是“Manifest 与图像服务代理均受控，生产部署需避免 Cantaloupe 旁路暴露”的阶段。

## 9. 关联文档

- `../03-产品与流程/USER_ROLE_PERMISSION_MATRIX.md`
- `../05-部署与运维/SETUP_AND_DEPLOYMENT.md`
- `../05-部署与运维/TROUBLESHOOTING.md`
