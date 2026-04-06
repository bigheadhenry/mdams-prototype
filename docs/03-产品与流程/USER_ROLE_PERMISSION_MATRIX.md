# 用户角色与权限矩阵

- 最后核对日期：2026-04-06
- 核对范围：`backend/app/permissions.py`、`backend/app/services/auth.py`、`frontend/src/auth/permissions.ts`、`frontend/src/App.tsx`

## 1. 目标

本文件用于说明当前 MDAMS 原型中已经落地的角色、权限、菜单入口和责任范围规则。

当前结论以代码为准，不以历史方案稿为准。

## 2. 当前角色清单

当前系统内置并播种以下角色：

| 角色 key | 标签 | 说明 |
| :--- | :--- | :--- |
| `image_structured_editor` | 2D Structured Editor | 维护二维资源结构化元数据 |
| `image_ingest_operator` | 2D Ingest Operator | 执行二维文件上传与入库准备 |
| `image_ingest_reviewer` | 2D Ingest Reviewer | 审核二维资源入库准备情况 |
| `image_resource_manager` | 2D Resource Manager | 维护二维资源与元数据质量 |
| `image_metadata_entry` | Image Metadata Entry | 创建与维护图像记录 |
| `image_photographer_upload` | Image Photographer Upload | 向待上传图像记录补充文件并执行匹配 |
| `three_d_operator` | 3D Operator | 管理三维对象、版本和上传 |
| `application_reviewer` | Application Reviewer | 审批利用申请并导出交付包 |
| `collection_owner` | Collection Owner | 在责任范围内查看和管理资源 |
| `resource_user` | Resource User | 浏览开放资源并提交申请 |
| `system_admin` | System Admin | 管理全局权限与系统能力 |

## 3. 当前权限清单

代码中当前已经使用的权限包括：

### 3.1 通用

- `dashboard.view`
- `platform.view`
- `system.manage`

### 3.2 二维资源

- `image.view`
- `image.edit`
- `image.delete`
- `image.upload`
- `image.ingest_review`
- `image.edit_scope`

### 3.3 图像记录

- `image.record.create`
- `image.record.view`
- `image.record.edit`
- `image.record.submit`
- `image.record.return`
- `image.record.list`
- `image.record.view_ready_for_upload`
- `image.file.upload`
- `image.file.match`

### 3.4 三维资源

- `three_d.view`
- `three_d.edit`
- `three_d.upload`
- `three_d.edit_scope`

### 3.5 利用申请

- `application.create`
- `application.view_own`
- `application.view_all`
- `application.review`
- `application.export`

### 3.6 范围相关

- `collection.scope`

## 4. 角色到权限映射

下表按当前 `ROLE_PERMISSIONS` 整理：

| 角色 | 当前权限 |
| :--- | :--- |
| `image_structured_editor` | `dashboard.view`, `image.view`, `image.edit`, `platform.view` |
| `image_ingest_operator` | `dashboard.view`, `image.view`, `image.upload`, `platform.view` |
| `image_ingest_reviewer` | `dashboard.view`, `image.view`, `image.ingest_review`, `platform.view` |
| `image_resource_manager` | `dashboard.view`, `image.view`, `image.edit`, `image.delete`, `platform.view` |
| `image_metadata_entry` | `dashboard.view`, `image.view`, `platform.view`, `image.record.create`, `image.record.view`, `image.record.edit`, `image.record.submit`, `image.record.return`, `image.record.list` |
| `image_photographer_upload` | `dashboard.view`, `image.view`, `platform.view`, `image.record.view`, `image.record.view_ready_for_upload`, `image.file.upload`, `image.file.match` |
| `three_d_operator` | `dashboard.view`, `three_d.view`, `three_d.upload`, `three_d.edit`, `platform.view` |
| `application_reviewer` | `dashboard.view`, `image.view`, `platform.view`, `application.view_all`, `application.review`, `application.export` |
| `collection_owner` | `dashboard.view`, `image.view`, `image.edit_scope`, `three_d.view`, `three_d.edit_scope`, `platform.view`, `collection.scope` |
| `resource_user` | `dashboard.view`, `image.view`, `three_d.view`, `platform.view`, `application.create`, `application.view_own` |
| `system_admin` | 拥有当前全部业务权限，并额外拥有 `system.manage` |

