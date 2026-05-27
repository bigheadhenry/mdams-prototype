# 资源申请与交付工作流

- 最后核对日期：2026-05-23
- 文档状态：current
- 核对口径：以当前已实现的申请车、申请单、审批和交付包导出能力为准
- 相关自动化护栏：`backend/tests/test_standard_demo_flow.py`、`backend/tests/test_applications.py`、`frontend/tests/dashboard.spec.ts`

## 1. 目标

本文件用于说明 MDAMS Prototype 当前资源利用申请与交付闭环的真实边界。它服务三个场景：

1. 开发者判断申请相关改动应影响哪些接口和页面。
2. 演示人员按稳定路径展示资源从浏览到交付的业务闭环。
3. 后续扩展审批、权限和交付格式时保持兼容的字段契约。

## 2. 当前闭环

当前最小闭环为：

```text
统一资源目录 / 统一资源详情
  -> 加入申请车
  -> 提交申请单
  -> 申请管理中审批
  -> 导出交付包
  -> 申请状态变为 fulfilled
```

这条链路当前可覆盖二维资源，也可以记录三维和视频等统一平台资源。二维本地资产在导出时会复制实际文件；三维和视频等未绑定本地二维 `Asset` 的条目会进入交付清单，但当前不会自动打包其全部源文件。

## 3. 角色与权限

| 环节 | 权限 | 当前推荐角色 |
| :--- | :--- | :--- |
| 浏览统一资源 | `platform.view` | `resource_user`、`system_admin` |
| 加入申请车 | `application.create` | `resource_user`、`system_admin` |
| 提交申请 | `application.create` | `resource_user`、`system_admin` |
| 查看申请管理 | `application.view_all` / `application.review` / `application.export` | `application_reviewer`、`system_admin` |
| 审批 | `application.review` | `application_reviewer`、`system_admin` |
| 导出交付包 | `application.export` | `application_reviewer`、`system_admin` |

`resource_user` 在前端有单角色菜单覆盖规则：默认只显示统一资源目录与申请车，用于模拟普通利用申请人员的最小视图。

## 4. 申请车条目契约

申请车条目应尽量保留统一平台定位字段：

| 字段 | 含义 |
| :--- | :--- |
| `cartKey` | 前端去重用 key，通常使用统一资源 `id` |
| `assetId` | 二维本地资产 ID；非二维来源可为空 |
| `sourceSystem` | 来源系统，如 `image_2d`、`three_d`、`video` |
| `sourceId` | 来源内稳定 ID |
| `resourceType` | 统一资源类型 |
| `title` | 申请资源标题 |
| `manifestUrl` | 当前主要访问入口 |
| `sourceLabel` | 来源标签 |
| `objectNumber` | 当前使用统一资源 ID 或业务对象号 |
| `note` | 申请备注 |

前端统一通过 `buildApplicationCartItemFromUnifiedResource` 将统一资源转换为申请车条目，避免目录页、详情页和 Mirador 入口产生不同字段语义。

## 5. 后端申请单契约

后端 `POST /api/applications` 要求：

- 申请单必须包含至少一个条目。
- 每个条目必须满足以下任一条件：
  - 有 `asset_id`
  - 有 `source_system + source_id`
- 如果传入 `asset_id`，后端会验证二维资产存在。
- 如果没有 `asset_id`，条目作为统一资源定位记录进入申请单。

申请状态当前包括：

| 状态 | 含义 |
| :--- | :--- |
| `submitted` | 已提交，待处理 |
| `approved` | 已通过，可导出 |
| `rejected` | 已拒绝 |
| `fulfilled` | 已交付 |

## 6. 交付包边界

当前交付包导出行为：

1. 只允许导出 `approved` 或已经 `fulfilled` 的申请。
2. 申请包含二维 `Asset` 时，会将物理文件复制到交付包 `data/` 目录。
3. 申请包含非二维或未绑定资产的统一资源时，会在 `application.json` 中保留来源定位、标题、manifest、备注和交付说明。
4. 导出后申请状态更新为 `fulfilled`。

当前交付包不承诺：

- 自动打包三维对象下全部模型表现和文件。
- 自动导出视频源文件。
- 按申请用途自动选择不同分辨率、格式或水印策略。
- 生成正式合同、授权书或外部审批记录。

这些能力应作为后续生产化扩展项。

## 7. 回归建议

修改申请链路后至少运行：

```powershell
python -m pytest backend\tests\test_applications.py backend\tests\test_standard_demo_flow.py -q
cd frontend
npx playwright test tests/dashboard.spec.ts --project=chromium
```

如果改动涉及权限，还应补跑：

```powershell
python -m pytest backend\tests\test_permissions.py -q
```

## 8. 后续扩展方向

后续可按以下顺序扩展：

1. 区分申请人归属，实现 `application.view_own` 的真实过滤。
2. 增加申请条目级审批意见和交付格式选择。
3. 为三维对象增加表现级交付选择。
4. 为视频来源增加可控交付包策略。
5. 增加审批日志、导出日志和交付包校验信息。

