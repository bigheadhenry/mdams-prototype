# Rights Metadata 字段三层分类

> 基于 MDAMS 当前元数据模型（`metadata_layers.py`），�?Rights 相关字段按「详情页展示」「API 返回」「后台管理」三个层次分类，供检索平台详情页设计参考�?

---

## 一、全量字段清单（当前模型�?

Rights 层定义于 `RIGHTS_FIELDS`�? 字段）：

| 字段 key | 中文含义 | 受控词表 |
|----------|----------|----------|
| `copyright_status` | 版权状�?| 故宫所�?/ 合作共享 / 授权使用 / 捐赠 / 公共领域 / 其他 |
| `copyright_owner` | 版权所�?| �?|
| `access_scope` | 访问范围 | 公开 / 院内 / 部门�?/ 限制访问 |
| `allowed_usage` | 允许用�?| �?|
| `license` | 授权协议 | —（建议关联 CC 协议词表�?|
| `usage_restrictions` | 使用限制 | �?|
| `rights_holder` | 权利持有�?| �?|
| `permission_notes` | 权限说明 | �?|

---

## 二、三层分类明�?

### 🟩 Layer 1 �?详情页展示（Detail Page�?

**原则**：用户查看资源详情时，「必须知道才能合规使用」的信息。放�?`rights` 面板区�?

| 字段 | 展示方式 | 说明 |
|------|----------|------|
| **`rights_statement`** 🆕 | 顶栏声明（单行文本） | 一个计算字段，形如「�?故宫博物�?· 本资源仅限学术用途�?|
| **`license`** | 标签 + 图标（CC / Custom�?| CC 协议直接显示图标+链接，自定义许可显示文本 |
| **`copyright_status`** | 标签（受控词表着色） | ❗当值为 `公共领域` �?`故宫所有` 时影响用户行为，需醒目 |
| **`credit_line`** 🆕 | 署名格式（灰色参考文字） | 例：「故宫博物院资料信息�?· 摄影：张莹」�?用户可直接复�?|
| **`usage_restrictions`** | 可折叠详情文�?| 一句话警告：「不得用于商业用途、不得进�?AI 训练�?|
| **`license_url`** 🆕 | 底部链接（可点击�?| 许可协议全文链接，如 CC BY-NC-SA 4.0 法律文本 |

**�?6 个前台展示元�?*，其�?3 个是已有字段的直接映射，3 个是派生/新增�?

#### 详情页布局示意（rights 面板�?

```
┌─────────────────────────────────────────────────────�?
�?📄 权利信息                                          �?
�?                                                    �?
�? © 故宫博物�?· 本资源仅限非商业用�?                    �?
�?                                                    �?
�? 许可协议  [CC BY-NC-SA 4.0 ⬈]                       �?
�? 版权状�? �?故宫所�?                                 �?
�? 署名要求  故宫博物院资料信息部 · 摄影：张�?             �?
�? 使用限制  不得用于商业用途，不得进行AI训练               �?
�? ───────────────────────────────────────             �?
�? �?许可协议全文  CC BY-NC-SA 4.0 法律文本 �?          �?
└─────────────────────────────────────────────────────�?
```

#### 条件性展�?

| 场景 | 行为 |
|------|------|
| `copyright_status` = "公共领域" | 额外高亮一条「�?本资源属于公共领域，不受版权限制�?|
| `allow_derivatives` 🆕 = false | 自动追加「禁止衍生」警�?|
| `license` 为空，但 `allowed_usage` / `usage_restrictions` 有�?| 用文本描述替�?CC 图标，说明「本资源遵循自定义许可�?|
| `access_scope` �?"公开" | 在面板顶部显示「�?受限资源」，并显示访问范�?|

---

### 🟨 Layer 2 �?API 返回（Internal API Response�?

**原则**：后端详�?API（`/api/assets/{id}/detail`）返�?**全部 Rights 字段**，供前端、客户端集成、IIIF Manifest 等消费�?

前端�?Layer 1 规则渲染；客户端集成（如第三�?API 调用、数据导出）使用完整数据自己做取舍�?

| 字段 | 用�?|
|------|------|
| `copyright_status` | 基础元数�?|
| `copyright_owner` | 基础元数�?|
| `access_scope` | �?API 消费，前端不直接显示，而是控制资源是否可见 |
| `allowed_usage` | API 供第三方集成判断 |
| `license` | API + IIIF Manifest 映射 |
| `usage_restrictions` | API 供第三方集成判断 |
| `rights_holder` | API 供第三方集成 |
| `permission_notes` | API + 管理界面 |

**对于 IIIF Manifest**，在 `metadata` 区块中加�?rights 层字段（当前 `build_iiif_metadata_entries()` 未包�?rights 层——已留意到，如需补充可后续扩展）。IIIF �?`rights` property 应映�?`license_url`，`attribution` 应映�?`credit_line`�?

---

### 🟥 Layer 3 �?后台管理（Backend Admin / Management Console�?

**原则**：只有管理员或授权流程涉及到的内部字段，**不返�?*给普通详情页 API，仅在管理控制台展示�?

这些字段存在于数据库或管理流程中，但不应出现在检索平台的详情页或公开 API 上：

