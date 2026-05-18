# Current Task

## Goal
- 对统一资源目录与统一资源详情进行可视化优化（信息效率导向），提升博物馆方汇报场景下的信息可读性。

## Why Now
- 项目面向博物馆方信息部门与业务管理岗汇报，管理者需要在有限屏幕空间中快速定位资源数量、状态分布和操作入口，而非沉浸式视觉体验。
- 统一资源目录和详情是汇报频次最高的页面，其信息层级和操作效率直接影响演示效果。

## Expected Outputs
1. 目录页卡片 Meta 三层化、排序下拉、筛选 chips、批量操作
2. 检索概览栏三段重组 + 可点击切换 Tab + 可折叠
3. 详情页 Hero 真双栏、操作分主次、面包屑增维度层、生命周期 Timeline、锚点导航
4. 三维源详情 Drawer 拆独立组件 + Tabs + 固定底部栏
5. 主导航 Sider 和检索概览栏默认收起
6. 目录上下文持久化（进详情后返回还原 Tab/页码/排序/筛选）
7. 三维预览动画批量重生成脚本

## Completion Standard
- [x] PlatformDirectory 卡片 Meta 三层化 + 表格主操作 + 排序 + 筛选 chips + 批量入口
- [x] PlatformStatsBar 三段分组（Tab 概览 / 可点击维度分布 / 健康度）+ 可折叠竖排迷你条
- [x] UnifiedResourceDetail 面包屑维度层 + 操作分层 + 双列 Descriptions + 生命周期 Timeline + 锚点 + 嵌套元数据可展开
- [x] ThreeDSourceDetailDrawer 独立组件 + 5 Tab + 底部固定栏 + 自适应宽度
- [x] 主导航 Sider collapsible + 默认收起
- [x] 目录上下文持久化（sessionStorage 六个字段 + isInitialMountRef）
- [x] 移除三维重复预览按钮
- [x] 三维预览动画批量重生成脚本完成，7 个资源全部更新
- [x] `memory/` 实验日志、决策、原型设计记录已同步

## Inputs
- `frontend/src/components/PlatformDirectory.tsx`
- `frontend/src/components/PlatformStatsBar.tsx`
- `frontend/src/components/UnifiedResourceDetail.tsx`
- `frontend/src/components/ThreeDSourceDetailDrawer.tsx`（新增）
- `frontend/src/App.tsx`
- `backend/app/scripts/regenerate_three_d_previews.py`（新增）
- `backend/app/services/three_d_preview.py`

## Status
- Done on 2026-05-17.
- Verification: `npx tsc --noEmit` 通过，`docker compose up -d --build frontend` 通过，前端 http://localhost:3000 返回 200。