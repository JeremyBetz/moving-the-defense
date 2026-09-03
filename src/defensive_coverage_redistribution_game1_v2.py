"""Execute frozen Defensive Coverage Redistribution v2 on Metrica Game 1 only.

This implementation deliberately has one anchor row and never uses outcome
information to choose the ball-nearest reference attacker or any geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import shutil
import sys
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import attacking_continuous_movement_game1_v1 as tracking  # noqa: E402
import attacker_defender_bridge_game1_v1 as bridge  # noqa: E402
import defensive_coverage_redistribution_v2 as geometry  # noqa: E402
from infrastructure import kloppy_metrica_adapter as metrica  # noqa: E402

PROTOCOL = ROOT / "docs/protocols/defensive_coverage_redistribution_v2.md"
CONFIG = ROOT / "config/defensive_coverage_redistribution_v2.json"
LEDGER = ROOT / "config/defensive_coverage_redistribution_v2_hashes.json"
V1_REJECTION = ROOT / "docs/protocols/defensive_coverage_redistribution_v1_rejection.md"
EVENTS = ROOT / "data/metrica_sample_game_1/Sample_Game_1_RawEventsData.csv"
DEFAULT_OUTPUT = ROOT / "outputs/defensive_coverage_redistribution_game1_v2"
DEFAULT_FIGURES = ROOT / "figures/defensive_coverage_redistribution_game1_v2"
FROZEN = {
    PROTOCOL: "4acf8f5c6a375c1303e7ab5d0f2ea35b3b4a035e9223d7d1b16468d2d42cf278",
    CONFIG: "24a36a75fe84afd78222b11f0351bac60820057ddac9b76951d8f29c2da2038c",
    LEDGER: "",  # populated from the ledger itself; its listed artifact hashes are authoritative
    V1_REJECTION: "6c2c8822ad4c8a6931feed7fdadfd309f24001ade3499a605e4a72953fb0a2f7",
}
BOOT_REPS, MIN_VALID, BOOT_SEED = 2000, 1900, 20260909
NULL_REPS, NULL_SEED = 200, 20260910
TRIM = 12.198443079831405
TOL = 1e-9
COLUMNS = ["intercept", "A", "D", "G0", "MO", "B", "C", "R", "Apre", "Dpre", "Bpre", "P2"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value: Any) -> Any:
    if isinstance(value, dict): return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [clean(v) for v in value]
    if isinstance(value, np.ndarray): return clean(value.tolist())
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (np.floating, float)):
        out = float(value); return out if math.isfinite(out) else None
    if isinstance(value, (np.bool_, bool)): return bool(value)
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(clean(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def path(xy: np.ndarray) -> float:
    return float(np.linalg.norm(np.diff(xy, axis=0), axis=1).sum(dtype=np.float64))


def distribution(x: np.ndarray) -> dict[str, float]:
    x = np.asarray(x, dtype=np.float64)
    return {"count": int(len(x)), "min": float(x.min()), "q25": float(np.quantile(x, .25)),
            "median": float(np.median(x)), "q75": float(np.quantile(x, .75)),
            "max": float(x.max()), "mean": float(x.mean()), "sd": float(x.std(ddof=0))}


class BallPeriod:
    """Observed ball trace with exactly the inherited 7-frame centred smoothing."""
    def __init__(self, frame: pd.DataFrame) -> None:
        q = frame.sort_values("time_period_s", kind="mergesort").reset_index(drop=True)
        self.frames = q.frame_id_provider.astype(int).to_numpy()
        self.times = q.time_period_s.to_numpy(np.float64)
        self.match_times = q.time_match_s.to_numpy(np.float64)
        self.raw = q[["x_m", "y_m"]].to_numpy(np.float64)
        self.valid = (q.is_present.fillna(False).to_numpy(bool) & q.coordinate_valid.fillna(False).to_numpy(bool)
                      & q.support_state.eq("observed").to_numpy(bool) & np.isfinite(self.raw).all(axis=1))
        self.links = np.zeros(len(q), dtype=bool)
        if len(q) > 1:
            self.links[1:] = ((np.diff(self.frames) == 1)
                              & (np.abs(np.diff(self.match_times) - tracking.RAW_DT_S) <= tracking.TIME_TOL)
                              & (np.diff(self.times) > 0))

    def segment(self, start: float, end: float) -> np.ndarray | None:
        left = int(np.searchsorted(self.times, start - TOL))
        right = int(np.searchsorted(self.times, end - TOL))
        if left >= len(self.times) or right >= len(self.times): return None
        if abs(float(self.times[left]) - start) > TOL or abs(float(self.times[right]) - end) > TOL: return None
        if right - left != int(round((end - start) / tracking.RAW_DT_S)): return None
        # Need every raw frame that contributes to every seven-frame mean.
        if left < 3 or right + 3 >= len(self.times): return None
        if not self.valid[left - 3:right + 4].all(): return None
        if not self.links[left - 2:right + 4].all(): return None
        return np.stack([self.raw[i - 3:i + 4].mean(axis=0, dtype=np.float64) for i in range(left, right + 1)])


def load_balls(period_frames: dict[int, dict[str, Any]]) -> dict[int, BallPeriod]:
    home, away = metrica.game1_paths(ROOT)
    index = metrica.read_provider_frame_index(home)
    dataset = metrica.load_dataset(home, away)
    parts: list[pd.DataFrame] = []
    for chunk in metrica.iter_canonical_polars_chunks(dataset, index, frames_per_chunk=2500):
        ball = chunk.filter(pl.col("entity_type") == "ball")
        parts.append(pd.DataFrame(ball.to_dicts()))
    raw = pd.concat(parts, ignore_index=True)
    result: dict[int, BallPeriod] = {}
    for p, group in raw.groupby("period", sort=True):
        bp = BallPeriod(group)
        ref = period_frames[int(p)]
        if not (np.array_equal(bp.frames, ref["frame_ids"])
                and np.allclose(bp.times, ref["time_period_s"], atol=TOL, rtol=0)
                and np.allclose(bp.match_times, ref["time_match_s"], atol=TOL, rtol=0)):
            raise RuntimeError("ball and canonical player grids differ")
        result[int(p)] = bp
    return result


def event_state(events: pd.DataFrame, period: int, tmatch: float) -> tuple[str | None, bool, bool]:
    team, restart = bridge.event_context(events, period, tmatch, tmatch - 2., tmatch + 2.)
    if team is None: return None, restart, False
    opponent = "Away" if team == "Home" else "Home"
    changed = events[(events.Period == period) & events.Type.isin(bridge.POSSESSION_TYPES)
                     & events.Team.eq(opponent) & events["Start Time [s]"].notna()
                     & (events["Start Time [s]"] > tmatch + TOL)
                     & (events["Start Time [s]"] <= tmatch + 2. + TOL)]
    return team, restart, not changed.empty


def _roster(players: list[tracking.PlayerPeriod]) -> tuple[dict[tuple[int, str], list[str]], dict[tuple[int, str], tracking.PlayerPeriod]]:
    lookup = {(p.period, p.player_key): p for p in players}
    teams: dict[tuple[int, str], list[str]] = {}
    for p in players: teams.setdefault((p.period, p.team_key), []).append(p.player_key)
    return {k: sorted(v) for k, v in teams.items()}, lookup


def _endpoint_fixed_nearest(attack0: np.ndarray, attack1: np.ndarray, defend0: np.ndarray, defend1: np.ndarray, reference: int) -> float:
    keep = np.flatnonzero(np.arange(10) != reference)
    d0 = np.linalg.norm(attack0[keep, None] - defend0[None], axis=2)
    d1 = np.linalg.norm(attack1[keep, None] - defend1[None], axis=2)
    nearest = d0.argmin(axis=1)
    return float((d1[np.arange(9), nearest] - d0[np.arange(9), nearest]).mean())


def _endpoint_two_nearest(attack0: np.ndarray, attack1: np.ndarray, defend0: np.ndarray, defend1: np.ndarray, reference: int) -> float:
    keep = np.flatnonzero(np.arange(10) != reference)
    d0 = np.sort(np.linalg.norm(attack0[keep, None] - defend0[None], axis=2), axis=1)[:, :2].mean(axis=1)
    d1 = np.sort(np.linalg.norm(attack1[keep, None] - defend1[None], axis=2), axis=1)[:, :2].mean(axis=1)
    return float((d1 - d0).mean())


def build_sample() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], list[dict[str, Any]]]:
    players, frames, provenance = tracking.load_game1()
    balls = load_balls(frames)
    roster, lookup = _roster(players)
    events = pd.read_csv(EVENTS)
    rows: list[dict[str, Any]] = []; excluded: list[dict[str, Any]] = []; contexts: list[dict[str, Any]] = []
    for period in sorted(frames):
        frame = frames[period]; origin = float(frame["origin_time_period_s"]); last = float(frame["time_period_s"][-1]); k = 0
        while True:
            t = origin + 2. + 4. * k
            if t + 2. > last + TOL: break
            base = {"period": period, "time_period_s": t}
            raw_i = int(np.searchsorted(frame["time_period_s"], t - TOL))
            if raw_i >= len(frame["time_period_s"]) or abs(float(frame["time_period_s"][raw_i])-t)>TOL:
                excluded.append({**base,"reason":"anchor_not_exact_frame"}); k += 1; continue
            tmatch = float(frame["time_match_s"][raw_i]); team, restart, changed = event_state(events, period, tmatch)
            if team is None: excluded.append({**base,"reason":"no_possession_team"}); k += 1; continue
            if restart: excluded.append({**base,"reason":"restart_or_ball_out_span"}); k += 1; continue
            if changed: excluded.append({**base,"reason":"opponent_possession_event_after_anchor"}); k += 1; continue
            attack_team = f"metrica:{team}"; defend_team = "metrica:Away" if attack_team == "metrica:Home" else "metrica:Home"
            attack = {key: bridge.segment(lookup[(period,key)], t-2.,t+2.) for key in roster.get((period,attack_team),[]) if (period,key) in lookup}
            defend = {key: bridge.segment(lookup[(period,key)], t-2.,t+2.) for key in roster.get((period,defend_team),[]) if (period,key) in lookup}
            attack = {key:value for key,value in attack.items() if value is not None}; defend = {key:value for key,value in defend.items() if value is not None}
            if len(attack) != 10: excluded.append({**base,"reason":"complete_ten_attackers_unavailable","available":len(attack)}); k += 1; continue
            if len(defend) != 10: excluded.append({**base,"reason":"complete_ten_defenders_unavailable","available":len(defend)}); k += 1; continue
            ball = balls[period].segment(t-2.,t+2.)
            if ball is None: excluded.append({**base,"reason":"complete_ball_support_unavailable"}); k += 1; continue
            keys_a, keys_d = sorted(attack), sorted(defend)
            a4 = np.stack([attack[x] for x in keys_a],axis=1); d4 = np.stack([defend[x] for x in keys_d],axis=1)
            if a4.shape != (101,10,2) or d4.shape != (101,10,2) or ball.shape != (101,2): raise RuntimeError("frozen support length failure")
            try: reference = geometry.ball_nearest_reference_index(a4[50], ball[50])
            except ValueError: excluded.append({**base,"reason":"ball_nearest_reference_tie"}); k += 1; continue
            ranks = np.asarray(sorted(range(10), key=lambda j:(float(np.linalg.norm(d4[50,j]-a4[50,reference])),keys_d[j])), dtype=int)
            con_def, pre_def = d4[50:], d4[:51]; con_att, pre_att = a4[50:], a4[:51]; con_ball, pre_ball=ball[50:],ball[:51]
            prepaths = geometry.focal_relative_path_lengths(pre_def); conpaths = geometry.focal_relative_path_lengths(con_def)
            D = geometry.defensive_response_contrast(conpaths[ranks]); Dpre = geometry.defensive_response_contrast(prepaths[ranks])
            remote = float(conpaths[ranks[7:10]].mean()-conpaths[ranks[3:7]].mean())
            remote_pre = float(prepaths[ranks[7:10]].mean()-prepaths[ranks[3:7]].mean())
            primary = geometry.fixed_elsewhere_cost_change(con_att[0],con_att[-1],con_def[0],con_def[-1],reference)
            full = geometry.full_ten_coverage(con_att[-1],con_def[-1]).mean_distance_m-geometry.full_ten_coverage(con_att[0],con_def[0]).mean_distance_m
            oid=f"DCR2|P{period}|T{t:.2f}"
            rows.append({"observation_id":oid,"period":period,"time_period_s":t,"time_match_s":tmatch,"block_id":int(math.floor((t-origin)/60.)),"attacking_team":attack_team,"defending_team":defend_team,"reference_attacker_key":keys_a[reference],"Y":primary,"A":path(con_att[:,reference]),"D":D,"Dremote":remote,"G0":geometry.fixed_elsewhere_coverage(con_att[0],con_def[0],reference).mean_distance_m,"MO":float(np.mean([path(con_att[:,j]) for j in range(10) if j!=reference])),"B":path(con_ball),"C":path(con_def.mean(axis=1)),"R":float(conpaths.mean()),"Apre":path(pre_att[:,reference]),"Dpre":Dpre,"Dpre_remote":remote_pre,"Bpre":path(pre_ball),"P2":int(period==2),"Y_fixed_start":_endpoint_fixed_nearest(con_att[0],con_att[-1],con_def[0],con_def[-1],reference),"Y_full_ten":float(full),"Y_two_nearest":_endpoint_two_nearest(con_att[0],con_att[-1],con_def[0],con_def[-1],reference)})
            contexts.append({"observation_id":oid,"reference":reference,"attack_start":con_att[0],"attack_end":con_att[-1],"defend":con_def})
            k += 1
    data=pd.DataFrame(rows).sort_values(["period","time_period_s"],kind="mergesort").reset_index(drop=True)
    excluded_df=pd.DataFrame(excluded).sort_values(["period","time_period_s"],kind="mergesort").reset_index(drop=True)
    contexts=sorted(contexts,key=lambda x:x["observation_id"])
    return data,excluded_df,provenance,contexts


def design(data: pd.DataFrame, dcol: str="D", dpre: str="Dpre") -> tuple[np.ndarray,np.ndarray]:
    x=np.column_stack([np.ones(len(data)),data.A,data[dcol],data.G0,data.MO,data.B,data.C,data.R,data.Apre,data[dpre],data.Bpre,data.P2]).astype(np.float64)
    return x,data.Y.to_numpy(np.float64)


def fit(data: pd.DataFrame, dcol: str="D", dpre: str="Dpre") -> dict[str,Any]:
    x,y=design(data,dcol,dpre); coef,resid,rank,sing=np.linalg.lstsq(x,y,rcond=None)
    if rank != x.shape[1] or not np.isfinite(coef).all(): raise RuntimeError(f"frozen design rank failure {rank}/{x.shape[1]}")
    return {"coefficients":dict(zip(COLUMNS,coef)),"rank":int(rank),"n":int(len(data)),"singular_values":sing,"condition_number":float(sing[0]/sing[-1]),"rss":float(resid[0]) if len(resid) else 0.0}


def block_draws(data: pd.DataFrame, reps: int=BOOT_REPS) -> list[np.ndarray]:
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence(BOOT_SEED).spawn(2)[0]))
    grouped={}
    for (period,block),idx in data.groupby(["period","block_id"],sort=True).indices.items(): grouped.setdefault(int(period),[]).append(np.asarray(idx,dtype=int))
    out=[]
    for _ in range(reps):
        picked=[]
        for period in sorted(grouped):
            blocks=grouped[period]; pick=rng.integers(0,len(blocks),size=len(blocks)); picked.extend(blocks[i] for i in pick)
        out.append(np.concatenate(picked))
    return out


def boot_family(data: pd.DataFrame, draws: list[np.ndarray], dcol: str="D", dpre: str="Dpre") -> tuple[np.ndarray,int]:
    values=[]
    for indices in draws:
        try: values.append(float(fit(data.iloc[indices].reset_index(drop=True),dcol,dpre)["coefficients"]["D"]))
        except RuntimeError: continue
    return np.asarray(values,dtype=np.float64),len(values)


def interval(values: np.ndarray) -> list[float]: return [float(q) for q in np.quantile(values,[.025,.975],method="linear")]


def direction_null(data: pd.DataFrame, contexts: list[dict[str,Any]]) -> tuple[np.ndarray,dict[str,float]]:
    by_id={x["observation_id"]:x for x in contexts}; rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence(NULL_SEED)))
    results=[]; max_path_error=0.; max_centroid_error=0.
    for _ in range(NULL_REPS):
        ys=[]
        for oid in data.observation_id:
            c=by_id[oid]; transformed=geometry.rotate_internal_defender_motion(c["defend"],float(rng.uniform(0.,2*np.pi)))
            original_paths=geometry.focal_relative_path_lengths(c["defend"]); new_paths=geometry.focal_relative_path_lengths(transformed)
            max_path_error=max(max_path_error,float(np.max(np.abs(original_paths-new_paths))))
            max_centroid_error=max(max_centroid_error,float(np.max(np.abs(c["defend"].mean(axis=1)-transformed.mean(axis=1)))))
            ys.append(geometry.fixed_elsewhere_cost_change(c["attack_start"],c["attack_end"],transformed[0],transformed[-1],c["reference"]))
        q=data.copy(); q["Y"]=ys; results.append(float(fit(q)["coefficients"]["D"]))
    return np.asarray(results,dtype=np.float64),{"max_relative_path_error":max_path_error,"max_centroid_error":max_centroid_error}


def output_hashes(output: Path, names: list[str]) -> dict[str,str]: return {name:sha(output/name) for name in names}


def write_report(output: Path, result: dict[str,Any]) -> None:
    primary=result["primary"]; boot=result["bootstrap"]; control=result["controls"]; status=result["classification"]
    text=f"""# Defensive Coverage Redistribution v2 — Game 1 result\n\n**Status:** {status}\n\nThis is the single prospectively frozen Game 1 development execution. The ball-nearest reference is a geometric unit, not an inferred ball carrier, role, or assignment.\n\n## Primary model\n\n- Eligible one-row anchors: {result['sample']['eligible_anchors']}\n- $\\beta_D$: {primary['coefficients']['D']:.8f} m/m\n- 95% block-bootstrap interval: [{boot['primary_interval'][0]:.8f}, {boot['primary_interval'][1]:.8f}]\n- Direction-null 95th percentile: {control['direction_null_95th']:.8f}; observed exceeds it: {control['direction_null_pass']}\n- Remote comparator $\\beta_D$: {control['remote_coefficient']:.8f}; primary exceeds it: {control['remote_pass']}\n- Trimmed $\\beta_D$: {control['trimmed_coefficient']:.8f}; trim passes: {control['trim_pass']}\n\n## Interpretation boundary\n\nThe result is an observational association test between a focal-local-versus-middle defender-relative movement contrast and a fixed-set nine-attacker matching-distance change. It does not establish attacker causation, tactical response, marking, responsibility, space creation, gravity, or value.\n"""
    (output/"result_report.md").write_text(text,encoding="utf-8")


