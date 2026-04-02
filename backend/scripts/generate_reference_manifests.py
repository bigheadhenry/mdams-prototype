from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path


def _write_quality_report(output_dir: Path, plan: list[dict[str, object]]) -> Path:
    counter = Counter()
    lines = [
        "# Reference Resource Quality Report",
        "",
        f"- Total candidates: {len(plan)}",
        "",
        "## By Profile",
        "",
    ]

    profile_counter = Counter(str(item.get("profile_key") or "unknown") for item in plan)
    for profile_key, count in sorted(profile_counter.items()):
        lines.append(f"- `{profile_key}`: {count}")

    lines.extend(["", "## Quality Flags", ""])
    for item in plan:
        for flag in item.get("quality_flags") or []:
            counter[str(flag)] += 1

    if counter:
        for flag, count in sorted(counter.items()):
            lines.append(f"- {flag}: {count}")
    else:
        lines.append("- none")

    lines.extend(["", "## Candidates", ""])
    for item in plan:
        lines.append(f"- `{item['relative_dir']}`")
        lines.append(f"  title: {item['title']}")
        lines.append(f"  profile: {item['profile_key']}")
        lines.append(f"  manifest: {item['manifest_path']}")
        flags = item.get("quality_flags") or []
        warnings = item.get("warnings") or []
        lines.append(f"  quality_flags: {', '.join(flags) if flags else 'none'}")
        lines.append(f"  warnings: {', '.join(warnings) if warnings else 'none'}")

    report_path = output_dir / "quality-report.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SIP-ready manifests from reference resource packages.")
    parser.add_argument("--source-root", required=True, help="Root folder of the reference resource package.")
    parser.add_argument("--output-dir", required=True, help="Directory to write generated manifests into.")
    parser.add_argument("--visibility-scope", default="open", choices=["open", "owner_only"], help="Visibility scope to embed into generated metadata.")
    parser.add_argument("--limit", type=int, default=0, help="Optional limit on generated candidate count.")
    parser.add_argument("--stage-files", action="store_true", help="Copy the selected primary image into the output directory beside its manifest.")
    args = parser.parse_args()

    backend_root = Path(__file__).resolve().parents[1]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    from app.services.reference_import import collect_reference_candidates

    source_root = Path(args.source_root).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    candidates = collect_reference_candidates(
        source_root,
        visibility_scope=args.visibility_scope,
        limit=args.limit or None,
    )

    plan: list[dict[str, object]] = []
    for candidate in candidates:
        relative_dir = candidate.source_dir.relative_to(source_root)
        target_dir = output_dir / relative_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = target_dir / f"{candidate.primary_image.name}.manifest.json"
        manifest_path.write_text(
            json.dumps(candidate.manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        staged_image_path = None
        if args.stage_files:
            staged_image_path = target_dir / candidate.primary_image.name
            shutil.copy2(candidate.primary_image, staged_image_path)

        plan.append(
            {
                "relative_dir": str(relative_dir),
                "title": candidate.title,
                "profile_key": candidate.profile_key,
                "source_image": str(candidate.primary_image),
                "staged_image": str(staged_image_path) if staged_image_path else None,
                "manifest_path": str(manifest_path),
                "warnings": list(candidate.warnings),
                "quality_flags": list(candidate.quality_flags),
            }
        )

    summary_path = output_dir / "import-plan.json"
    summary_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    quality_report_path = _write_quality_report(output_dir, plan)

    print(f"Generated {len(plan)} manifest files")
    print(f"Summary: {summary_path}")
    print(f"Quality report: {quality_report_path}")


if __name__ == "__main__":
    main()
