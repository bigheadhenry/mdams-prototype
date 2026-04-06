# 测试策略

- 最后核对日期：2026-04-06
- 核对范围：`backend/tests/`、`frontend/tests/`、`frontend/package.json`、`pytest.ini`

## 1. 目标

本项目采用分层测试策略，目标不是只保留少量“大而全”的端到端用例，而是让问题能够尽量在最接近根因的层级暴露。

核心原则：

- 新功能至少补一个契约测试或集成测试
- 缺陷修复必须补回归测试
- smoke 测试保持小而稳定
- 前端回归重点覆盖登录态、菜单可见性和关键流程入口

## 2. 当前测试分层

### 2.1 后端

后端当前适合按以下层次理解：

- 单元测试：纯逻辑、规则、字典、元数据分层
- 契约测试：schema、响应结构、字段约束
- 集成测试：路由 + 数据库 + 文件系统行为
- smoke 测试：关键 happy path
- 子系统测试：跨多个服务函数和路由的业务链路

### 2.2 前端

前端当前主要采用：

- `eslint` 静态检查
- `vite build` 构建检查
- Playwright 回归测试

Playwright 当前重点覆盖：

- 登录态初始化
- 菜单可见性
- 统一平台目录与统一详情
- 图像记录工作台
- 不同角色下的页面入口差异

## 3. 当前测试文件分布

### 3.1 后端测试

当前后端主要测试文件包括：

- `test_health.py`
- `test_config.py`
- `test_auth_service.py`
- `test_permissions.py`
- `test_asset_visibility.py`
- `test_derivative_policy.py`
- `test_metadata_layers.py`
- `test_ingest.py`
- `test_image_records.py`
- `test_applications.py`
- `test_platform_directory.py`
- `test_reference_import.py`
- `test_preview_images.py`
- `test_iiif_access_phase1.py`
- `test_routes_smoke.py`
- `test_three_d_dictionary.py`
- `test_three_d_production.py`
- `test_three_d_subsystem.py`
- `test_ai_mirador.py`

### 3.2 前端测试

当前前端主要测试文件包括：

- `dashboard.spec.ts`
- `mirador-ai.spec.ts`

## 4. 推荐执行顺序

建议日常开发按以下顺序执行：

1. 后端 `pytest`
2. 前端 `npm run lint`
3. 前端 `npm run build`
4. 前端 `npm run test`

如果只是改了文档，不需要跑完整测试。

如果改了下列内容，建议补跑对应测试：

- 改权限、角色、菜单：后端权限测试 + 前端 Playwright
- 改统一平台：`test_platform_directory.py` + Playwright 目录相关用例
- 改图像记录：`test_image_records.py` + Playwright 工作台用例
- 改三维子系统：三维相关 pytest
- 改配置和启动路径：`test_config.py`、`test_health.py`、`test_routes_smoke.py`

## 5. 常用命令

### 5.1 后端

```powershell
cd backend
python -m pytest
```

如需只跑单个测试文件：

```powershell
cd backend
python -m pytest tests/test_image_records.py
```

### 5.2 前端

```powershell
cd frontend
npm run lint
npm run build
npm run test
```

如需只跑 Playwright 某个用例文件：

```powershell
cd frontend
npx playwright test tests/dashboard.spec.ts
```

## 6. 当前策略重点

当前测试策略最重视以下区域：

- 配置是否可启动
- 健康检查与 readiness
- 权限与资源可见范围
- 图像记录拆分工作流
- 统一平台资源聚合
- 三维资源对象与生产链路
- Mirador / AI 面板相关基础行为

## 7. 新增测试的建议规则

### 7.1 新功能

新增功能时，至少应满足以下其一：

- 新增 1 个契约测试
- 新增 1 个集成测试
- 如果功能跨页面或跨模块，再补 1 个 Playwright 回归

### 7.2 缺陷修复

缺陷修复时，优先在最窄层补测试：

- 纯规则错误：补单元测试
- 返回结构错误：补契约测试
- 路由行为错误：补集成测试
- 角色入口错误：补 Playwright

### 7.3 避免的问题

应避免：

- 所有行为都塞进单个超大端到端用例
- 只做 happy path 不做失败路径
- 前端改了菜单和入口，但没有角色回归
- 权限改了后只改前端，不补后端测试

## 8. 后续增强方向

后续建议继续补强：

- 更清晰的测试标签或目录分层
- 统一平台多来源适配器测试
- 申请审批与导出异常路径测试
- 更多三维上传类型覆盖
- 文档与测试命令同步校验

## 9. 完成标准

当前阶段文档与测试策略保持一致的最低标准应是：

- 关键后端模块均有 pytest 覆盖
- 关键前端入口至少有基础 Playwright 回归
- 角色、菜单、统一平台、图像记录、三维链路均有对应测试
- 文档中列出的命令可以直接执行
