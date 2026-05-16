"""Update the metrics table in README.md from a gold eval JSON report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

START = "<!-- metrics:start -->"
END = "<!-- metrics:end -->"


def main() -> int:
    parser = argparse.ArgumentParser(description="Update README metrics table")
    parser.add_argument("--report", type=Path, default=Path("reports/gold_eval_latest.json"))
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    args = parser.parse_args()

    report = json.loads(args.report.read_text(encoding="utf-8"))
    readme = args.readme.read_text(encoding="utf-8")
    table = _render_table(report)

    if START not in readme or END not in readme:
        raise RuntimeError("README is missing metrics markers")
    before, rest = readme.split(START, 1)
    _, after = rest.split(END, 1)
    args.readme.write_text(f"{before}{START}\n{table}\n{END}{after}", encoding="utf-8")
    return 0


def _render_table(report: dict[str, Any]) -> str:
    metrics = report.get("metrics", {})
    secondary = report.get("secondary_metrics", {})
    generated_at = report.get("last_refreshed") or report.get("generated_at") or "unknown"
    rows = [
        ("M1 extraction F1", metrics.get("extraction_f1"), "0.85"),
        ("Inflection recall", metrics.get("inflection_recall"), "0.80"),
        ("Current-state accuracy", metrics.get("current_state_accuracy"), "0.75"),
        ("Stance F1", metrics.get("stance_f1"), "0.75"),
        ("Cost per claim, cold", metrics.get("cost_per_claim_cold"), "No public target"),
    ]
    lines = [
        f"Last refreshed: `{generated_at}`",
        "",
        "| Metric | Current | Target | Status |",
        "| --- | ---: | ---: | --- |",
    ]
    for name, metric, target in rows:
        metric = metric or {}
        lines.append(
            f"| {name} | {_format_metric(metric)} | {target} | {metric.get('status', 'unavailable')} |"
        )
    lines.extend([
        "",
        f"Claims evaluated: `{secondary.get('claims_evaluated', '-')}` · "
        f"Inflection precision: `{_format_ratio(secondary.get('inflection_precision'))}` · "
        f"Avg papers per claim: `{secondary.get('avg_papers_per_claim', '-')}`",
    ])
    return "\n".join(lines)


def _format_metric(metric: dict[str, Any]) -> str:
    value = metric.get("value")
    if value is None:
        return "-"
    if metric.get("unit") == "usd":
        return f"${float(value):.4f}"
    return _format_ratio(float(value))


def _format_ratio(value: Any) -> str:
    if value is None:
        return "-"
    return f"{float(value):.0%}"


if __name__ == "__main__":
    raise SystemExit(main())
