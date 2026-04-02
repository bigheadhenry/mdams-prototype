from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def _write_markdown_report(output_path: Path, rows: list[dict[str, object]]) -> None:
    lines = [
        "# Reference Resource Completeness Report",
        "",
        f"- Total candidates: {len(rows)}",
        "",
        "## Average By Profile",
        "",
    ]

    grouped: dict[str, list[float]] = {}
    for row in rows:
        grouped.setdefault(str(row["profile_key"]), []).append(float(row["ratio"]))
    for profile_key, values in sorted(grouped.items()):
        average = sum(values) / len(values)
        lines.append(f"- `{profile_key}`: {average:.3f}")

    missing_counter = Counter(field for row in rows for field in row.get("missing", []))
    lines.extend(["", "## Most Missing Fields", ""])
    if missing_counter:
        for field, count in missing_counter.most_common():
            lines.append(f"- `{field}`: {count}")
    else:
        lines.append("- none")

    lines.extend(["", "## Candidates", ""])
    for row in rows:
        lines.append(f"- `{row['relative_dir']}`")
        lines.append(f"  title: {row['title']}")
        lines.append(f"  profile: {row['profile_key']}")
        lines.append(f"  completeness: {row['filled']}/{row['expected']} ({row['ratio']:.3f})")
        lines.append(f"  missing: {', '.join(row['missing']) if row['missing'] else 'none'}")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a metadata completeness report for reference resource manifests.")
    parser.add_argument("--source-root", required=True, help="Root folder of the reference resource package.")
    parser.add_argument("--output-dir", required=True, help="Directory to write the completeness report into.")
    parser.add_argument("--visibility-scope", default="open", choices=["open", "owner_only"], help="Visibility scope to embed while evaluating manifests.")
    args = parser.parse_args()

    backend_root = Path(__file__).resolve().parents[1]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    from app.services.reference_import import assess_manifest_completeness, collect_reference_candidates

    source_root = Path(args.source_root).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    candidates = collect_reference_candidates(source_root, visibility_scope=args.visibility_scope)
    for candidate in candidates:
        row = assess_manifest_completeness(candidate.manifest)
        row["relative_dir"] = str(candidate.source_dir.relative_to(source_root))
        row["title"] = candidate.title
        rows.append(row)

    json_path = output_dir / "completeness-report.json"
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path = output_dir / "completeness-report.md"
    _write_markdown_report(md_path, rows)

    print(f"Completeness report JSON: {json_path}")
    print(f"Completeness report Markdown: {md_path}")


if __name__ == "__main__":
    main()
