"""add shared resource events and three d fixity

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-14
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _sha256(path: str) -> str | None:
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_file():
        return None
    digest = hashlib.sha256()
    try:
        with candidate.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def upgrade() -> None:
    op.add_column("three_d_asset_files", sa.Column("sha256", sa.String(), nullable=True))
    op.add_column("three_d_asset_files", sa.Column("fixity_status", sa.String(), server_default="pending", nullable=True))
    op.add_column("three_d_asset_files", sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_three_d_asset_files_sha256", "three_d_asset_files", ["sha256"])
    op.create_index("ix_three_d_asset_files_fixity_status", "three_d_asset_files", ["fixity_status"])

    op.create_table(
        "resource_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_system", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("actor_user_id", sa.String(), nullable=True),
        sa.Column("actor_display_name", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("evidence", sa.String(), nullable=True),
        sa.Column("metadata_info", sa.JSON(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    for name in ("id", "source_system", "source_id", "event_type", "status", "actor_user_id", "occurred_at"):
        op.create_index(f"ix_resource_events_{name}", "resource_events", [name])

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, file_path FROM three_d_asset_files")).mappings()
    for row in rows:
        checksum = _sha256(str(row["file_path"] or ""))
        bind.execute(
            sa.text(
                "UPDATE three_d_asset_files SET sha256=:sha256, fixity_status=:status, "
                "last_verified_at=CASE WHEN :sha256 IS NULL THEN NULL ELSE CURRENT_TIMESTAMP END WHERE id=:id"
            ),
            {"id": row["id"], "sha256": checksum, "status": "verified" if checksum else "missing"},
        )
        if checksum is None:
            asset_state = bind.execute(
                sa.text(
                    "SELECT asset.id, asset.preservation_status FROM three_d_assets AS asset "
                    "JOIN three_d_asset_files AS asset_file ON asset_file.asset_id=asset.id "
                    "WHERE asset_file.id=:id"
                ),
                {"id": row["id"]},
            ).mappings().first()
            if asset_state is not None:
                backup_exists = bind.execute(
                    sa.text(
                        "SELECT 1 FROM resource_events WHERE source_system='three_d' AND source_id=:source_id "
                        "AND evidence='migration:b2c3d4e5f6a7:preservation-backup'"
                    ),
                    {"source_id": str(asset_state["id"])},
                ).first()
                if backup_exists is None:
                    bind.execute(
                        sa.text(
                            "INSERT INTO resource_events "
                            "(source_system, source_id, event_type, status, description, evidence, metadata_info) "
                            "VALUES ('three_d', :source_id, 'preserve', 'needs_review', "
                            "'Migration marked an unreadable file for preservation review', "
                            "'migration:b2c3d4e5f6a7:preservation-backup', CAST(:metadata_info AS JSON))"
                        ),
                        {
                            "source_id": str(asset_state["id"]),
                            "metadata_info": json.dumps(
                                {"previous_preservation_status": asset_state["preservation_status"]}
                            ),
                        },
                    )
            bind.execute(
                sa.text(
                    "UPDATE three_d_assets SET preservation_status='needs_review' "
                    "WHERE id=(SELECT asset_id FROM three_d_asset_files WHERE id=:id)"
                ),
                {"id": row["id"]},
            )

    production_rows = bind.execute(
        sa.text(
            "SELECT id, asset_id, event_type, status, actor, description, evidence, metadata_info, occurred_at "
            "FROM three_d_production_records"
        )
    ).mappings()
    for row in production_rows:
        bind.execute(
            sa.text(
                "INSERT INTO resource_events "
                "(source_system, source_id, event_type, status, actor_display_name, description, evidence, metadata_info, occurred_at) "
                "VALUES ('three_d', :source_id, :event_type, :status, :actor, :description, :evidence, CAST(:metadata_info AS JSON), :occurred_at)"
            ),
            {
                "source_id": str(row["asset_id"]),
                "event_type": row["event_type"],
                "status": row["status"],
                "actor": row["actor"],
                "description": row["description"],
                "evidence": row["evidence"],
                "metadata_info": json.dumps(row["metadata_info"] or {}),
                "occurred_at": row["occurred_at"],
            },
        )

    image_rows = bind.execute(sa.text("SELECT id, status, metadata_info FROM image_records")).mappings()
    for row in image_rows:
        metadata = row["metadata_info"] if isinstance(row["metadata_info"], dict) else {}
        raw = metadata.get("raw_metadata") if isinstance(metadata.get("raw_metadata"), dict) else {}
        audit_trail = raw.get("audit_trail") if isinstance(raw.get("audit_trail"), list) else []
        for entry in audit_trail:
            if not isinstance(entry, dict):
                continue
            action = str(entry.get("action") or "ingest")
            event_type = "bind" if action in {"asset_bound", "asset_replaced"} else "review" if action in {"submitted", "returned"} else "ingest"
            bind.execute(
                sa.text(
                    "INSERT INTO resource_events "
                    "(source_system, source_id, event_type, status, actor_user_id, actor_display_name, description, metadata_info, occurred_at) "
                    "VALUES ('image_record', :source_id, :event_type, :status, :actor_user_id, :actor, :description, CAST(:metadata_info AS JSON), CAST(:occurred_at AS TIMESTAMPTZ))"
                ),
                {
                    "source_id": str(row["id"]),
                    "event_type": event_type,
                    "status": row["status"] or "unknown",
                    "actor_user_id": entry.get("user_id"),
                    "actor": entry.get("actor"),
                    "description": entry.get("note") or action,
                    "metadata_info": json.dumps({"action": action}),
                    "occurred_at": entry.get("at"),
                },
            )


def downgrade() -> None:
    bind = op.get_bind()
    backup_rows = bind.execute(
        sa.text(
            "SELECT source_id, metadata_info FROM resource_events "
            "WHERE source_system='three_d' "
            "AND evidence='migration:b2c3d4e5f6a7:preservation-backup'"
        )
    ).mappings()
    for row in backup_rows:
        metadata = row["metadata_info"] if isinstance(row["metadata_info"], dict) else {}
        if str(row["source_id"]).isdigit():
            bind.execute(
                sa.text(
                    "UPDATE three_d_assets SET preservation_status=:status WHERE id=:asset_id"
                ),
                {
                    "asset_id": int(row["source_id"]),
                    "status": metadata.get("previous_preservation_status"),
                },
            )
    op.drop_table("resource_events")
    op.drop_index("ix_three_d_asset_files_fixity_status", table_name="three_d_asset_files")
    op.drop_index("ix_three_d_asset_files_sha256", table_name="three_d_asset_files")
    op.drop_column("three_d_asset_files", "last_verified_at")
    op.drop_column("three_d_asset_files", "fixity_status")
    op.drop_column("three_d_asset_files", "sha256")