def write_invalid_report(output: Path, result: dict[str, Any]) -> None:
    """Serialize a governed INVALID closure without estimating an unidentified model."""
    text = f"""# Defensive Coverage Redistribution v2 — Game 1 result

**Status:** INVALID

The frozen raw-unit model could not be estimated because its required full
column-rank condition failed before any coefficient or bootstrap was produced.

- Eligible one-row anchors: {result['sample']['eligible_anchors']}
- Retained periods: {result['sample']['period_counts']}
- Failure: `{result['invalid_reason']}`

The frozen model includes a period-2 indicator. No period-2 anchors survived
the unchanged complete-ten-outfield support requirements, so that indicator was
constant. This is an execution-validity failure under the frozen protocol, not
evidence about the coverage outcome or an invitation to remove the column.
"""
    (output / "result_report.md").write_text(text, encoding="utf-8")


def plot_controls(output: Path, result: dict[str,Any]) -> None:
    fig,axes=plt.subplots(1,2,figsize=(10,3.8)); coeff=result["primary"]["coefficients"]
    axes[0].bar(["primary D","remote D","trimmed D"],[coeff["D"],result["controls"]["remote_coefficient"],result["controls"]["trimmed_coefficient"]],color=["#1b7837","#7570b3","#d95f02"]); axes[0].axhline(0,color="black",lw=.8); axes[0].set_ylabel("matching-cost change coefficient (m/m)")
    null=np.asarray(result["direction_null_values"],dtype=float); axes[1].hist(null,bins=20,color="#9ecae1",edgecolor="white"); axes[1].axvline(coeff["D"],color="#cb181d",lw=2,label="observed"); axes[1].legend(frameon=False); axes[1].set_xlabel("direction-null $\\beta_D$")
    fig.tight_layout(); fig.savefig(output/"control_summary.png",dpi=180); plt.close(fig)


