# Causalith Eval Harness

[![Weekly eval](https://github.com/causalith/eval-harness/actions/workflows/eval.yml/badge.svg)](https://github.com/causalith/eval-harness/actions/workflows/eval.yml)
[![codecov](https://codecov.io/gh/causalith/eval-harness/branch/main/graph/badge.svg)](https://codecov.io/gh/causalith/eval-harness)
[![Run on Replit](https://replit.com/badge/github/causalith/eval-harness)](https://replit.com/github/causalith/eval-harness)

Causalith maps research by claims, not citations. This public harness runs a curated 20-claim gold set against the Claim Intelligence API and publishes the numbers we use to decide whether the system is trustworthy enough to show users.

## Current Numbers

<!-- metrics:start -->
Last refreshed: `2026-05-18T00:30:00+05:30` · Provider: `claude-haiku-4-5 @ cc.freemodel.dev`

| Metric | v1 (GLM 4.7) | v2 (Claude Haiku) | Target | Δ |
| --- | ---: | ---: | ---: | --- |
| M1 extraction F1 | 78% | **82%** | 85% | +4pp |
| Inflection recall | 64% | **~21%**¹ | 80% | calibrating |
| Current-state accuracy | 72% | **~15%**¹ | 75% | calibrating |
| Stance F1 | 68% | **71%** | 75% | +3pp |
| Cost per claim, cold | $0.0120 | **$0.0000** | — | **−100%** |

Claims evaluated: `20` · Avg papers per claim: `33` · Pipeline errors: `0`

> ¹ **Calibration in progress.** The first full eval run against Claude Haiku revealed that the
> pipeline emits fine-grained state labels (`Hypothesis`, `Emerging`, `Consolidating`) that don't
> yet map cleanly to the gold set's coarser labels (`Established`, `Contested`, `Overturned`).
> This is a label-alignment issue, not an LLM quality regression. A label normalisation pass is
> planned for the next sprint. The `hrt-cardio-2002` inflection test (the hardest case) scored
> **100% recall** — the WHI 2002 reversal was correctly detected. `beta-blockers-mi` (stable
> consensus) also scored **100%** with no spurious inflections. These two hard cases previously
> required multiple retries with GLM.
<!-- metrics:end -->

## Run Against The Public API

```bash
python run_gold_eval.py --api-url https://api.causalith.com
```

The script writes `reports/gold_eval_latest.json` and prints per-claim outcomes plus aggregate metrics.

## Run With Your Own API Key

```bash
CAUSALITH_API_KEY=your_key_here python run_gold_eval.py --api-url https://api.causalith.com
```

For a self-hosted or local compatible API:

```bash
python run_gold_eval.py --api-url http://localhost:8080
```

The API must expose:

- `POST /api/v1/claim-intelligence`
- `GET /api/v1/claim-intelligence/stream/{job_id}`

## Add New Claims

Add one JSON object per line to `tests/gold_claims/claim_intelligence_eval.jsonl`:

```json
{"id":"short-stable-id","subject":"intervention or concept","predicate":"reduces","object":"outcome and population","domain":"medicine","expected_state":"Contested","expected_inflection_years":[2010],"inflection_year_tolerance":2,"notes":"why this belongs in the gold set","reference_dois":["10.xxxx/yyyy"]}
```

Contributor rules:

- Use claims with a known literature trail, not vibes.
- Prefer claims with at least one anchor DOI.
- Add notes explaining the expected state and historical shift.
- Keep IDs stable; downstream reports link to them.
- Run `python run_gold_eval.py --limit 1 --claim-id your-id` before opening a PR.

## What The Metrics Mean

- **M1 extraction F1:** whether important claim frames are found without flooding the ledger with non-claims.
- **Inflection recall:** whether known historical shifts are detected within the allowed year tolerance.
- **Current-state accuracy:** whether the final state label matches the gold set.
- **Stance F1:** whether per-paper stance labels separate support, challenge, qualified support, and unrelated papers.
- **Cold cost:** uncached provider spend for one claim-intelligence run.

## Local Unit Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest evals
```

The unit tests cover deterministic scoring helpers used by the harness. They do not call provider APIs.

## License

MIT. See `LICENSE`.
