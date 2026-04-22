# Current Task

## Goal
- 完成统一平台来源定位契约冻结与跨子系统最小事件边界的基础落地，确认 `source_system/source_id` 为主标准，`resource_id` 仅保留兼容入口。

## Why Now
- 统一目录、统一详情、Mirador AI 和申请车已经完成显式定位收口，现在需要用单独契约页把标准固定下来，避免后续实现漂移。
- 冻结后，`resource_id` 会退到兼容/历史层，后续新增来源可以直接遵循同一标准。
- 跨子系统事件边界已经有 detail / production record / output 层的实现锚点，现在适合用最小词表和 contract tests 把它钉牢。

## Expected Outputs
1. 新增统一平台来源定位契约页
2. 主参考文档指向统一契约页
3. 相关验证和写作记忆同步更新
4. 第二阶段事件边界形成具体推进计划

## Completion Standard
- 统一平台来源定位契约页已建立并被主文档引用
- `source_system/source_id` 是主标准，`resource_id` 仅作为兼容入口
- 跨子系统最小事件边界已具备共享词表和契约测试锚点
- 变更理由、验证结果和写作可复用表述已经写入 `memory/` 和 `tasks/`

## Inputs
- `backend/app/schemas.py`
- `backend/app/platform/image_source.py`
- `backend/app/platform/three_d_source.py`
- `backend/tests/test_platform_directory.py`
- `backend/tests/test_three_d_subsystem.py`
- `frontend/src/types/assets.ts`
- `frontend/src/components/UnifiedResourceDetail.tsx`

## Status
- Done on 2026-04-22 and extended on 2026-04-23.
- Verification: `python3 -m compileall backend/app backend/tests` passed; targeted backend contract tests on event boundary / three_d_production / routes_smoke passed with PostgreSQL-related skips only.

## Next
- 审计剩余历史文档与镜像说明中的术语漂移，再决定是否需要继续批量迁移。
