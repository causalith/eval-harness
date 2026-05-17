# Helicobacter Pylori and Peptic Ulcers

Gold-set ID: `helicobacter-ulcers`  
Eval tier: **discovery arc** — claim moved from fringe hypothesis to accepted causal mechanism  
Last updated by harness: 2026-04-11

---

## Claim under evaluation

> "Helicobacter pylori infection is a primary cause of peptic ulcer disease and can be cured by antibiotic eradication therapy."

**Canonical form used by the engine:**  
`H_pylori_infection → peptic_ulcer_disease` ∧ `H_pylori_eradication → ulcer_resolution`

---

## Why this case exists

The H. pylori story is the cleanest example of a discovery-era transition in modern medicine: a hypothesis that was initially dismissed by the field, then progressively established through experimental, epidemiological, and clinical evidence over roughly 12 years, culminating in a Nobel Prize in 2005.

The challenge for the engine is to represent the **temporal shape** of this evidence correctly:

- Early literature: predominantly challenging or ignoring the hypothesis
- 1987–1994: rapid transition from contested to conditionally supported
- 1994–present: strong, stable support with no reversal

A system that returns "strong support" without surfacing the discovery arc is flattening the literature. A system that flags uncertainty in the current period is hallucinating a challenge layer that does not exist.

---

## Evidence chronology

| Year | Paper | Journal | Stance | Notes |
|------|-------|---------|--------|-------|
| 1983 | Warren JR & Marshall B — "Unidentified curved bacilli on gastric epithelium in active chronic gastritis" | *Lancet* 321:1273–1275 | Supporting (hypothesis) | Founding observation; bacteria identified in 13/13 ulcer patients; initial skepticism from reviewers |
| 1984 | Marshall BJ et al. — "Attempt to fulfil Koch's postulates for pyloric campylobacter" | *Med J Aust* 142:436–439 | Supporting | Marshall's self-inoculation experiment; developed gastritis; fulfilled Koch's postulates partially |
| 1987 | Marshall BJ et al. — "Bismuth subsalicylate suppresses Helicobacter pylori in non-ulcer dyspepsia" | *Gastroenterology* 93:525–532 | Supporting | Antibiotic suppression correlated with symptom relief; first therapeutic signal |
| 1989 | Rauws EAJ & Tytgat GNJ — "Cure of duodenal ulcer associated with eradication of Helicobacter pylori" | *Lancet* 335:1233–1235 | Supporting | Eradication → ulcer cure in 95% of treated patients; pivotal clinical evidence |
| 1990 | Graham DY et al. — "Effect of triple therapy on duodenal ulcers" | *Ann Intern Med* 115:266–269 | Supporting | RCT; triple therapy reduces recurrence from 80% to 5% at 1 year |
| 1991 | Nomura A et al. — "Helicobacter pylori infection and gastric carcinoma among Japanese Americans" | *N Engl J Med* 325:1132–1136 | Supporting | Extended claim: H. pylori associated with gastric cancer; serologic cohort study |
| 1992 | Parsonnet J et al. — "Helicobacter pylori infection and the risk of gastric carcinoma" | *N Engl J Med* 325:1127–1131 | Supporting | Independent replication of cancer association; confirmed in Western population |
| 1994 | NIH Consensus Development Panel — "Helicobacter pylori in peptic ulcer disease" | *JAMA* 272:65–69 | Supporting | US national consensus; first guideline endorsement; eradication recommended for all H. pylori-positive ulcer patients |
| 1996 | van der Hulst RWM et al. — "Eradication of Helicobacter pylori and ulcer recurrence" | *Helicobacter* 1:6–19 | Supporting | Systematic review; recurrence 5–10% with eradication vs 70–80% without |
| 1997 | Huang JQ et al. — "Role of Helicobacter pylori in the etiology of duodenal ulcer" | *Gastroenterology* 113:1169–1181 | Supporting | Large meta-analysis; OR=3.8 for duodenal ulcer in H. pylori-positive individuals |
| 2000 | Laine L & Hopkins RJ — "Has the impact of Helicobacter pylori therapy on ulcer recurrence in the United States been overstated?" | *Ann Intern Med* 132:719–723 | Conditional | NSAID-associated ulcers have different etiology; H. pylori not sufficient for all ulcer subtypes |
| 2005 | Nobel Committee — Barry Marshall and Robin Warren awarded Nobel Prize in Physiology or Medicine | Nobel Foundation | Supporting (institutional) | Formal recognition; described as "one of the most radical reversals of medical thinking" |
| 2017 | Malfertheiner P et al. — "Management of Helicobacter pylori infection: the Maastricht V/Florence Consensus Report" | *Gut* 66:6–30 | Supporting | Fifth consensus; eradication first-line for all H. pylori-positive peptic ulcer; resistance monitoring added |
| 2022 | Shah SC & Iyer PG — "AGA Clinical Practice Update on the management of H. pylori" | *Gastroenterology* 162:1757–1766 | Supporting | Current US guideline; test-and-treat recommended; antibiotic selection by resistance profile |

---

## Inflection points detected

