"""add three d digital objects and representation fields

Revision ID: a1b2c3d4e5f6
Revises: f5a6b7c8d9e0
Create Date: 2026-07-11
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "f5a6b7c8d9e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


REPRESENTATION_TYPES = (
    "original_master",
    "web_display",
    "mobile_lightweight",
    "research_detail",
    "derivative",
)
PUBLICATION_STATUSES = (
    "draft",
    "validating",
    "approved",
    "published",
    "withdrawn",
    "rejected",
)


def _metadata_value(metadata: Any, key: str) -> Any:
    if not isinstance(metadata, dict):
        return None
    if metadata.get(key) not in (None, ""):
        return metadata[key]
    for section_name in ("core", "management", "profile", "raw_metadata"):
        section = metadata.get(section_name)
        if not isinstance(section, dict):
            continue
        if section.get(key) not in (None, ""):
            return section[key]
        fields = section.get("fields")
        if isinstance(fields, dict) and fields.get(key) not in (None, ""):
            return fields[key]
    return None


def _infer_representation_type(row: Any) -> str:
    explicit = str(_metadata_value(row.metadata_info, "representation_type") or "").strip().lower()
    if explicit in REPRESENTATION_TYPES:
        return explicit
    version = str(row.version_label or "").lower()
    if "original" in version or "master" in version:
        return "original_master"
    if "mobile" in version or "light" in version:
        return "mobile_lightweight"
    if "detail" in version or "research" in version or "high" in version:
        return "research_detail"
    if "web" in version or bool(row.is_web_preview and row.web_preview_status == "ready"):
        return "web_display"
    return "derivative"


def upgrade() -> None:
    op.create_table(
        "three_d_digital_objects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("object_key", sa.String(), nullable=False),
        sa.Column("collection_object_id", sa.Integer(), nullable=True),
        sa.Column("legacy_resource_group", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("project_code", sa.String(), nullable=True),
        sa.Column("capture_batch", sa.String(), nullable=True),
        sa.Column("responsible_department", sa.String(), nullable=True),
        sa.Column("lifecycle_status", sa.String(), server_default="draft", nullable=False),
        sa.Column("metadata_info", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(
            ["collection_object_id"],
            ["three_d_collection_objects.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_three_d_digital_objects_id", "three_d_digital_objects", ["id"])
    op.create_index("ix_three_d_digital_objects_object_key", "three_d_digital_objects", ["object_key"], unique=True)
    op.create_index("ix_three_d_digital_objects_collection_object_id", "three_d_digital_objects", ["collection_object_id"])
    op.create_index("ix_three_d_digital_objects_legacy_resource_group", "three_d_digital_objects", ["legacy_resource_group"])
    op.create_index("ix_three_d_digital_objects_title", "three_d_digital_objects", ["title"])
    op.create_index("ix_three_d_digital_objects_project_code", "three_d_digital_objects", ["project_code"])
    op.create_index("ix_three_d_digital_objects_capture_batch", "three_d_digital_objects", ["capture_batch"])
    op.create_index("ix_three_d_digital_objects_responsible_department", "three_d_digital_objects", ["responsible_department"])
    op.create_index("ix_three_d_digital_objects_lifecycle_status", "three_d_digital_objects", ["lifecycle_status"])

    op.add_column("three_d_assets", sa.Column("three_d_object_id", sa.Integer(), nullable=True))
    op.add_column("three_d_assets", sa.Column("representation_type", sa.String(), nullable=True))
    op.add_column("three_d_assets", sa.Column("publication_status", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_three_d_assets_three_d_object_id",
        "three_d_assets",
        "three_d_digital_objects",
        ["three_d_object_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_three_d_assets_three_d_object_id", "three_d_assets", ["three_d_object_id"])
    op.create_index("ix_three_d_assets_representation_type", "three_d_assets", ["representation_type"])
    op.create_index("ix_three_d_assets_publication_status", "three_d_assets", ["publication_status"])

    bind = op.get_bind()
    assets = sa.table(
        "three_d_assets",
        sa.column("id", sa.Integer()),
        sa.column("collection_object_id", sa.Integer()),
        sa.column("resource_group", sa.String()),
        sa.column("filename", sa.String()),
        sa.column("metadata_info", sa.JSON()),
        sa.column("version_label", sa.String()),
        sa.column("is_web_preview", sa.Boolean()),
        sa.column("web_preview_status", sa.String()),
        sa.column("status", sa.String()),
        sa.column("three_d_object_id", sa.Integer()),
        sa.column("representation_type", sa.String()),
        sa.column("publication_status", sa.String()),
    )
    digital_objects = sa.table(
        "three_d_digital_objects",
        sa.column("id", sa.Integer()),
        sa.column("object_key", sa.String()),
        sa.column("collection_object_id", sa.Integer()),
        sa.column("legacy_resource_group", sa.String()),
        sa.column("title", sa.String()),
        sa.column("lifecycle_status", sa.String()),
        sa.column("metadata_info", sa.JSON()),
    )

    object_ids: dict[tuple[int | None, str], int] = {}
    rows = bind.execute(sa.select(assets)).mappings().all()
    for row in rows:
        group = str(row.resource_group or "").strip() or f"asset-{row.id}"
        grouping_key = (row.collection_object_id, group)
        object_id = object_ids.get(grouping_key)
        if object_id is None:
            object_key = f"collection:{row.collection_object_id if row.collection_object_id is not None else 'none'}:group:{group}"
            title = str(_metadata_value(row.metadata_info, "title") or group or row.filename or f"3D Object {row.id}")
            result = bind.execute(
                digital_objects.insert().values(
                    object_key=object_key,
                    collection_object_id=row.collection_object_id,
                    legacy_resource_group=group,
                    title=title,
                    lifecycle_status="draft",
                    metadata_info={"migrated_from": "resource_group"},
                ).returning(digital_objects.c.id)
            )
            object_id = int(result.scalar_one())
            object_ids[grouping_key] = object_id

        preview_ready = bool(
            row.is_web_preview and row.web_preview_status == "ready" and row.status == "ready"
        )
        bind.execute(
            assets.update()
            .where(assets.c.id == row.id)
            .values(
                three_d_object_id=object_id,
                representation_type=_infer_representation_type(row),
                publication_status="published" if preview_ready else "draft",
            )
        )

    op.alter_column("three_d_assets", "three_d_object_id", nullable=False)
    op.alter_column("three_d_assets", "representation_type", nullable=False, server_default="derivative")
    op.alter_column("three_d_assets", "publication_status", nullable=False, server_default="draft")
    op.create_check_constraint(
        "ck_three_d_assets_representation_type",
        "three_d_assets",
        f"representation_type IN {REPRESENTATION_TYPES}",
    )
    op.create_check_constraint(
        "ck_three_d_assets_publication_status",
        "three_d_assets",
        f"publication_status IN {PUBLICATION_STATUSES}",
    )


def downgrade() -> None:
    op.drop_constraint("ck_three_d_assets_publication_status", "three_d_assets", type_="check")
    op.drop_constraint("ck_three_d_assets_representation_type", "three_d_assets", type_="check")
    op.drop_index("ix_three_d_assets_publication_status", table_name="three_d_assets")
    op.drop_index("ix_three_d_assets_representation_type", table_name="three_d_assets")
    op.drop_index("ix_three_d_assets_three_d_object_id", table_name="three_d_assets")
    op.drop_constraint("fk_three_d_assets_three_d_object_id", "three_d_assets", type_="foreignkey")
    op.drop_column("three_d_assets", "publication_status")
    op.drop_column("three_d_assets", "representation_type")
    op.drop_column("three_d_assets", "three_d_object_id")
    op.drop_table("three_d_digital_objects")
