# Opportunity Redistribution v1 — Game 1 Development Result

**Status:** **GAME 1 OPPORTUNITY REDISTRIBUTION DEVELOPMENT NEGATIVE**

The frozen protocol (`15825647...625fa`), configuration (`45c418a9...e431`), and prospective hash ledger (`aa5cba16...9df5`) matched before execution. No prior opportunity result existed. Game 2, Game 3, and IDSSE were not accessed.

## Sample

The complete-support rules retained 5,750 focal-attacker observations at 575 period/time anchors. Every anchor contained all ten simultaneous focal perspectives, nine non-focal attacking outfield players per perspective, and ten defending outfield players. Away supplied 3,240 focal rows and Home 2,510.

The period-2 diagnosis is **PERIOD-2 EXCLUSION CORRECT UNDER FROZEN RULES**. The inherited tracking-support registry prospectively invalidates Home Player3 and Away Player22 for the entirety of period 2. Each team therefore has at most nine supported outfield players there. Because Opportunity Redistribution v1 requires ten supported attackers and ten supported defenders simultaneously—not merely one focal attacker plus a complete opposing defence—no period-2 anchor can qualify. The implementation correctly enforced that frozen rule; it was not changed or relaxed after results.

Anchor-level exclusions were 503 for incomplete attacking support, 118 for incomplete defending support, 142 for restart/ball-out spans, 102 for an opposing possession-defining event after the anchor, and 9 for unavailable possession-team context. The frozen extreme-movement rule excluded 57 focal rows and retained 5,693.

The raw local-minus-remote separation-change outcome had median 0.02261 m, IQR −1.07236 to 1.13176 m, range −7.64628 to 7.31977 m, mean 0.04577 m, and population SD 1.87454 m. The raw defensive predictor $D$ had median 0.01323 m, IQR −0.57645 to 0.62747 m, range −5.51501 to 7.11332 m, mean 0.07365 m, and population SD 1.13879 m.

## Frozen primary model

Within-period/time-anchor demeaning retained full rank 6. The six no-intercept OLS coefficients were:

| Predictor | Estimate | Frozen 95% interval |
|---|---:|---:|
| Concurrent focal path $A$ | −0.04235 | [−0.08378, −0.00038] |
| Defensive contrast $D$ | **−0.02407** | **[−0.09392, 0.04776]** |
| Initial separation contrast $S_0$ | −0.08715 | [−0.11033, −0.06920] |
| Recipient-path contrast $M_R$ | −0.12841 | [−0.18673, −0.07145] |
| Prior focal path $A_{pre}$ | −0.00483 | [−0.05075, 0.04145] |
| Prior defensive contrast $D_{pre}$ | 0.03968 | [−0.02677, 0.11306] |

All 2,000 grouped 60-second block-bootstrap replicates were valid. Because the prospectively predicted primary coefficient $\hat\beta_D$ was nonpositive, the frozen decision tree assigns **NEGATIVE**. Neither another coefficient nor any secondary quantity can rescue that result.

## Frozen robustness and secondary description

| Specification | $\hat\beta_D$ | Frozen 95% interval | Sign |
|---|---:|---:|---:|
| Fixed-start nearest defender | 0.00914 | [−0.06411, 0.08427] | Positive |
| Three-nearest-defender separation | −0.08117 | [−0.15251, −0.00282] | Negative |
| Extreme focal-movement trim | −0.02852 | [−0.10268, 0.04578] | Negative |
| Endpoint deformation predictor, descriptive | 0.05122 | [−0.04477, 0.15139] | Positive |

The primary sign failed, and two of three classifying robustness signs also failed. The fixed-start alternative was weakly positive with an interval spanning zero. The descriptive deformation coefficient was positive with an interval spanning zero and is nonclassifying by design.

Local recipients gained 0.02668 m mean nearest-defender separation, while remote recipients lost 0.01908 m on average, but this unconditional geometric description does not establish the frozen conditional $D$ association. A median of two of the nine recipient nearest-defender identities changed between endpoints, reinforcing that nearest distance is a dynamic proximity description rather than an assignment.

## Interpretation boundary

The strongest permitted conclusion is:

> In Metrica Sample Game 1, the frozen model did not support the predicted positive conditional association between greater focal-local versus middle defender movement and relatively greater nearest-defender separation gain for other attackers initially local rather than remote to the focal attacker. The primary estimate was negative and uncertain, and its sign was not retained by two of three classifying robustness checks.

This negative result concerns the tested separation representation and conditional design. It does not show that attacking movement never changes teammates' opportunities, nor does it validate or refute pass availability, pitch control, tactical success, causation, reaction, responsibility, marking, dragging, pinning, tracking, space creation, gravity, or off-ball value. The strict complete-support sample covered period 1 only, and this remains one development match.

## Reproducibility

The complete execution was rerun independently. All nine governed machine-readable outputs reproduced byte-for-byte, every model had rank 6, every bootstrap family completed 2,000/2,000 replicates, and all hard checks passed. The deterministic first-anchor pitch panel is an audit example selected by sample order, not effect size.

Run:

```bash
MPLCONFIGDIR=/tmp/mtd-opportunity .venv/bin/python src/opportunity_redistribution_game1_v1.py
MPLCONFIGDIR=/tmp/mtd-opportunity .venv/bin/python src/opportunity_redistribution_game1_v1.py --reproduce
```

Machine-readable artifacts are in `outputs/opportunity_redistribution_game1_v1/`; figures are in `figures/opportunity_redistribution_game1_v1/`.