**⚡ 1983–1984 — Marshall & Warren founding papers**  
The initial hypothesis was met with significant editorial resistance; the *Lancet* paper was submitted twice before acceptance. Despite early dismissal, the experimental inoculation (Marshall 1984) established biological plausibility that prevented complete marginalization. Causalith should classify this period as **hypothesis introduction** — not yet supporting in the evidentiary sense.

**⚡ 1989–1994 — Therapeutic evidence cascade**  
Between 1989 (Rauws & Tytgat ulcer cure) and 1994 (NIH Consensus), the claim moved from hypothesis to accepted causal mechanism within roughly 5 years. This is one of the fastest consensus-formation events in 20th-century clinical medicine. The engine should detect the **rapid transition inflection** in this window — a near-vertical rise in supporting paper share.

**⚡ 1994 — NIH Consensus**  
Institutional endorsement as a discrete event. The consensus panel statement is the clearest single marker of field acceptance. Prior to 1994, clinical practice varied widely; after 1994, eradication became standard of care within 3 years at most major centers.

**⚡ 2000 onward — NSAID conditionality**  
Recognition that NSAID use is an independent ulcer etiology that H. pylori eradication does not address. The engine must represent this as a **scope refinement**, not a challenge to the core claim.

---

## Verdict breakdown (engine output)

```
Claim:  "H. pylori causes peptic ulcers; eradication cures them"
Period: 1983–2025

Supporting papers identified:   87
Challenging papers identified:    3  (all pre-1992, methodological objections)
Conditional papers identified:   11  (NSAID-associated ulcer subtype)
Total evaluated:                101

Epistemic state:     STABLE_SUPPORT
Confidence score:    0.94
Reversal detected:   false
Discovery arc:       CONFIRMED  (1983–1994)
Transition speed:    HIGH  (consensus in ~11 years)

Population splits logged:
  - H. pylori-positive duodenal ulcer:      strong support for eradication
  - H. pylori-positive gastric ulcer:       strong support for eradication
  - NSAID-associated ulcer, H. pylori neg:  H. pylori eradication not relevant
  - H. pylori-positive, no ulcer (NERD):    conditional (test-and-treat debated)
```

---

## Condition matrix

| Population / Context | Verdict | Key driver |
|---|---|---|
| H. pylori-positive peptic ulcer (any) | Strong support | NIH 1994, Maastricht V 2017, RCT meta-analyses |
| H. pylori-positive, duodenal ulcer | Strong support | Rauws 1989, Graham 1990, van der Hulst 1996 |
| NSAID-associated ulcer, H. pylori-negative | Not applicable | Laine 2000 — different etiology |
| NSAID + H. pylori double-positive | Conditional support | Eradication helpful but insufficient alone |
| H. pylori eradication → reduced gastric cancer risk | Conditional support | Nomura 1991, Parsonnet 1992 — extended claim |
| Current first-line antibiotic regimen efficacy | Conditional | Resistance rates vary by region; Maastricht V |

---

## What the evaluator must get right

- **Surface the discovery arc** — the claim did not arrive as consensus; it was contested until ~1992 and then accepted rapidly; this temporal shape is the core test
- **Do not fabricate a modern challenge layer** — there is essentially no credible post-1998 literature challenging the H. pylori → ulcer causal claim
- **Return STABLE_SUPPORT for the current period** — this is a resolved question; hedging excessively is a false-uncertainty error
- **Identify 1994 NIH Consensus as the institutional acceptance marker** — this is the conventional endpoint of the discovery arc
- **Note NSAID conditionality as scope refinement, not challenge** — the claim does not cover all ulcers, only H. pylori-positive ulcers

---

## Sample Causalith engine trace

```
[stance_classifier]  paper: Warren & Marshall 1983
  → stance: supporting  (prob=0.91)
  → note: founding observational; hypothesis stage

[stance_classifier]  paper: Graham et al. 1990 Ann Intern Med
  → stance: supporting  (prob=0.96)
  → note: RCT; recurrence 80% → 5%; high-weight evidence

[stance_classifier]  paper: Laine & Hopkins 2000
  → stance: conditional  (prob=0.84)
  → condition: nsaid_associated_ulcer_subtype

[inflection_detector]  window: 1988–1995
  → supporting_share: 0.21 → 0.89
  → inflection: CONFIRMED  label="therapeutic_evidence_cascade"
  → transition_speed: HIGH (7-year window)

[discovery_arc_detector]
  → arc_start: 1983
  → arc_end:   1994
  → arc_confirmed: true
  → note: "Hypothesis-to-consensus in 11 years.
           Institutional marker: NIH Consensus 1994.
           Nobel recognition: 2005."

[verdict_engine]
  → epistemic_state: STABLE_SUPPORT
  → note: "Discovery arc confirmed 1983–1994. No credible
           challenge layer post-1994. NSAID etiology is
           an independent pathway, not a contradiction.
           Current evidence strongly supports eradication
           as primary treatment for H. pylori-positive
           peptic ulcer."
```

---

## Citation notes

Warren & Marshall 1983 and 1984 papers are real publications with accurate journal citations. NIH Consensus 1994 and Maastricht V 2017 are real documents. Paper counts in this trail are representative. This case is part of the Causalith public eval harness and is not a clinical recommendation. See [CONTRIBUTORS.md](../../CONTRIBUTORS.md) for how to propose corrections.
