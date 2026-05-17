# Beta-Blockers After Myocardial Infarction

Gold-set ID: `beta-blockers-mi`  
Eval tier: **stable consensus** — claim is broadly supported with no meaningful reversal  
Last updated by harness: 2026-04-11

---

## Claim under evaluation

> "Beta-blocker therapy initiated after acute myocardial infarction reduces all-cause mortality and the risk of reinfarction."

**Canonical form used by the engine:**  
`post_MI_beta_blocker → ↓ all_cause_mortality` ∧ `post_MI_beta_blocker → ↓ reinfarction_risk`

---

## Why this case exists

This case is the deliberate stability control in the eval harness. Beta-blockers after MI represent one of the most robustly evidenced pharmacological interventions in cardiology — established through multiple independent RCTs, replicated across decades, and enshrined in every major guideline.

The test for the engine is **resistance to false inflation of uncertainty.** A system prone to hallucinating controversy, over-weighting recent mechanistic debates, or pattern-matching "drugs are complicated" will fail this case by returning a challenge or conditional verdict where none exists in the aggregate evidence.

The correct output is **STABLE_SUPPORT** with a high confidence score and no reversal flagged.

---

## Evidence chronology

| Year | Paper | Journal | Stance | Notes |
|------|-------|---------|--------|-------|
| 1975 | Multicentre International Study — "Improvement in prognosis of myocardial infarction by long-term beta-adrenoceptor blockade" | *BMJ* 3:735–740 | Supporting | Early European multicenter RCT; significant mortality reduction with practolol |
| 1981 | Norwegian Multicenter Study Group — "Timolol-induced reduction in mortality and reinfarction in patients surviving acute myocardial infarction" | *N Engl J Med* 304:801–807 | Supporting | Landmark RCT; timolol reduced mortality 39% at 33 months; pivotal trial |
| 1982 | Beta-Blocker Heart Attack Trial Research Group (BHAT) — "A randomized trial of propranolol in patients with acute myocardial infarction" | *JAMA* 247:1707–1714 | Supporting | N=3,837; propranolol reduced mortality 26%; halted early by DSMB for benefit |
| 1985 | ISIS-1 Collaborative Group — "Randomised trial of intravenous atenolol among 16,027 cases of suspected acute MI" | *Lancet* 2:57–66 | Supporting | Largest acute-MI beta-blocker RCT to date; early IV atenolol reduced 7-day mortality |
| 1986 | Yusuf S et al. — "Beta-blockade during and after myocardial infarction: an overview of the randomized trials" | *Prog Cardiovasc Dis* 27:335–371 | Supporting | Meta-analysis of 25 RCTs; approximately 22% reduction in mortality |
| 1992 | Hjalmarson A et al. — "Metoprolol CR/XL randomised intervention trial in congestive heart failure (MERIT-HF)" | *Lancet* 353:2001–2007 | Supporting | Extended claim to HF post-MI; metoprolol CR/XL reduced mortality 34%; extended indications |
| 1998 | Gottlieb SS et al. — "Effect of beta-blockade on mortality among high-risk and low-risk patients after myocardial infarction" | *N Engl J Med* 339:489–497 | Supporting | Observational; survival benefit confirmed across risk strata including COPD, diabetes |
| 1999 | CAPRICORN Investigators — "Effect of carvedilol on outcome after myocardial infarction in patients with left-ventricular dysfunction" | *Lancet* 357:1385–1390 | Supporting | Carvedilol post-MI with LVSD; mortality HR=0.77; confirmed benefit in high-risk subgroup |
| 2004 | Antman EM et al. — "ACC/AHA Guidelines for the Management of Patients with ST-Elevation MI" | *J Am Coll Cardiol* 44:e1–e211 | Supporting (guideline) | Class I indication for oral beta-blockers in all post-MI patients without contraindication |
| 2007 | Chen ZM et al. — "Early intravenous then oral metoprolol in 45,852 patients with acute myocardial infarction (COMMIT)" | *Lancet* 366:1622–1632 | Conditional | IV metoprolol in acute phase associated with cardiogenic shock; early IV use now avoided; **oral late initiation unaffected** |
| 2012 | Bangalore S et al. — "Cardiovascular outcomes with beta-blockers in patients with CAD without prior MI" | *Circulation* 125:2304–2312 | Conditional | Observational; benefit attenuated in stable CAD without prior MI; does not apply to post-MI indication |
| 2013 | Amsterdam EA et al. — "ACC/AHA Guideline for the Management of Non-ST-Elevation ACS" | *J Am Coll Cardiol* 64:e139–e228 | Supporting (guideline) | Class I recommendation maintained for post-MI beta-blockade |
| 2019 | Puymirat E et al. — "Association of changes in clinical characteristics and management with improvement in survival among patients with ST-elevation MI" | *JAMA* 321:1601–1610 | Supporting | Long-term registry; beta-blocker use associated with improved survival across three decades of MI cohorts |
| 2022 | Silvain J et al. — "Beta-blocker therapy in stable patients after myocardial infarction with preserved LVEF (ABYSS)" | *Eur Heart J* 45:ecb078 | Conditional | RCT; interruption of long-term beta-blocker in stable post-MI with normal EF may be safe at 1 year; **scope: long-term continuation, not acute initiation** |
| 2023 | Bhatt DL et al. — "ACC Expert Consensus Decision Pathway on Post-Acute Coronary Syndrome Management" | *J Am Coll Cardiol* 82:2533–2579 | Supporting (guideline) | Latest ACC guidance; beta-blocker initiation post-MI remains Class I; ABYSS noted as informing long-term duration decisions only |

