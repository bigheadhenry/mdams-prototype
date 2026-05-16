from __future__ import annotations

import html
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


PREVIEW_FRAME_COUNT = 24


def _frame_svg(*, title: str, frame_index: int, frame_count: int) -> str:
    angle = (frame_index / max(frame_count, 1)) * math.tau
    width = 640
    height = 360
    cx = width / 2
    cy = height / 2 + 8
    rx = 108 + math.cos(angle) * 36
    ry = 58
    top_rx = max(42, rx * 0.62)
    hue = int((frame_index / max(frame_count, 1)) * 42 + 200)
    escaped_title = html.escape(title[:80])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#f8fafc"/>
      <stop offset="1" stop-color="#e5eef8"/>
    </linearGradient>
    <linearGradient id="body" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="hsl({hue}, 58%, 72%)"/>
      <stop offset="1" stop-color="hsl({hue - 18}, 45%, 46%)"/>
    </linearGradient>
  </defs>
  <rect width="640" height="360" fill="url(#bg)"/>
  <ellipse cx="{cx:.1f}" cy="286" rx="{rx * 1.18:.1f}" ry="20" fill="#cbd5e1" opacity="0.56"/>
  <path d="M {cx - top_rx:.1f} {cy - 98:.1f}
           C {cx - rx:.1f} {cy - 52:.1f}, {cx - rx:.1f} {cy + 78:.1f}, {cx:.1f} {cy + 108:.1f}
           C {cx + rx:.1f} {cy + 78:.1f}, {cx + rx:.1f} {cy - 52:.1f}, {cx + top_rx:.1f} {cy - 98:.1f}
           Z" fill="url(#body)" stroke="#334155" stroke-width="3"/>
  <ellipse cx="{cx:.1f}" cy="{cy - 98:.1f}" rx="{top_rx:.1f}" ry="{ry * 0.42:.1f}" fill="#f8fafc" stroke="#334155" stroke-width="3"/>
  <ellipse cx="{cx:.1f}" cy="{cy + 108:.1f}" rx="{rx * 0.56:.1f}" ry="{ry * 0.30:.1f}" fill="#475569" opacity="0.26"/>
  <path d="M {cx:.1f} {cy - 74:.1f} C {cx + math.sin(angle) * 70:.1f} {cy - 20:.1f}, {cx + math.sin(angle) * 60:.1f} {cy + 42:.1f}, {cx:.1f} {cy + 88:.1f}" fill="none" stroke="#f8fafc" stroke-width="5" opacity="0.38"/>
  <text x="24" y="34" font-family="Arial, sans-serif" font-size="18" fill="#334155">{escaped_title}</text>
  <text x="24" y="58" font-family="Arial, sans-serif" font-size="13" fill="#64748b">auto generated turntable preview · frame {frame_index + 1}/{frame_count}</text>
</svg>"""


def build_three_d_preview_data(
    resource_dir: Path,
    *,
    asset_id: int,
    title: str,
    file_records: Sequence[Mapping[str, Any]],
    frame_count: int = PREVIEW_FRAME_COUNT,
) -> dict[str, Any]:
    """Generate lightweight turntable preview frames for list/card browsing.

    The current prototype does not run a server-side 3D renderer. These frames are
    a deterministic preview contract that can be replaced by real renderer output
    later without changing the frontend payload shape.
    """
    preview_dir = resource_dir / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    safe_title = title or "三维资源"
    frames: list[str] = []
    for index in range(frame_count):
        frame_path = preview_dir / f"turntable-{index:02d}.svg"
        frame_path.write_text(
            _frame_svg(title=safe_title, frame_index=index, frame_count=frame_count),
            encoding="utf-8",
        )
        frames.append(f"/api/three-d/resources/{asset_id}/previews/{frame_path.name}")

    model_file = next((record for record in file_records if str(record.get("role")) == "model"), None)
    preview_data = {
        "kind": "turntable_frames",
        "status": "ready",
        "frame_count": frame_count,
        "poster_url": frames[0] if frames else None,
        "frames": frames,
        "source": "auto_generated_placeholder",
        "note": "Prototype preview frames generated at ingest. Replace with rendered model captures in production.",
        "model_filename": model_file.get("filename") if model_file else None,
    }
    (preview_dir / "preview.json").write_text(json.dumps(preview_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return preview_data
