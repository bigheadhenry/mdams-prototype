# 认证与 IIIF 访问控制

- 最后核对日期：2026-04-06
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

当前 Manifest 中写入的图像服务地址，不是后端受控代理地址，而是基于 `CANTALOUPE_PUBLIC_URL` 生成的公开 IIIF 地址。

本地推荐值通常是：

```text
http://localhost:3000/iiif/2
```

前端 Nginx 会把它代理到 Cantaloupe。

### 4.3 当前尚未完全收口的部分

后端虽然已经提供了：

- `/api/iiif/{asset_id}/service/{image_path:path}`

这样的代理接口，并且它也会做权限检查，但当前 Manifest 默认并没有把图像服务 `id` 指向这个受控代理路径。

这意味着当前状态是：

- Manifest 入口已经受控
- 资产详情和列表入口已经受控
- 但 IIIF 切片 / `info.json` 访问还没有完全统一到应用认证入口

## 5. 当前风险判断

当前风险不在“页面能否登录”，而在“图像服务是否和业务权限完全一致”。

如果不进一步收口，理论上会存在以下风险：

1. 页面本身受权限控制，但图像服务地址仍然过于公开
2. `owner_only` 资源的 Manifest 已受控，但后续切片访问没有完全沿用同一套鉴权入口
3. 应用权限和 IIIF 图像服务权限之间仍存在分层差距

因此，当前最准确的表述不是“认证与 IIIF 已完全统一”，而是：

> 当前已经完成 Manifest 级别的认证收口，但还没有完全完成图像切片级别的统一鉴权。

## 6. 当前推荐配置

为了让当前实现尽量稳定，建议本地保持：

```text
API_PUBLIC_URL=http://localhost:3000/api
CANTALOUPE_PUBLIC_URL=http://localhost:3000/iiif/2
```

这样至少可以保证：

- 前端统一走代理
- Manifest 与 IIIF 服务地址在浏览器视角下是稳定的

## 7. 推荐的下一步收口方向

建议下一步按以下顺序推进：

1. 保持应用认证与资源可见范围判断继续由 MDAMS 负责
2. 把 Manifest 中的图像服务 `id` 切换为后端受控代理路径
3. 让 IIIF 切片和 `info.json` 也统一经过应用权限入口
4. 再评估是否需要单独的 IIIF auth proxy / gateway

## 8. 当前结论

当前最准确的结论是：

- MDAMS 已经负责登录、会话和资源可见性判断
- Manifest 访问已经进入应用权限控制
- 资源列表和详情也已经进入权限控制
- IIIF 图像切片访问尚未完全统一到应用认证入口

一句话总结：

> 当前是“Manifest 受控、图像服务未完全收口”的阶段，而不是“认证与 IIIF 已完全统一”的阶段。

## 9. 关联文档

- `../03-产品与流程/USER_ROLE_PERMISSION_MATRIX.md`
- `../05-部署与运维/SETUP_AND_DEPLOYMENT.md`
- `../05-部署与运维/TROUBLESHOOTING.md`
