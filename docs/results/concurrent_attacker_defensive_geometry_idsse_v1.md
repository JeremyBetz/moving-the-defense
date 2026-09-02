# Concurrent Attacker–Defensive Geometry v1 — IDSSE External Replication

**Final status:** **IDSSE EXTERNAL REPLICATION SUPPORTED**

The unchanged frozen design was executed across all seven governed IDSSE matches. Every match passed the pre-outcome provider-equivalence gate, produced a positive near-minus-middle estimate, and retained a positive estimate under the transported Metrica trim. The pooled estimate was positive with its 95% interval strictly above zero and retained 91.71% magnitude after trimming. All frozen support conditions therefore passed.

## Provider equivalence

Frames, raw timestamps, player/team/goalkeeper metadata, and player observed/null masks matched exactly in all seven matches. Maximum coordinate disagreement was below $2\times10^{-6}$ m against the frozen $10^{-5}$ m tolerance. Event context was shared exactly. The provider ball object uses a raw object ID while the canonical view uses a generic ball key; the raw ID remains in the provenance sidecar. Ball coordinates do not enter this construct, so this descriptive key difference is not a construct-equivalence failure.

The canonical period grid begins at the first observed provider frame; raw UTC timestamps remain the synchronization key for event context. Thus every anchor remains exactly `period origin + 2 + 4k` on the native 25 Hz cadence even though the event kickoff timestamp itself is not necessarily cadence-aligned.

## Match-level replications

| Match | Attacker-anchor observations | Unique anchors | Near | Middle | Far (descriptive) | Near − middle [95% interval] | Trim retained | Secondary deformation [95% interval] |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| J03WMX | 12,353 | 1,236 | 0.09788 | 0.04997 | 0.05596 | 0.04791 [0.03504, 0.06016] | 94.26% | 0.02454 [0.01627, 0.03299] |
| J03WN1 | 4,876 | 532 | 0.10040 | 0.03892 | 0.06653 | 0.06148 [0.03780, 0.08552] | 81.45% | 0.02633 [0.01329, 0.04020] |
| J03WOH | 11,287 | 1,129 | 0.08865 | 0.03935 | 0.05818 | 0.04930 [0.03699, 0.06267] | 96.98% | 0.02456 [0.01605, 0.03314] |
| J03WOY | 11,579 | 1,158 | 0.07086 | 0.03227 | 0.04840 | 0.03859 [0.02630, 0.05389] | 90.21% | 0.01939 [0.01168, 0.02848] |
| J03WPY | 12,433 | 1,244 | 0.09949 | 0.05430 | 0.05438 | 0.04520 [0.03280, 0.05971] | 92.18% | 0.02329 [0.01587, 0.03084] |
| J03WQQ | 10,000 | 1,023 | 0.09970 | 0.04291 | 0.06160 | 0.05679 [0.04188, 0.07132] | 85.60% | 0.02374 [0.01534, 0.03200] |
| J03WR9 | 11,538 | 1,154 | 0.10058 | 0.03434 | 0.04098 | 0.06624 [0.05328, 0.07995] | 96.12% | 0.03460 [0.02696, 0.04297] |

The sign count is **7/7 positive**. Individual-match intervals are reported transparently but were not separate significance gates. Secondary deformation is **SUPPORTIVE** in every match; it remains secondary and nonclassifying.

## Pooled precision summary

The pooled observation-weighted model contains 74,066 attacker-anchor observations, 7,476 match/period/time anchors, and 740,660 defender rows.

| Rank | Attacker-path coefficient (m/m) |
|---|---:|
| D1 | 0.15324 |
| D2 | 0.07269 |
| D3 | 0.05483 |
| D4 | 0.04898 |
| D5 | 0.04114 |
| D6 | 0.04334 |
| D7 | 0.03629 |
| D8 | 0.04136 |
| D9 | 0.05926 |
| D10 | 0.06171 |

Near was 0.09359, middle was 0.04244, and descriptive far was 0.05411. The primary pooled near-minus-middle estimate was **0.05115 m/m [0.04595, 0.05642]**.

The frozen trim removed 811 attacker anchors (1.095%). Its estimate was 0.04691 [0.04161, 0.05220], preserving the positive sign and 91.71% of the untrimmed magnitude. Pooled secondary deformation was 0.02513 [0.02198, 0.02830], classified **SUPPORTIVE** but excluded from the final status.

## Frozen status evaluation

| Condition | Result |
|---|---|
| All governed matches and pooled execution valid | PASS |
| Pooled near-minus-middle $>0$ | PASS |
| Pooled 95% interval strictly above zero | PASS |
| At least 5/7 match estimates positive | PASS: 7/7 |
| Pooled trimmed estimate positive | PASS |
| Trim retains at least 50% magnitude | PASS: 91.71% |
| No construct-equivalence failure | PASS |

Therefore the exact frozen result is **IDSSE EXTERNAL REPLICATION SUPPORTED**.

## Interpretation boundary

The strongest permitted statement is:

> Across the two Metrica sample matches and an independent seven-match IDSSE dataset, greater attacker movement within fixed two-second intervals was associated with stronger concurrent focal-relative defender movement among nearby than middle-ranked defenders after conditioning on the prospectively specified pre-interval movement context.

In plain football language: during the same two-second passage, defenders nearest to a moving attacker tended to move differently from the rest of the defensive unit more strongly than defenders in the middle proximity ranks. This is a repeated geometric association, not proof that the attacker caused a reaction or that the movement was tactically useful.

Important counterevidence and limitations remain. Every pooled rank coefficient is positive, the rank profile is not monotonic, and descriptive far exceeds middle. Pre-interval adjustment cannot eliminate concurrent shared movement or all omitted context. Seven matches provide seven replication units from one independent provider environment, not seven providers. The frozen seven-frame smoother spans 0.28 s at 25 Hz IDSSE but 0.70 s at 10 Hz Metrica; this physical-timescale difference was retained rather than tuned.

The result does not establish causation, defender reaction or latency, attention, marking responsibility, assignment, intent, dragging, pinning, space or opportunity creation, tactical success, gravity, player quality, or value.

## Reproduction

All six governed pre-closure outputs reproduced byte-for-byte in an independent complete rerun. Every pooled bootstrap family and all but two J03WN1 replicates produced 2,000 valid fits; J03WN1 produced 1,998, above the frozen 1,900 minimum. All designs had rank 72. Machine-readable results, coefficient intervals, exclusions, provider equivalence, observation rows, manifests, and closure hashes are in `outputs/concurrent_attacker_defensive_geometry_idsse_v1/`.