| 字段 | 存在位置 | 说明 |
|------|----------|------|
| `authorization_status` | backend 授权模块 | 授权流程状态（已授�?待审�?已过期），对终端用户无意�?|
| `authorization_type` | backend 授权模块 | 商业授权/学术授权/内部使用，属于管理维�?|
| `authorization_expiry` | backend 授权模块 | 授权到期日期，用户应通过「申请授权」流程而非详情页了�?|
| `price_tier` | backend 订单模块 | 定价层级，不应暴露在公开详情页面 |
| `watermark_required` | backend 下载模块 | 系统行为标志位，控制是否加水�?|
| `rights_clearance_status` | backend 审计模块 | 版权清理状态，内部合规流程�?|
| `rights_notes` | backend 内部备注 | 内部备注文本 |
| `internal_contact` | backend 联系信息 | 权利联系人信息，不直接暴�?|
| `review_status` | backend 审批模块 | 审核状态（待复�?已通过/已驳回） |
| `audit_log` | backend 审计模块 | 历史操作记录 |

> ⚠️ **如果 API 返回这些字段**，必须声明为 `internal: true` 或使�?`admin_only` 标注，前端组件据此决定是否渲染。建议通过独立的管�?API（如 `/api/admin/assets/{id}/rights`）提供，不与公开详情 API 混用�?

---

## 三、新旧字段映射表

| 本设计字�?| 当前模型字段 | 新增/映射 | Layer |
|------------|-------------|-----------|-------|
| `rights_statement` | �?| 🆕 派生字段 | 1 |
| `copyright_status` | `RIGHTS_FIELDS[0]` | 已有 | 1+2 |
| `copyright_owner` | `RIGHTS_FIELDS[1]` | 已有 | 2 |
| `license` | `RIGHTS_FIELDS[4]` | 已有 | 1+2 |
| `license_url` | �?| 🆕 新增字段 | 1+2 |
| `credit_line` | �?| 🆕 派生字段 | 1 |
| `usage_restrictions` | `RIGHTS_FIELDS[5]` | 已有 | 1+2 |
| `allowed_usage` | `RIGHTS_FIELDS[3]` | 已有 | 2 |
| `rights_holder` | `RIGHTS_FIELDS[6]` | 已有 | 2 |
| `access_scope` | `RIGHTS_FIELDS[2]` | 已有 | 2 |
| `permission_notes` | `RIGHTS_FIELDS[7]` | 已有 | 2 |
| `allow_derivatives` | �?| 🆕 建议新增布尔字段 | 1（条件性）|

---

## 四、派生字段计算逻辑

### `rights_statement`

```
格式：「�?{copyright_owner} · {简短用途声明}�?

例：
  copyright_owner="故宫博物�?, allowed_usage="学术研究"
  �?"© 故宫博物�?· 本资源仅供学术研究使�?

  copyright_owner="故宫博物�?, license="CC0"
  �?"© 故宫博物�?· 本资源属于公共领�?
```

### `credit_line`

```
格式：「{著作权人/机构} · 摄影：{photographer}」（�?management 层取 photographer�?

例：
  copyright_owner="故宫博物�?, photographer="张莹"
  �?"故宫博物�?· 摄影：张�?

回退链：copyright_owner �?rights_holder �?"故宫博物�?
```

---

## 五、API 响应结构建议

```json
{
  "rights": {
    "display": {
      "statement": "© 故宫博物�?· 本资源仅供非商业用�?,
      "license": "CC BY-NC-SA 4.0",
      "license_url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
      "copyright_status": "故宫所�?,
      "credit_line": "故宫博物�?· 摄影：张�?,
      "usage_restrictions": "不得用于商业用途，不得进行AI训练",
      "allow_derivatives": false
    },
    "internal": {
      "copyright_owner": "故宫博物�?,
      "rights_holder": "故宫博物院资料信息部",
      "allowed_usage": "学术研究",
      "access_scope": "公开",
      "permission_notes": "该影像为2025年春季拍摄，版权归故宫博物院所�?
    }
  }
}
```

拆分 `display` �?`internal` 两个子对象，前端只需渲染 `rights.display`，无需判断哪些字段该显示�?

---

## 六、实现路�?

### 最小改动（week 1�?

1. �?`RIGHTS_FIELDS` 中新�?`license_url` �?`allow_derivatives` 字段
2. `metadata_layers.py` 中新�?`_build_rights_display()` 辅助函数，生�?`statement` �?`credit_line`
3. `AssetDetailResponse` schema 中新�?`rights_display` 字段
4. 前端详情页新�?`RightsPanel` 组件，渲�?`rights_display`

### 扩展改进（week 2-3�?

5. `build_iiif_metadata_entries()` 中补�?rights 层条目（用于 IIIF Manifest�?
6. 管理后台独立 rights 编辑页面（写�?`metadata` 中的 rights 块）
7. 详情页增强：CC 图标、可折叠协议全文、下载确认弹�?

---

## 七、参考标准映�?

| MDAMS 字段 | Dublin Core | IIIF Presentation 3 | Europeana |
|------------|-------------|---------------------|-----------|
| `rights_statement` | `dc:rights` | �?| `edm:rights` |
| `license` | `dcterms:license` | `rights` (URL) | `cc:license` |
| `credit_line` | �?| `requiredStatement` | `cc:attributionName` |
| `copyright_status` | �?| �?| �?|
| `usage_restrictions` | `dcterms:accessRights` | �?| �?|
| `access_scope` | `dcterms:accessRights` | �?| �?|
