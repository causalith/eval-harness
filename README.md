# Causalith Eval Harness

[![Weekly eval](https://github.com/causalith/eval-harness/actions/workflows/eval.yml/badge.svg)](https://github.com/causalith/eval-harness/actions/workflows/eval.yml)
[![codecov](https://codecov.io/gh/causalith/eval-harness/branch/main/graph/badge.svg)](https://codecov.io/gh/causalith/eval-harness)
[![Run on Replit](https://replit.com/badge/github/causalith/eval-harness)](https://replit.com/github/causalith/eval-harness)

Causalith maps research by claims, not citations. This public harness runs a curated 20-claim gold set against the Claim Intelligence API and publishes the numbers we use to decide whether the system is trustworthy enough to show users.

## Current Numbers

<!-- metrics:start -->
Last refreshed: `2026-07-27T06:49:18.220939+00:00`

| Metric | Current | Target | Status |
| --- | ---: | ---: | --- |
| M1 extraction F1 | 82% | 0.85 | near |
| Inflection recall | 0% | 0.80 | below |
| Current-state accuracy | 0% | 0.75 | below |
| Stance F1 | 71% | 0.75 | near |
| Cost per claim, cold | $0.0000 | No public target | measured |

Claims evaluated: `20` · Inflection precision: `0%` · Avg papers per claim: `0.0`
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