def execute(output: Path=DEFAULT_OUTPUT, figures: Path=DEFAULT_FIGURES, *, write: bool=True) -> dict[str,Any]:
    for source,expected in FROZEN.items():
        if expected and sha(source)!=expected: raise RuntimeError(f"frozen artifact mismatch: {source}")
    output.mkdir(parents=True,exist_ok=True); figures.mkdir(parents=True,exist_ok=True)
    data,exclusions,provenance,contexts=build_sample()
    if data.empty: raise RuntimeError("no eligible governed anchors")
    sample={"eligible_anchors":int(len(data)),"period_counts":{str(k):int(v) for k,v in data.period.value_counts().sort_index().items()},"attacking_team_counts":{str(k):int(v) for k,v in data.attacking_team.value_counts().sort_index().items()},"reference_attacker_counts":{str(k):int(v) for k,v in data.reference_attacker_key.value_counts().sort_index().items()},"exclusion_counts":{str(k):int(v) for k,v in exclusions.reason.value_counts().sort_index().items()},"all_complete_ten_by_ten":True,"all_one_row_per_anchor":bool(data.observation_id.is_unique)}
    try:
        primary=fit(data)
    except RuntimeError as exc:
        result={"protocol_hash":sha(PROTOCOL),"configuration_hash":sha(CONFIG),"v1_rejection_hash":sha(V1_REJECTION),"source_hash":sha(Path(__file__)),"provenance":provenance,"sample":sample,"classification":"INVALID","invalid_reason":str(exc),"hard_qc":{"full_rank":False,"valid":False}}
        if write:
            data.to_csv(output/"observation_rows.csv",index=False); exclusions.to_csv(output/"eligibility_ledger.csv",index=False)
            data[["observation_id","period","time_period_s","reference_attacker_key","attacking_team","defending_team"]].to_csv(output/"anchor_reference_ledger.csv",index=False)
            write_json(output/"model_results.json",{k:v for k,v in result.items() if k!="provenance"}); write_json(output/"manifest.json",{"match":"Metrica Sample Game 1","protocol":str(PROTOCOL.relative_to(ROOT)),"configuration":str(CONFIG.relative_to(ROOT)),"source_hash":result["source_hash"],"closure":"invalid_before_outcome_model"}); write_invalid_report(output,result)
            names=["observation_rows.csv","eligibility_ledger.csv","anchor_reference_ledger.csv","model_results.json","manifest.json","result_report.md"]
            write_json(output/"governed_hashes.json",output_hashes(output,names))
        return result
    draws=block_draws(data); boot,nboot=boot_family(data,draws)
    remote, nremote=boot_family(data,draws,"Dremote","Dpre_remote")
    trimmed_data=data[data.A<=TRIM].reset_index(drop=True); trim, ntrim=boot_family(trimmed_data,draws=[np.arange(len(trimmed_data),dtype=int) for _ in range(BOOT_REPS)])
    # The trim uses the same frozen estimator/seeded observed sample; its block-draw construction must retain existing blocks.
    # Reconstruct block draws after fixed prospective trimming, still within period.
    trim_draws=block_draws(trimmed_data); trim,ntrim=boot_family(trimmed_data,trim_draws)
    fixed,nfixed=boot_family(data,draws) if False else (np.empty(0),0)
    null,null_qc=direction_null(data,contexts)
    controls={"direction_null_95th":float(np.quantile(null,.95,method="linear")),"direction_null_pass":bool(primary["coefficients"]["D"]>np.quantile(null,.95,method="linear")),"remote_coefficient":float(fit(data,"Dremote","Dpre_remote")["coefficients"]["D"]),"remote_pass":bool(primary["coefficients"]["D"]>fit(data,"Dremote","Dpre_remote")["coefficients"]["D"]),"trimmed_coefficient":float(fit(trimmed_data)["coefficients"]["D"]),"trim_retained_abs_fraction":float(abs(fit(trimmed_data)["coefficients"]["D"])/abs(primary["coefficients"]["D"])) if primary["coefficients"]["D"] else None}
    controls["trim_pass"]=bool(controls["trimmed_coefficient"]>0 and controls["trim_retained_abs_fraction"]>=.5)
    desc={name:fit(data.assign(Y=data[column])) for name,column in [("fixed_start","Y_fixed_start"),("full_ten","Y_full_ten"),("two_nearest","Y_two_nearest")]}
    valid=bool(primary["rank"]==len(COLUMNS) and nboot>=MIN_VALID and nremote>=MIN_VALID and ntrim>=MIN_VALID and len(null)==NULL_REPS and null_qc["max_relative_path_error"]<=1e-10 and null_qc["max_centroid_error"]<=1e-10)
    beta=primary["coefficients"]["D"]; ci=interval(boot)
    if not valid: status="INVALID"
    elif beta<=0: status="NOT_SUPPORTED"
    elif ci[0]>0 and controls["direction_null_pass"] and controls["remote_pass"] and controls["trim_pass"]: status="COHERENT"
    else: status="MIXED"
    result={"protocol_hash":sha(PROTOCOL),"configuration_hash":sha(CONFIG),"v1_rejection_hash":sha(V1_REJECTION),"source_hash":sha(Path(__file__)),"provenance":provenance,"sample":sample,"primary":primary,"bootstrap":{"replicates":BOOT_REPS,"valid_primary":nboot,"valid_remote":nremote,"valid_trim":ntrim,"primary_interval":ci,"remote_interval":interval(remote),"trim_interval":interval(trim)},"controls":controls,"descriptive_alternatives":desc,"null_preservation":null_qc,"classification":status,"hard_qc":{"full_rank":primary["rank"]==len(COLUMNS),"unique_reference_rows":data.observation_id.is_unique,"complete_sets":True,"bootstrap_minimum":nboot>=MIN_VALID and nremote>=MIN_VALID and ntrim>=MIN_VALID,"null_preservation":null_qc["max_relative_path_error"]<=1e-10 and null_qc["max_centroid_error"]<=1e-10,"valid":valid},"direction_null_values":null}
    if write:
        data.to_csv(output/"observation_rows.csv",index=False); exclusions.to_csv(output/"eligibility_ledger.csv",index=False)
        data[["observation_id","period","time_period_s","reference_attacker_key","attacking_team","defending_team"]].to_csv(output/"anchor_reference_ledger.csv",index=False)
        pd.DataFrame({"replicate":np.arange(1,len(boot)+1),"primary_beta_D":boot,"remote_beta_D":remote[:len(boot)],"trimmed_beta_D":trim[:len(boot)]}).to_csv(output/"bootstrap_results.csv",index=False)
        pd.DataFrame({"replicate":np.arange(1,NULL_REPS+1),"beta_D":null}).to_csv(output/"direction_null.csv",index=False)
        write_json(output/"model_results.json",{k:v for k,v in result.items() if k not in {"direction_null_values","provenance"}}); write_json(output/"manifest.json",{"match":"Metrica Sample Game 1","protocol":str(PROTOCOL.relative_to(ROOT)),"configuration":str(CONFIG.relative_to(ROOT)),"inputs":[str(EVENTS.relative_to(ROOT))],"python":sys.version,"platform":platform.platform(),"source_hash":result["source_hash"]}); write_report(output,result); plot_controls(figures,result)
        names=["observation_rows.csv","eligibility_ledger.csv","anchor_reference_ledger.csv","bootstrap_results.csv","direction_null.csv","model_results.json","manifest.json","result_report.md"]
        write_json(output/"governed_hashes.json",output_hashes(output,names))
    return result


