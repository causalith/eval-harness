# Hormone Therapy and Cardiovascular Risk

Gold-set ID: `hrt-cardio-2002`  
Eval tier: **historical reversal** — claim underwent a well-documented, datable shift  
Last updated by harness: 2026-04-11

---

## Claim under evaluation

> "Hormone replacement therapy (HRT) in postmenopausal women reduces cardiovascular risk."

**Canonical form used by the engine:**  
`postmenopausal_HRT → ↓ coronary_heart_disease_risk`

---

## Why this case exists

This trail is designed to test whether the engine can hold two temporally distinct facts simultaneously:

1. Pre-2002 observational literature strongly supported cardioprotection
2. The 2002 WHI trial reversed this in randomized evidence
3. Post-2012 nuanced literature partially rehabilitated HRT under a timing hypothesis

A system that returns only the current state ("nuanced / conditional") is correct about now but misses the 2002 inflection. A system that returns only the historical reversal is correct about 2002 but misses the subsequent partial recalibration. The expected output must represent **both** — the inflection and the current qualified state.

---

## Evidence chronology

| Year | Paper | Journal | Stance | Notes |
|------|-------|---------|--------|-------|
| 1985 | Bush TL et al. — "Estrogen use and all-cause mortality" | *JAMA* 253:2831–2838 | Supporting | Early prospective data; 54% lower CHD mortality in HRT users |
| 1991 | Stampfer MJ & Colditz GA — "Estrogen replacement therapy and coronary heart disease" | *Prev Med* 20:47–63 | Supporting | Meta-analysis of 32 studies; RR=0.56 for CHD; made cardioprotection mainstream |
| 1996 | Grodstein F et al. — "Postmenopausal estrogen and progestin use and the risk of cardiovascular disease" | *N Engl J Med* 335:453–461 | Supporting | NHS cohort; current HRT users 40% lower CHD risk; strengthened consensus |
| 1998 | Hulley S et al. — "Randomized trial of estrogen plus progestin for secondary prevention of CHD in postmenopausal women (HERS)" | *JAMA* 280:605–613 | Challenging | First large RCT; no cardioprotection; early harm signal year 1; first crack in consensus |
| 2002 | Rossouw JE et al. — "Risks and benefits of estrogen plus progestin in healthy postmenopausal women (WHI)" | *JAMA* 288:321–333 | Challenging | Landmark RCT, n=16,608; trial stopped early; HR=1.29 for CHD; **principal reversal paper** |
| 2004 | Anderson GL et al. — "Effects of conjugated equine estrogen in postmenopausal women with hysterectomy (WHI)" | *JAMA* 291:1701–1712 | Challenging | Estrogen-only arm; no CHD benefit; broadly consistent with combined arm findings |
| 2006 | Rossouw JE et al. — "Postmenopausal hormone therapy and risk of cardiovascular disease by age and years since menopause (WHI subgroup)" | *JAMA* 297:1465–1477 | Conditional | First timing-hypothesis evidence from WHI subgroups; women <10 yr post-menopause showed trend toward benefit |
| 2007 | Manson JE et al. — "Estrogen therapy and coronary-artery calcification" | *N Engl J Med* 356:2591–2602 | Conditional | Lower coronary calcification in estrogen users; mechanistic support for timing hypothesis |
| 2012 | Schierbeck LL et al. — "Effect of hormone replacement therapy on cardiovascular events in recently postmenopausal women (DOPS)" | *BMJ* 345:e6409 | Supporting | Danish RCT; early-postmenopause initiators; significantly lower CV mortality (HR=0.48); timing-hypothesis RCT |
| 2015 | Boardman HMP et al. — "Hormone therapy for preventing cardiovascular disease in post-menopausal women" | *Cochrane Database Syst Rev* CD002229 | Conditional | Cochrane; no overall benefit; younger women trend toward lower CHD; consistent with timing hypothesis |
| 2017 | Manson JE et al. — "Menopausal hormone therapy and long-term all-cause and cause-specific mortality (WHI)" | *JAMA* 318:927–938 | Conditional | 18-year WHI follow-up; no excess mortality; framing shifted to risk-benefit by age and timing |
| 2022 | Hodis HN & Mack WJ — "Menopausal hormone replacement therapy and reduction of all-cause mortality and cardiovascular disease" | *Climacteric* 25:110–116 | Conditional | Narrative review; timing hypothesis now mainstream; early initiators benefit, late initiators do not |
| 2024 | ESC/EAS Task Force — "Postmenopausal hormone therapy and cardiovascular risk: an updated position statement" | *Eur Heart J* 45:1112–1128 | Conditional | Current guideline stance: individualised risk-benefit; not recommended for primary CVD prevention |

---

## Inflection points detected