## 5. 菜单入口规则

前端当前按权限控制菜单可见性，菜单与权限关系如下：

| 菜单 key | 菜单含义 | 显示条件 |
| :--- | :--- | :--- |
| `1` | 仪表盘 | `dashboard.view` |
| `2` | 二维资源 | `image.view` |
| `3` | 申请车 | `application.create` |
| `4` | 入库处理 | `image.upload` 或 `image.ingest_review` 或 `image.edit` |
| `5` | 统一资源目录 | `platform.view` |
| `6` | 统一资源详情 | `platform.view` |
| `7` | 三维管理 | `three_d.view` |
| `8` | 申请管理 | `application.view_all` 或 `application.review` 或 `application.export` |
| `9` | 图像记录工作台 | `image.record.list` 或 `image.record.view_ready_for_upload` |

## 6. 可见范围规则

当前代码中已经落地两级可见范围：

| 可见范围 | 含义 |
| :--- | :--- |
| `open` | 对拥有查看权限的馆内用户开放 |
| `owner_only` | 仅系统管理员或责任范围命中的人员可见 |

后端当前访问判断逻辑：

- `open`：要求用户至少具备 `image.view` 或 `three_d.view`
- `owner_only`：系统管理员直接可见；其他用户只有在 `collection_object_id` 落入自身 `collection_scope` 时才可见

## 7. 当前默认测试用户

当前播种的默认测试用户包括：

| 用户名 | 角色 |
| :--- | :--- |
| `image_editor` | `image_structured_editor` |
| `image_ingest` | `image_ingest_operator` |
| `image_review` | `image_ingest_reviewer` |
| `image_manager` | `image_resource_manager` |
| `image_metadata_entry` | `image_metadata_entry` |
| `image_photographer` | `image_photographer_upload` |
| `three_d_operator` | `three_d_operator` |
| `application_review` | `application_reviewer` |
| `collection_owner` | `collection_owner` |
| `resource_user` | `resource_user` |
| `system_admin` | `system_admin` |

默认密码统一为：

```text
mdams123
```

## 8. 角色使用建议

### 8.1 图像记录工作流

推荐角色分工如下：

- `image_metadata_entry` 负责建记录、填元数据、提交
- `image_photographer_upload` 负责从待上传池领取并补文件
- `image_ingest_reviewer` 负责审核入库准备情况

### 8.2 二维资源治理

推荐角色分工如下：

- `image_structured_editor` 偏结构化元数据
- `image_ingest_operator` 偏上传与入库准备
- `image_resource_manager` 偏维护、修正和清理

### 8.3 资源利用

- `resource_user` 负责浏览开放资源与提交申请
- `application_reviewer` 负责审批与导出

### 8.4 责任范围管理

- `collection_owner` 是当前责任范围逻辑的核心角色
- 它的能力不来自全局编辑，而来自 `collection_scope` 与资源归属匹配

## 9. 当前局限

当前权限体系已经可用，但仍有这些边界：

- 还没有完整的后台角色管理界面
- `application.view_own` 与更细粒度的申请归属控制还可以继续增强
- `owner_only` 目前主要围绕责任范围做判断，规则仍可进一步细化
- 菜单显示和接口保护已经联动，但文档与实现仍在进一步收敛

## 10. 关联文档

- `FRONTEND_MENU_VISIBILITY_MATRIX.md`
- `WORKFLOW_GUIDE.md`
- `../01-总览/PROJECT_STATUS.md`