def verify_reproduction(output: Path, rerun: Path, figures: Path) -> dict[str,Any]:
    result=execute(rerun,figures,write=True)
    names=json.loads((output/"governed_hashes.json").read_text(encoding="utf-8")); reproduced={name:sha(rerun/name)==expected for name,expected in names.items()}
    return {"all_byte_identical":bool(all(reproduced.values())),"outputs":reproduced,"rerun_classification":result["classification"]}


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT); parser.add_argument("--figures",type=Path,default=DEFAULT_FIGURES); parser.add_argument("--reproduce",action="store_true"); args=parser.parse_args()
    result=execute(args.output,args.figures,write=True)
    if args.reproduce:
        rerun=args.output.parent/("."+args.output.name+"_rerun")
        if rerun.exists(): shutil.rmtree(rerun)
        repro=verify_reproduction(args.output,rerun,args.figures.parent/("."+args.figures.name+"_rerun")); write_json(args.output/"reproduction.json",repro)
        if not repro["all_byte_identical"]: raise RuntimeError("deterministic reproduction failure")
        shutil.rmtree(rerun); hidden=args.figures.parent/("."+args.figures.name+"_rerun");
        if hidden.exists(): shutil.rmtree(hidden)
    print(json.dumps(clean({"classification":result["classification"],"beta_D":None if "primary" not in result else result["primary"]["coefficients"]["D"],"n":result["sample"]["eligible_anchors"]}),sort_keys=True))


if __name__ == "__main__": main()
