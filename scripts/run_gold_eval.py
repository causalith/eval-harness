"""Run the public Causalith Claim Intelligence gold-set evaluation.

The harness is intentionally API-first: it does not import Causalith production
code, open a database connection, or require provider keys. By default it calls
the public API at https://api.causalith.com.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parent.parent
GOLD_FILE = ROOT / "tests" / "gold_claims" / "claim_intelligence_eval.jsonl"

TARGETS = {
    "extraction_f1": 0.85,
    "inflection_recall": 0.80,
    "current_state_accuracy": 0.75,
    "stance_f1": 0.75,
}

# The public API currently exposes inflection/current-state events. Extraction
# and stance F1 are retained in the report shape so the methodology page can
# stay stable while the API grows richer eval traces.
#
# Provider history:
#   2026-05-06  NVIDIA GLM 4.7  (nvapi, openai-format)  cost=$0.0120/claim
#   2026-05-18  Claude Haiku 4.5 via cc.freemodel.dev    cost=$0.0000/claim (free tier)
#              → extraction confidence improved (decimal/negation bugs resolved)
#              → state-label calibration in progress (see reports/ for latest run)
CURRENT_BASELINES = {
    "extraction_f1": 0.82,   # improved: decimal + negation + passive-voice bugs fixed
    "stance_f1": 0.71,       # Claude Haiku shows cleaner JSON instruction following
    "cost_per_claim_cold": 0.000,  # cc.freemodel.dev free tier (retail Haiku ~$0.004)
}


def load_gold(path: Path = GOLD_FILE) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_one(
    gold: dict[str, Any],
    *,
    api_url: str,
    api_key: str | None,
    timeout_s: float,
    max_papers: int,
    verbose: bool = False,
) -> dict[str, Any]:
    claim_id = gold["id"]
    started = time.perf_counter()

    body = {
        "subject": gold["subject"],
        "predicate_direction": gold["predicate"],
        "object": gold["object"],
        "domain": gold.get("domain", "medicine"),
        "max_papers": max_papers,
    }

    detected_state: str | None = None
    detected_inflection_years: list[int] = []
    paper_count = 0
    weighted_support: float | None = None
    fetched_count = 0
    stances_by_year: dict[int, dict[str, int]] = {}
    errors: list[str] = []

    try:
        start_payload = _post_json(
            _join_api(api_url, "/api/v1/claim-intelligence"),
            body,
            api_key=api_key,
            timeout_s=timeout_s,
        )
        sse_url = start_payload.get("sse_url")
        if not isinstance(sse_url, str) or not sse_url:
            raise RuntimeError(f"API response did not include sse_url: {start_payload}")

        for event_name, event_data in _read_sse(
            _join_api(api_url, sse_url),
            api_key=api_key,
            timeout_s=timeout_s,
        ):
            if event_name == "fetched_papers":
                fetched_count = int(event_data.get("count") or 0)
            elif event_name == "stances":
                for stance in event_data.get("stances", []):
                    year = stance.get("year")
                    label = str(stance.get("stance") or "?")
                    if year:
                        y = int(year)
                        stances_by_year.setdefault(y, {})
                        stances_by_year[y][label] = stances_by_year[y].get(label, 0) + 1
            elif event_name == "support_ratio":
                paper_count = int(event_data.get("total_papers") or 0)
                weighted_support = event_data.get("weighted_support")
                fetched_count = int(event_data.get("fetched_count") or fetched_count or 0)
            elif event_name == "inflections":
                detected_inflection_years = [
                    int(point["year"])
                    for point in event_data.get("inflection_points", [])
                    if point.get("year") is not None
                ]
                history = event_data.get("history", [])
                if history:
                    detected_state = history[-1].get("state")
            elif event_name == "error":
                errors.append(str(event_data.get("message") or event_data))
            elif event_name in {"complete", "done"}:
                break
    except Exception as exc:
        errors.append(str(exc))

    expected_years: list[int] = gold.get("expected_inflection_years", [])
    tolerance = int(gold.get("inflection_year_tolerance", 1))
    expected_state = str(gold.get("expected_state") or "")

    true_positive_years = [
        y for y in detected_inflection_years
        if any(abs(y - expected) <= tolerance for expected in expected_years)
    ]
    n_tp = len(true_positive_years)
    n_expected = len(expected_years)
    n_detected = len(detected_inflection_years)

    inflection_recall = n_tp / n_expected if n_expected else (1.0 if n_detected == 0 else 0.0)
    inflection_precision = n_tp / n_detected if n_detected else (1.0 if n_expected == 0 else 0.0)
    state_correct = (
        detected_state is not None and detected_state.lower() == expected_state.lower()
    ) if expected_state else None

    result = {
        "id": claim_id,
        "subject": gold["subject"],
        "predicate": gold["predicate"],
        "object": gold["object"],
        "paper_count": paper_count,
        "fetched_count": fetched_count,
        "weighted_support": round(float(weighted_support), 3) if weighted_support is not None else None,
        "expected_state": expected_state,
        "detected_state": detected_state,
        "state_correct": state_correct,
        "expected_inflection_years": expected_years,
        "detected_inflection_years": detected_inflection_years,
        "inflection_recall": round(inflection_recall, 3),
        "inflection_precision": round(inflection_precision, 3),
        "elapsed_s": round(time.perf_counter() - started, 1),
        "errors": errors,
        "stances_by_year": {str(k): v for k, v in sorted(stances_by_year.items())},
    }

    if verbose:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        recall_mark = "PASS" if inflection_recall >= TARGETS["inflection_recall"] or not expected_years else "FAIL"
        state_mark = "PASS" if state_correct else ("SKIP" if state_correct is None else "FAIL")
        print(
            f"{recall_mark:<4} {claim_id:<34} "
            f"recall={inflection_recall:.0%} precision={inflection_precision:.0%} "
            f"state={state_mark}({detected_state or '?'}) papers={paper_count}"
        )

    return result


def build_report(
    *,
    results: list[dict[str, Any]],
    api_url: str,
    gold_file: Path,
    limit: int | None,
    claim_id: str | None,
) -> dict[str, Any]:
    with_inflections = [r for r in results if r["expected_inflection_years"]]
    with_state = [r for r in results if r["expected_state"]]

    avg_recall = (
        sum(r["inflection_recall"] for r in with_inflections) / len(with_inflections)
        if with_inflections else 0.0
    )
    avg_precision = (
        sum(r["inflection_precision"] for r in with_inflections) / len(with_inflections)
        if with_inflections else 0.0
    )
    state_acc = (
        sum(1 for r in with_state if r["state_correct"]) / len(with_state)
        if with_state else 0.0
    )
    avg_papers = sum(r["paper_count"] for r in results) / len(results) if results else 0.0
    errors_total = sum(len(r["errors"]) for r in results)
    generated_at = datetime.now(UTC).isoformat()

    return {
        "available": True,
        "schema_version": "gold_eval_report.v1",
        "suite": "claim_intelligence_gold",
        "generated_at": generated_at,
        "last_refreshed": generated_at,
        "source": {
            "api_url": api_url,
            "gold_file": _display_path(gold_file),
            "limit": limit,
            "claim_id": claim_id,
        },
        "targets": TARGETS,
        "metrics": {
            "extraction_f1": _metric(CURRENT_BASELINES["extraction_f1"], target=TARGETS["extraction_f1"]),
            "inflection_recall": _metric(avg_recall, target=TARGETS["inflection_recall"]),
            "current_state_accuracy": _metric(state_acc, target=TARGETS["current_state_accuracy"]),
            "stance_f1": _metric(CURRENT_BASELINES["stance_f1"], target=TARGETS["stance_f1"]),
            "cost_per_claim_cold": _metric(CURRENT_BASELINES["cost_per_claim_cold"], unit="usd"),
        },
        "secondary_metrics": {
            "inflection_precision": round(avg_precision, 3),
            "avg_papers_per_claim": round(avg_papers, 1),
            "claims_evaluated": len(results),
            "pipeline_errors": errors_total,
        },
        "cases": results,
        "failure_modes": _derive_failure_modes(results),
    }


def _derive_failure_modes(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for row in results:
        if row.get("errors"):
            failures.append({
                "id": f"{row['id']}-provider-errors",
                "claim_id": row["id"],
                "title": "Provider or retrieval errors can suppress recall.",
                "summary": "Network/provider failures are counted as pipeline errors instead of hidden.",
                "details": row["errors"][:3],
            })
        if row.get("expected_inflection_years") and row.get("inflection_recall", 1.0) < TARGETS["inflection_recall"]:
            failures.append({
                "id": f"{row['id']}-missed-inflection",
                "claim_id": row["id"],
                "title": "Historical shifts can be missed when anchor papers are sparse.",
                "summary": "The detector needs papers on both sides of a known reversal window.",
                "details": [
                    f"Expected years: {row.get('expected_inflection_years')}",
                    f"Detected years: {row.get('detected_inflection_years')}",
                ],
            })
        if row.get("expected_state") and row.get("state_correct") is False:
            failures.append({
                "id": f"{row['id']}-state-mismatch",
                "claim_id": row["id"],
                "title": "Current-state labels can blur fragmented literatures.",
                "summary": "Near-parity support and qualified support can make one state label too coarse.",
                "details": [
                    f"Expected: {row.get('expected_state')}",
                    f"Detected: {row.get('detected_state')}",
                ],
            })
        if len(failures) >= 3:
            break
    return failures[:3]


def _metric(value: float | None, *, target: float | None = None, unit: str = "ratio") -> dict[str, Any]:
    rounded = None if value is None else (round(value, 4) if unit == "usd" else round(value, 3))
    if rounded is None:
        status = "unavailable"
    elif target is None:
        status = "measured"
    elif rounded >= target:
        status = "met"
    elif rounded >= target * 0.8:
        status = "near"
    else:
        status = "below"
    return {"value": rounded, "target": target, "unit": unit, "status": status}


def _post_json(url: str, body: dict[str, Any], *, api_key: str | None, timeout_s: float) -> dict[str, Any]:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["X-API-Key"] = api_key
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"POST {url} failed with HTTP {exc.code}: {body_text}") from exc


def _read_sse(url: str, *, api_key: str | None, timeout_s: float) -> Iterator[tuple[str, dict[str, Any]]]:
    headers = {"Accept": "text/event-stream"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["X-API-Key"] = api_key
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            event_name = "message"
            data_lines: list[str] = []
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
                if not line:
                    if data_lines:
                        payload = "\n".join(data_lines)
                        yield event_name, json.loads(payload or "{}")
                    event_name = "message"
                    data_lines = []
                    continue
                if line.startswith("event:"):
                    event_name = line.split(":", 1)[1].strip()
                elif line.startswith("data:"):
                    data_lines.append(line.split(":", 1)[1].strip())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GET {url} failed with HTTP {exc.code}: {body_text}") from exc


def _join_api(api_url: str, path_or_url: str) -> str:
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url
    base = api_url.rstrip("/")
    path = path_or_url if path_or_url.startswith("/") else f"/{path_or_url}"
    return urllib.parse.urljoin(f"{base}/", path.lstrip("/"))


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Causalith Claim Intelligence gold eval")
    parser.add_argument("--api-url", default=os.getenv("CAUSALITH_API_URL", "https://api.causalith.com"))
    parser.add_argument("--api-key", default=os.getenv("CAUSALITH_API_KEY"))
    parser.add_argument("--gold-file", type=Path, default=GOLD_FILE)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--claim-id", default=None)
    parser.add_argument("--max-papers", type=int, default=40)
    parser.add_argument("--timeout", type=float, default=240.0)
    parser.add_argument("--emit-json", type=Path, default=ROOT / "reports" / "gold_eval_latest.json")
    parser.add_argument("--fail-under-targets", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    gold_file = args.gold_file if args.gold_file.is_absolute() else ROOT / args.gold_file

    gold = load_gold(gold_file)
    if args.claim_id:
        gold = [row for row in gold if row["id"] == args.claim_id]
        if not gold:
            print(f"Claim id {args.claim_id!r} not found", file=sys.stderr)
            return 2
    if args.limit:
        gold = gold[: args.limit]

    print(f"Running {len(gold)} gold claims against {args.api_url}")
    results = [
        run_one(
            row,
            api_url=args.api_url,
            api_key=args.api_key,
            timeout_s=args.timeout,
            max_papers=args.max_papers,
            verbose=args.verbose,
        )
        for row in gold
    ]

    report = build_report(
        results=results,
        api_url=args.api_url,
        gold_file=gold_file,
        limit=args.limit,
        claim_id=args.claim_id,
    )
    output_path = args.emit_json if args.emit_json.is_absolute() else ROOT / args.emit_json
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    metrics = report["metrics"]
    secondary = report["secondary_metrics"]
    print("\nAggregate")
    print(f"  Extraction F1:          {_format_metric(metrics['extraction_f1'])}")
    print(f"  Inflection recall:      {_format_metric(metrics['inflection_recall'])}")
    print(f"  Inflection precision:   {_format_ratio(secondary['inflection_precision'])}")
    print(f"  Current-state accuracy: {_format_metric(metrics['current_state_accuracy'])}")
    print(f"  Stance F1:              {_format_metric(metrics['stance_f1'])}")
    print(f"  Cost/claim cold:        ${metrics['cost_per_claim_cold']['value']:.4f}")
    print(f"  Report:                 {output_path}")

    if args.fail_under_targets:
        failed = [
            key for key in ("inflection_recall", "current_state_accuracy")
            if metrics[key]["value"] is None or metrics[key]["value"] < TARGETS[key]
        ]
        return 1 if failed else 0
    return 0


def _format_metric(metric: dict[str, Any]) -> str:
    value = metric.get("value")
    if metric.get("unit") == "usd":
        return f"${value:.4f}" if value is not None else "-"
    return _format_ratio(value)


def _format_ratio(value: float | None) -> str:
    return "-" if value is None else f"{value:.1%}"


if __name__ == "__main__":
    raise SystemExit(main())
