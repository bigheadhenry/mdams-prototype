# 图像记录工作台说明

- 最后核对日期：2026-04-06
- 核对范围：`backend/app/routers/image_records.py`、`backend/app/services/image_record_validation.py`、`frontend/src/components/ImageRecordWorkbench.tsx`

## 1. 目标

本文件用于说明当前图像记录工作台的角色分工、页面职责和工作流边界。

## 2. 工作台定位

图像记录工作台当前用于承接“先建记录、后传文件”的拆分工作流。

它服务的不是单一角色，而是两类不同用户：

- 元数据录入人员
- 摄影上传人员

## 3. 当前服务角色

### 3.1 `image_metadata_entry`

当前负责：

- 创建图像记录
- 编辑结构化信息
- 提交记录
- 退回后继续修改

### 3.2 `image_photographer_upload`

当前负责：

- 查看已分配的待上传记录
- 上传文件
- 将文件绑定到指定图像记录
- 执行替换上传

### 3.3 `system_admin`

当前可作为全量调试和演示角色进入该工作台。

## 4. 当前入口条件

前端当前把以下权限视为图像记录工作台入口条件：

- `image.record.list`
- `image.record.view_ready_for_upload`

因此：

- 元数据录入人员能进入
- 摄影上传人员能进入
- 普通浏览用户不能进入

## 5. 当前工作流拆分

### 5.1 记录创建阶段

元数据录入人员创建图像记录，并填写：

- 标题
- profile
- 可见范围
- 关联对象
- 业务字段

### 5.2 提交阶段

记录录入完成后可提交，进入下一阶段。

### 5.3 待上传阶段

摄影上传人员可查看自己被分配的记录池。

### 5.4 文件绑定阶段

摄影上传人员上传文件，系统进行：

- 文件基础分析
- 扩展名规则判断
- 基础元数据读取
- 重复检测

然后由用户显式确认绑定。

### 5.5 替换阶段

已经有文件的记录仍可进入替换上传流程。

## 6. 当前实现特点

当前工作台有以下几个实现特点：

- 记录和文件被拆成两个对象协作
- 上传不是自动吞并，而是显式确认绑定
- 绑定后会继续进入验证与 IIIF access 相关流程
- 摄影上传人员看到的是自己的任务池，而不是全部记录

## 7. 当前边界

当前工作台已经能承接 Phase 1 骨架，但仍有边界：

- 更复杂的指派机制还没有完全产品化
- 更细的状态机仍可继续增强
- 批量操作和高级审核能力仍可继续补

## 8. 关联文档

- `WORKFLOW_GUIDE.md`
- `USER_ROLE_PERMISSION_MATRIX.md`
- `../04-实施方案/IMAGE_RECORD_ROLE_SPLIT_PHASE1_PLAN.md`
- `../04-实施方案/IMAGE_RECORD_MATCHING_PHASE1_PLAN.md`
- `../04-实施方案/IMAGE_RECORD_VALIDATION_PHASE1_PLAN.md`
