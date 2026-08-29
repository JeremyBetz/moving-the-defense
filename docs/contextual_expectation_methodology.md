# Contextual-Expectation Methodology and Provenance

Phase 5A borrows the general expected-versus-observed architecture from existing sports-tracking work while deliberately testing a much narrower scalar target. The project does not claim to invent expected defensive movement.

| Precedent | What it did | Relevance to Phase 5A | Borrowed | Deliberately not borrowed |
|---|---|---|---|---|
| Wu and Swartz (2023) | Predicted a defender's two-dimensional velocity in soccer context and compared actual with typical predicted velocity to construct a defensive-anticipation measure. | Direct precedent for learning observable defensive movement expectation from tracking context. | Expected-versus-observed framing and contextual prediction as a prerequisite to interpretation. | Their semantic “anticipation” metric, velocity target, “fast is better” premise, and player evaluation. |
| Le et al. (2017) | Used deep imitation learning on professional soccer tracking to generate counterfactual defensive “ghosts” relative to league/team behavior. | Establishes soccer defensive ghosting and contextual trajectory baselines as prior art. | The principle that actual movement can be compared with a context-conditioned reference. | Deep imitation learning, full trajectories, counterfactual “should,” team fine-tuning, and effectiveness evaluation. |
| Victor et al. (2021) | Compared deep team-sport trajectory models with simple extrapolation and found that beating linear extrapolation on soccer average displacement can be difficult. | Motivates a strong simple-model ladder and a prospective complexity gate. | Simple baselines before complex forecasting; held-out predictive improvement must be material. | Sparse-output graph/attention models and full-trajectory loss in Phase 5A. |
| Penn, Donnelly, and Bhatt (2023/2025) | Used an interpretable ARMAX-style player-motion model with ball movement to reconstruct continuous football tracking from sparse broadcast observations. | Shows that player/ball motion can support transparent dynamic prediction without beginning from deep multi-agent models. | Interpretable causal history, player/ball covariates, and explicit error auditing. | Broadcast interpolation, bidirectional reconstruction, Hungarian assignment, and future observations; Phase 5A forbids future-informed interpolation. |
| Teranishi et al. (2022) | Predicted multi-agent soccer trajectories with a graph variational recurrent model and compared actual versus predicted trajectories inside an off-ball scoring-opportunity valuation framework. | Direct precedent for later use of predicted movement as a reference in off-ball valuation. | Separation of observed movement, expected movement, and downstream value. | GVRNN, probabilistic multi-agent trajectories, attacker valuation, salary validation, and scoring-opportunity attribution. |
| Groom et al. (2026) | Inferred role-conditioned defensive assignments and used contextual ghosting for counterfactual off-ball defensive evaluation at corners. | A close future neighbor for context-aware defensive references. | Reminder that context and role can matter after a simple baseline is established. | HMM assignments, responsibility, role inference, ghosting, counterfactual value, and corner-specific semantics. |

## Methodological boundary

The Phase 5A target is not future x/y position, velocity, ADE/FDE, or a joint trajectory. It is the already validated scalar five-second focal-relative path. Frozen protocol v1.0 prospectively fixes Ridge regression and a transparent B0–B4 history/context ladder to test reproducible match-held-out predictive value before any richer relational or nonlinear architecture is considered. Its estimand is retrospective and conditional on an eligible uninterrupted target interval; it is not an online forecast.

The distinction among prediction, residual, response, and value is strict:

1. **Prediction:** expected scalar geometry conditional on pre-cutoff observables within the retrospectively eligible evaluation population.
2. **Residual:** observed minus predicted geometry under the current model.
3. **Defensive response:** a later behavioral interpretation requiring independent validation.
4. **Attacker association/attribution:** later links requiring opponent/action context and alternatives.
5. **Value:** a downstream consequence, not a property of prediction error alone.

Probabilistic and multimodal trajectory prediction remains a later methodological direction because real player futures can be non-unique. It is unnecessary for the initial scalar feasibility question and would obscure whether recent focal, collective, ball, or spatial context provides the predictive information.

Full source records are retained in the [bibliography](../references/bibliography.md). This provenance summary informs protocol design only; no model has been fitted.
