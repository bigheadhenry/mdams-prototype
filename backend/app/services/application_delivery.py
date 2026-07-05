import json
import os
import shutil
import tempfile
import zipfile

from fastapi import HTTPException

from ..models import Application


def _build_authorization_notice(application: Application) -> str:
    """Build the authorization notice/使用说明 for the delivery package."""
    items_summary = []
    for idx, item in enumerate(application.items, 1):
        asset = item.asset
        title = item.resource_title or (asset.filename if asset else "未命名资源")
        obj_no = item.object_number or ""
        items_summary.append(f"  {idx}. {title}" + (f"（文物编号：{obj_no}）" if obj_no else ""))

    return f"""# 数字资源授权使用说明

## 授权信息

- **授权编号**：{application.application_no}
- **申请人**：{application.requester_name}
- **所属机构**：{application.requester_org or "未提供"}
- **联系邮箱**：{application.contact_email or "未提供"}
- **获批用途**：{application.purpose}
- **使用范围**：{application.usage_scope or "未限定"}
- **审批意见**：{application.review_note or "无"}
- **审批日期**：{application.reviewed_at.strftime("%Y-%m-%d %H:%M") if application.reviewed_at else "未记录"}
- **有效期限**：自审批通过之日起计算，仅限获批用途单次使用。如需延期或变更用途，请重新提交申请。
- **授权方式**：非独占性、不可转让的内部使用授权

## 授权资源清单

{chr(10).join(items_summary) if items_summary else "  （无具体资源条目）"}

## 使用要求

1. **署名要求**：使用本院数字资源时，须在出版物、展览或相关成果中标注"故宫博物院"为资源提供方。
2. **使用限制**：
   - 不得将资源转授权、转售或提供给第三方使用。
   - 不得超出获批用途和使用范围使用资源。
   - 不得对资源进行歪曲、篡改或误导性使用。
3. **成果回传**：使用本院资源产生的出版物、展览图录或数字产品，建议向本院数字与信息部备案一份。
4. **版权归属**：资源版权归故宫博物院所有。本授权不转移任何版权或所有权。

## 注意事项

- 本授权说明随交付包一同提供，请妥善保管。
- 如发现资源文件损坏或与申请内容不符，请联系本院数字与信息部。
- 本院保留对授权使用情况进行追溯和核查的权利。

---

*本文件由 MDAMS 系统自动生成，仅供内部使用。*
"""


def build_application_export_package(application: Application) -> tuple[str, str, str]:
    temp_dir = tempfile.mkdtemp()
    package_root = os.path.join(temp_dir, f"{application.application_no}")
    data_dir = os.path.join(package_root, "data")
    os.makedirs(data_dir, exist_ok=True)

    manifest_items = []
    for item in application.items:
        asset = item.asset
        if asset is None:
            manifest_items.append(
                {
                    "application_item_id": item.id,
                    "asset_id": None,
                    "source_system": item.source_system,
                    "source_id": item.source_id,
                    "resource_type": item.resource_type,
                    "resource_title": item.resource_title,
                    "manifest_url": item.manifest_url,
                    "source_label": item.source_label,
                    "object_number": item.object_number,
                    "requested_variant": item.requested_variant,
                    "delivery_format": item.delivery_format,
                    "note": item.note,
                    "delivery_note": "This unified resource is recorded for review; no local 2D asset file was attached to this export package.",
                }
            )
            continue

        if not asset.file_path or not os.path.exists(asset.file_path):
            raise HTTPException(status_code=404, detail=f"Physical file missing for asset {asset.id}")

        actual_filename = os.path.basename(asset.file_path)
        safe_name = f"{asset.id}_{actual_filename}"
        export_path = os.path.join(data_dir, safe_name)
        shutil.copy2(asset.file_path, export_path)
        manifest_items.append(
            {
                "application_item_id": item.id,
                "asset_id": asset.id,
                "source_system": item.source_system or "image_2d",
                "source_id": item.source_id or str(asset.id),
                "resource_type": item.resource_type or asset.resource_type,
                "resource_title": item.resource_title or asset.filename,
                "manifest_url": item.manifest_url,
                "source_label": item.source_label,
                "object_number": item.object_number,
                "filename": asset.filename,
                "actual_filename": actual_filename,
                "export_filename": safe_name,
                "requested_variant": item.requested_variant,
                "delivery_format": item.delivery_format,
                "note": item.note,
            }
        )

    # Write application metadata
    with open(os.path.join(package_root, "application.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "application_no": application.application_no,
                "requester_name": application.requester_name,
                "requester_org": application.requester_org,
                "contact_email": application.contact_email,
                "purpose": application.purpose,
                "usage_scope": application.usage_scope,
                "status": application.status,
                "review_note": application.review_note,
                "reviewed_at": application.reviewed_at.isoformat() if application.reviewed_at else None,
                "items": manifest_items,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    # Write authorization notice
    notice = _build_authorization_notice(application)
    with open(os.path.join(package_root, "授权说明.md"), "w", encoding="utf-8") as f:
        f.write(notice)

    # Write brief README
    with open(os.path.join(package_root, "README.txt"), "w", encoding="utf-8") as f:
        f.write(
            f"Application No: {application.application_no}\n"
            f"本交付包包含批准交付的数字资源文件及授权说明。\n"
            f"详细授权条款请参阅「授权说明.md」。\n"
        )

    # Create ZIP
    zip_path = os.path.join(temp_dir, f"{application.application_no}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(package_root):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)

    return temp_dir, zip_path, f"{application.application_no}.zip"
