# Concurrent Attacker–Defensive Geometry v1 — Game 1 Development Result

**Status:** **GAME 1 CONCURRENT GEOMETRY DEVELOPMENT COHERENT**

**Execution tier:** Tier 1 development

The protocol (`1382e97f...b8f32`), configuration (`5b372112...c692d`), and prospective hash ledger (`7fb68191...873d`) matched the frozen identities before execution. No prior result existed. Game 2, Game 3, IDSSE, and opportunity outcomes were not accessed.

## Sample and implementation

The governed period-origin grid retained 8,265 attacker-anchor observations at 849 period/time anchors, producing 82,650 complete defender-rank rows. Home attacked in 4,785 observations and Away in 3,480; period counts were 6,278 and 1,987. Simultaneous attackers per anchor had median 10, IQR 9–10, and range 8–10. All retained observations contained D1–D10 once, ten unique defending outfield players, complete smoothed support, and no interpolation.

Concurrent attacker path had median 2.788 m, IQR 1.680–4.964 m, and range 0–17.717 m. Prior attacker path had median 2.816 m and IQR 1.727–4.914 m. Rank-distance medians increased from 5.843 m at D1 to 38.177 m at D10; the full governed table is machine-readable.

## Primary defender-relative movement

Attacker-path coefficients and frozen 95% intervals were:

| Rank/region | Coefficient (m/m) | 95% interval |
|---|---:|---:|
| D1 | 0.13397 | [0.10172, 0.16786] |
| D2 | 0.04909 | [0.02043, 0.07808] |
| D3 | 0.03697 | [0.01438, 0.05809] |
| D4 | 0.04930 | [0.02377, 0.07284] |
| D5 | 0.04385 | [0.01638, 0.07095] |
| D6 | 0.03958 | [0.01282, 0.06568] |
| D7 | 0.05397 | [0.02730, 0.08044] |
| D8 | 0.05014 | [0.02425, 0.07668] |
| D9 | 0.06836 | [0.04226, 0.09402] |
| D10 | 0.08274 | [0.05340, 0.11047] |
| Near D1–D3 | 0.07334 | [0.05138, 0.09600] |
| Middle D4–D7 | 0.04668 | [0.02608, 0.06615] |
| Far D8–D10, descriptive | 0.06708 | [0.04422, 0.09063] |
| **Near minus middle** | **0.02667** | **[0.01134, 0.04487]** |

All 2,000 bootstrap replicates were valid. The primary contrast was positive and its interval was strictly above zero.

## Extreme-movement robustness

The frozen 12.198443079831405 m threshold excluded 89 anchors (1.0768%). The trimmed near-minus-middle estimate was 0.02446 [0.00901, 0.04025], positive and 91.71% of the untrimmed magnitude. Both frozen robustness gates passed.

## Secondary deformation and directional descriptions

The secondary endpoint-deformation near coefficient was 0.06463 [0.04121, 0.08909], middle was 0.05110 [0.02895, 0.07340], and descriptive far was 0.05348 [0.02885, 0.07769]. Near minus middle was 0.01354 [0.00425, 0.02428], so deformation was **supportive** under the frozen descriptive rule. It did not classify the experiment.

Directional quantities remained descriptive. Median attacker-axis-parallel focal-relative displacement declined from +0.281 m at D1 to −0.325 m at D10; orthogonal and radial tables are retained without hypothesis tests or tactical labels. Four attacker anchors had undefined attacker axes under the frozen numerical rule.

## Prior movement context and limitations

The model included every frozen prior control. Medians (IQRs) were 2.816 m (3.187) for attacker path, 2.323 m (3.153) for defensive-centroid path, 2.006 m (1.948) for focal-relative path, and 3.229 m (2.911) for mean movement of the other nine defenders.

Conditioning does not eliminate every common-motion confounder. All rank coefficients were positive, far exceeded middle descriptively, and the near advantage was concentrated at D1 rather than forming a monotonic distance gradient. These are important counterweights to a broad “local response” narrative.

## Frozen decision

Every criterion passed: valid execution/construct QC, positive near-minus-middle point estimate, strictly positive 95% interval, positive trimmed estimate, and at least 50% retained magnitude. The exact status is therefore:

> **GAME 1 CONCURRENT GEOMETRY DEVELOPMENT COHERENT**

Strongest permitted statement:

> In Metrica Game 1, greater attacker movement within fixed two-second intervals was associated with a stronger concurrent focal-relative defender-movement coefficient among the three nearest defender ranks than among the four middle ranks after conditioning on the prospectively specified pre-interval movement context.

This is observational Game 1 development evidence. It does not establish attacker causation, reaction, latency, influence, attention, responsibility, assignment, marking, tracking, pinning, dragging, covering, handoff, defensive error, space or opportunity creation, tactical success, player quality, gravity, value, or elimination of all confounding.

## Artifacts

The machine-readable result SHA-256 is `cd782fcf31b1822e397297278f43b82dcb9ce270318786c1db8c3d57d52e0da0`. Two pre-closure defects were mechanical only: an output-variable typo stopped before loading data, and NumPy-array JSON serialization stopped after computation. A final numerical-compliance review replaced an algebraically equivalent normal-equation bootstrap solve with the protocol-named `numpy.linalg.lstsq(..., rcond=None)` sufficient-statistic implementation; the governed result above is from that compliant rerun. On identical samples, weights, and bootstrap draws, the maximum preliminary-versus-governed bootstrap coefficient difference was $1.04\times10^{-14}$ and the maximum interval-endpoint difference was $5.01\times10^{-15}$; no interval changed materially and the status remained COHERENT. No scientific rule changed.