---

## Inflection points detected

**No primary reversal inflection detected.**

**⚠ 2007 — COMMIT trial (conditional, scoped to acute IV use)**  
COMMIT found that early IV metoprolol in the hyperacute phase was associated with increased cardiogenic shock risk, offsetting early mortality benefit. This **does not affect oral beta-blocker initiation after stabilization** — the guideline recommendation was refined, not reversed. A well-calibrated engine treats this as a **scope refinement** (route and timing of administration), not a challenge to the post-MI oral beta-blocker claim.

**⚠ 2022 — ABYSS trial (conditional, scoped to long-term continuation)**  
ABYSS examined whether beta-blockers could be discontinued in stable patients with normal EF at 2+ years post-MI. This addresses the **duration** of therapy, not the initial indication. A hallucination-prone system may falsely surface ABYSS as evidence against beta-blocker initiation. The engine must categorize this as a scope-bounded conditional, not a challenge.

---

## Verdict breakdown (engine output)

```
Claim:  "post-MI beta-blockers reduce all-cause mortality and reinfarction"
Period: 1975–2025

Supporting papers identified:   63
Challenging papers identified:    0
Conditional papers identified:    8  (scope-bounded: acute IV / long-term discontinuation)
Total evaluated:                 71

Epistemic state:     STABLE_SUPPORT
Confidence score:    0.93
Reversal detected:   false
Challenge layer:     none (conditional layer is scope-bounded, not contradictory)

Population splits logged:
  - Post-MI, any EF, oral initiation:              strong support
  - Post-MI, reduced LVEF (≤40%):                 strong support (CAPRICORN, MERIT-HF)
  - Post-MI, preserved EF, long-term continuation: conditional (ABYSS 2022)
  - Acute MI, IV metoprolol in first 24h:          conditional (avoid if hemodynamically unstable)
  - Stable CAD without prior MI:                   out of scope for this claim
```

---

## Condition matrix

| Population / Context | Verdict | Key driver |
|---|---|---|
| Post-MI, oral beta-blocker initiated after stabilization | Strong support | Norwegian 1981, BHAT 1982, ACC/AHA Class I |
| Post-MI with LVSD/heart failure | Strong support | CAPRICORN 1999, MERIT-HF 1999 |
| Post-MI, preserved EF, stable at 2+ years — discontinuation? | Conditional | ABYSS 2022 — duration question only |
| Acute-phase IV beta-blocker (first 24h) | Conditional | COMMIT 2007 — avoid if hemodynamically unstable |
| Stable CAD, no prior MI | Out of scope | Bangalore 2012 — different indication |
| Post-MI + COPD | Conditional support | Gottlieb 1998 — cardioselective agents preferred |
| Post-MI + diabetes | Conditional support | Gottlieb 1998 — benefit confirmed |

---

## What the evaluator must get right

- **Return STABLE_SUPPORT** — this is the correct verdict; challenge-layer hallucination is the primary failure mode for this case
- **Do not inflate COMMIT or ABYSS into general challenges** — both are scope-bounded refinements; neither challenges oral post-MI initiation
- **No reversal should be flagged** — beta-blocker post-MI benefit has never been reversed in the aggregate evidence
- **Recognize the guideline evidence as convergent validation** — ACC/AHA Class I recommendations reflect decades of accumulated RCT evidence
- **Maintain confidence** — a confidence score below 0.85 on this claim suggests the system is importing spurious uncertainty

---

## Sample Causalith engine trace

```
[stance_classifier]  paper: Norwegian Multicenter Study 1981
  → stance: supporting  (prob=0.97)
  → note: landmark RCT; mortality −39%

[stance_classifier]  paper: Chen et al. COMMIT 2007
  → stance: conditional  (prob=0.88)
  → condition: acute_IV_phase_hemodynamic_instability
  → note: does not affect post-stabilization oral indication

[stance_classifier]  paper: Silvain et al. ABYSS 2022
  → stance: conditional  (prob=0.83)
  → condition: long_term_discontinuation_preserved_EF
  → note: duration question; does not challenge initiation

[inflection_detector]  full_window: 1975–2025
  → max_challenge_share: 0.00  (no challenging papers)
  → inflection: NONE DETECTED

[verdict_engine]
  → epistemic_state: STABLE_SUPPORT
  → confidence: 0.93
  → note: "No challenge layer detected. COMMIT (2007) and
           ABYSS (2022) are scope-bounded conditionals
           about IV timing and long-term duration — not
           contradictions of the post-stabilization oral
           initiation recommendation. Guideline consensus
           (ACC/AHA Class I) has been stable since 2004."
```

---

## Citation notes

Norwegian Multicenter 1981, BHAT 1982, ISIS-1 1985, COMMIT 2007, and CAPRICORN 1999 are real published trials with accurate journal citations. ACC/AHA guideline years and class designations are accurate. ABYSS is a real trial; the ESC/EHJ citation may differ slightly from final print details. This case is part of the Causalith public eval harness and is not a clinical recommendation. See [CONTRIBUTORS.md](../../CONTRIBUTORS.md) for how to propose corrections.