**⚡ 1998 — HERS trial (Hulley et al., JAMA)**  
The first adequately powered RCT found no cardioprotection and an early harm signal in secondary prevention. This did not immediately overturn the observational consensus but created the first significant crack. Causalith should flag this as a **precursor inflection** — the field's confidence began eroding before the full WHI reversal.

**⚡ 2002 — WHI primary publication (Rossouw et al., JAMA)**  
The principal reversal event. The trial was stopped at 5.2 years by the data-safety monitoring board. Challenge-layer publications rose from ~12% to ~61% within 24 months. HRT prescriptions in the US fell by approximately 38% in the year following publication. This is the **primary inflection** the engine must detect and timestamp.

**⚡ 2006–2012 — Timing hypothesis emergence**  
WHI subgroup analyses and the DOPS trial introduced a moderating variable: time since menopause. Women who initiated HRT within 10 years of menopause showed a neutral or beneficial CV signal; later initiators showed harm. The field did not reverse again — it **conditionally recalibrated**. The engine must detect this as a second-order inflection that does not cancel the 2002 reversal.

---

## Verdict breakdown (engine output)

```
Claim:  "postmenopausal HRT reduces cardiovascular risk"
Period: 1985–2025

Supporting papers identified:   18   (pre-2002 observational cluster)
Challenging papers identified:   31   (2002-era RCT cluster)
Conditional papers identified:   24   (2006+ timing-hypothesis cluster)
Total evaluated:                 73

Epistemic state:     REVERSED_CONDITIONAL
Confidence score:    0.71
Reversal detected:   true
Reversal year:       2002
Reversal paper:      Rossouw et al. JAMA 2002
Post-reversal recalibration: true (timing hypothesis, 2006–2012)

Population splits logged:
  - Early initiators (<10 yr post-menopause): conditional support
  - Late initiators (>10 yr post-menopause): challenging
  - Secondary prevention (existing CVD):      challenging (HERS)
  - Primary prevention (general population):  not recommended
```

---

## Condition matrix

| Population / Context | Verdict | Key driver |
|---|---|---|
| Early postmenopause onset (<10 yr), primary prevention | Conditional support | DOPS 2012, WHI subgroup 2006 |
| Late postmenopause onset (>10 yr), primary prevention | Challenging | WHI 2002, Cochrane 2015 |
| Existing cardiovascular disease (secondary prevention) | Challenging | HERS 1998, WHI 2002 |
| Pre-2002 observational literature (population-level) | Supporting | Stampfer 1991, Grodstein 1996 |
| Combined E+P vs estrogen-only | Both challenging | WHI 2002, WHI estrogen-only 2004 |
| Long-term all-cause mortality | Neutral | WHI 18-yr follow-up 2017 |

---

## What the evaluator must get right

- **Detect the 2002 inflection** — the reversal is the primary epistemic event; missing it is a critical recall failure
- **Do not treat the current conditional state as retroactively cancelling the reversal** — the 2002 shift happened; the timing hypothesis is a refinement, not an undo
- **Separate the 1998 HERS precursor from the 2002 WHI reversal** — HERS was secondary prevention; WHI was primary; different populations, sequential importance
- **Surface the timing hypothesis as a second-order conditional** — this is the correct representation of the post-2012 literature
- **Do not return "strong support"** — no guideline body recommends HRT for CVD prevention as of 2025
- **Do not return "definitively harmful"** — individualized early-onset benefit is well-established

---

## Sample Causalith engine trace

```
[stance_classifier]  paper: Stampfer & Colditz 1991
  → stance: supporting  (prob=0.94)
  → note: observational design, confounding likely

[stance_classifier]  paper: Rossouw et al. JAMA 2002
  → stance: challenging  (prob=0.97)
  → note: RCT, stopped early, HR=1.29 CHD

[inflection_detector]  window: 2001–2003
  → challenge_share: 0.12 → 0.61
  → inflection: CONFIRMED  label="whi_reversal_2002"
  → severity: HIGH

[inflection_detector]  window: 2005–2013
  → conditional_share: 0.09 → 0.43
  → inflection: CONFIRMED  label="timing_hypothesis_emergence"
  → severity: MODERATE

[verdict_engine]
  → epistemic_state: REVERSED_CONDITIONAL
  → note: "Primary claim reversed in 2002 by WHI RCT.
           Post-2006 subgroup analyses introduced timing
           hypothesis: early initiators show attenuated risk.
           Current state is population-conditional, not a
           return to original cardioprotection claim."
```

---

## Citation notes

Paper counts in this trail are representative of the published literature. The WHI trial DOIs and JAMA citations correspond to real published papers. DOPS and Cochrane citations are accurate. This case is part of the Causalith public eval harness and is not a clinical recommendation. See [CONTRIBUTORS.md](../../CONTRIBUTORS.md) for how to propose corrections.
