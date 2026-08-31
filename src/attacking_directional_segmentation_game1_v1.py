"""Execute frozen attacker-only directional segmentation v1 on Metrica Game 1."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from infrastructure import kloppy_metrica_adapter as metrica  # noqa: E402

FPS = 25.0
MIN25 = 10
MIN10 = 4
TOL = 1e-12
FIXTURE_SIGMA_MPS = 1.0
NOISE_FIXTURE_SIGMA_MPS = 0.25
NOISE_FIXTURE_TOLERANCE = 1e-12


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cost(prefix: np.ndarray, prefix2: np.ndarray, a: int, b: int, sigma: float) -> float:
    n = b - a
    s = prefix[b] - prefix[a]
    ss = prefix2[b] - prefix2[a]
    return float((ss - float(s @ s) / n) / (sigma * sigma))


def _key(value: float, cps: tuple[int, ...]) -> tuple[float, int, tuple[int, ...]]:
    return (value, len(cps), cps)


def exact_dp(x: np.ndarray, sigma: float, minimum: int) -> tuple[int, ...]:
    """Quadratic oracle used only on bounded fixtures/tests."""
    n = len(x); penalty = 3.0 * math.log(n)
    p = np.vstack([np.zeros(2), np.cumsum(x, axis=0)])
    p2 = np.r_[0.0, np.cumsum(np.sum(x * x, axis=1))]
    best: list[tuple[float, tuple[int, ...]] | None] = [None] * (n + 1)
    best[0] = (-penalty, ())
    for b in range(minimum, n + 1):
        candidates = []
        for a in range(0, b - minimum + 1):
            if best[a] is None:
                continue
            value = best[a][0] + cost(p, p2, a, b, sigma) + penalty
            cps = best[a][1] + ((a,) if a else ())
            candidates.append((value, cps))
        if candidates:
            best[b] = min(candidates, key=lambda z: _key(*z))
    if best[n] is None:
        raise ValueError("No legal partition")
    return best[n][1]


def exact_pelt(x: np.ndarray, sigma: float, minimum: int) -> tuple[int, ...]:
    """Exact PELT with jump=1 and governed deterministic tie handling."""
    n = len(x); penalty = 3.0 * math.log(n)
    p = np.vstack([np.zeros(2), np.cumsum(x, axis=0)])
    p2 = np.r_[0.0, np.cumsum(np.sum(x * x, axis=1))]
    states: dict[int, tuple[float, tuple[int, ...]]] = {0: (-penalty, ())}
    admissible: list[int] = []
    for b in range(minimum, n + 1):
        entrant = b - minimum
        if entrant in states:
            admissible.append(entrant)
        candidates: list[tuple[int, float, tuple[int, ...]]] = []
        for a in admissible:
            if b - a < minimum:
                continue
            prior, old = states[a]
            cps = old + ((a,) if a else ())
            value = prior + cost(p, p2, a, b, sigma) + penalty
            candidates.append((a, value, cps))
        if not candidates:
            continue
        _, value, cps = min(candidates, key=lambda z: _key(z[1], z[2]))
        states[b] = (value, cps)
        # Standard PELT pruning condition for a squared-error cost with K=0.
        admissible = [a for a, v, _ in candidates if v <= value + penalty + TOL]
    if n not in states:
        raise ValueError("No legal partition")
    return states[n][1]


def smooth_velocity(raw_xy: np.ndarray, times: np.ndarray, frames: np.ndarray) -> dict:
    kernel = np.ones(7, dtype=np.float64) / 7.0
    sm = np.column_stack([np.convolve(raw_xy[:, j], kernel, mode="valid") for j in range(2)])
    st = times[3:-3]; sf = frames[3:-3]
    vel = np.diff(sm, axis=0) / np.diff(st)[:, None]
    return {"positions": sm, "position_times": st, "position_frames": sf, "velocity": vel,
            "velocity_times": st[1:], "velocity_frames": sf[1:]}


def fixture_trace(kind: str, hz: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    t = np.arange(0.0, 6.0 + 1.0 / hz / 2, 1.0 / hz)
    v = np.zeros((len(t), 2)); v[:] = (3.0, 0.0)
    if kind == "low_speed": v[:] = (0.8, 0.3)
    elif kind == "low_motion": v[:] = (0.2, 0.1)
    elif kind == "brief_slowdown": v[(t >= 2.9) & (t <= 3.1)] = (1.0, 0.0)
    elif kind == "speed_change": v[t >= 3.0] = (4.0, 0.0); v[t < 3.0] = (2.0, 0.0)
    elif kind == "turn": v[t >= 3.0] = (0.0, 3.0)
    elif kind == "stop_restart": v[(t >= 2.0) & (t < 3.0)] = (0.0, 0.0)
    elif kind == "arc":
        theta = np.pi * t / 12.0; v = 3 * np.column_stack([np.cos(theta), np.sin(theta)])
    elif kind == "wander":
        theta = np.floor(t / 1.2) * np.pi / 3; v = 2.5 * np.column_stack([np.cos(theta), np.sin(theta)])
    pos = np.zeros_like(v)
    pos[1:] = np.cumsum(v[:-1] / hz, axis=0)
    pos += 0.005 * np.column_stack([np.sin(2*np.pi*1.7*t), np.cos(2*np.pi*1.3*t)])
    return pos, t, np.arange(len(t)), v


def run_fixtures(sigma: float = FIXTURE_SIGMA_MPS) -> list[dict]:
    if sigma != FIXTURE_SIGMA_MPS:
        raise ValueError("Algorithm fixtures require frozen sigma=1.0 m/s")
    rows = []
    expected = {"constant": 0, "low_speed": 0, "low_motion": 0, "brief_slowdown": 0,
                "speed_change": 1, "turn": 1, "stop_restart": 2}
    for hz, minimum in ((25, 10), (10, 4)):
        for kind in [*expected, "arc", "wander"]:
            pos, t, f, _ = fixture_trace(kind, hz)
            q = smooth_velocity(pos, t, f)
            cps = exact_pelt(q["velocity"], sigma, minimum)
            oracle = exact_dp(q["velocity"], sigma, minimum)
            required = kind in expected
            pass_count = (len(cps) == expected[kind]) if required else True
            target_ok = True
            if kind in {"speed_change", "turn"} and cps:
                target_ok = abs(q["position_times"][cps[0]] - 3.0) <= 1.0/hz + 1e-9
            if kind == "stop_restart" and len(cps) == 2:
                target_ok = all(abs(q["position_times"][c] - target) <= 1.0/hz + 1e-9 for c, target in zip(cps, (2., 3.)))
            low_motion_ok = True
            if kind == "low_motion":
                fitted_mean = q["velocity"].mean(axis=0)
                low_motion_ok = float(np.linalg.norm(fitted_mean)) < 0.5
            rows.append({"fixture": kind, "hz": hz, "change_count": len(cps),
                         "change_times_s": ";".join(f"{q['position_times'][c]:.6f}" for c in cps),
                         "oracle_match": cps == oracle, "required_pass": bool(pass_count and target_ok and low_motion_ok and cps == oracle)})
        # Invalid gap: separately smoothed blocks, no crossing by construction.
        pos, t, f, _ = fixture_trace("constant", hz)
        valid = ~((t >= 2.8-1e-12) & (t <= 3.2+1e-12))
        starts = np.flatnonzero(valid & ~np.r_[False, valid[:-1]])
        ends = np.flatnonzero(valid & ~np.r_[valid[1:], False])
        counts = []
        for a, b in zip(starts, ends):
            q = smooth_velocity(pos[a:b+1], t[a:b+1], f[a:b+1])
            counts.append(len(exact_pelt(q["velocity"], sigma, minimum)))
        rows.append({"fixture":"invalid_gap", "hz":hz, "change_count":sum(counts),
                     "change_times_s":"", "oracle_match":True,
                     "required_pass":len(counts)==2 and counts==[0,0]})
    return rows


def run_noise_estimator_fixture() -> dict:
    """Algebraic fixture for the frozen radial scale estimator only."""
    radial_difference = 2.0 * NOISE_FIXTURE_SIGMA_MPS * np.sqrt(np.log(2.0))
    velocity = np.zeros((101, 2), dtype=np.float64)
    velocity[1::2, 0] = radial_difference
    estimate, source_pairs = radial_sigma([{"velocity": velocity}])
    error = abs(estimate - NOISE_FIXTURE_SIGMA_MPS)
    return {"fixture": "radial_noise_estimator", "generating_sigma_mps": NOISE_FIXTURE_SIGMA_MPS,
            "estimated_sigma_mps": estimate, "absolute_error_mps": error,
            "absolute_tolerance_mps": NOISE_FIXTURE_TOLERANCE,
            "source_pairs": source_pairs, "pass": error <= NOISE_FIXTURE_TOLERANCE}


@dataclass
class Block:
    block_id: str
    player_key: str
    team_key: str
    period: int
    raw_frames: np.ndarray
    raw_times: np.ndarray
    raw_xy: np.ndarray
    q25: dict


def load_blocks() -> tuple[list[Block], pd.DataFrame, dict]:
    home, away = metrica.game1_paths(ROOT)
    idx = metrica.read_provider_frame_index(home)
    ds = metrica.load_dataset(home, away)
    traces: dict[str, list[pd.DataFrame]] = {}
    meta: dict[str, tuple[str, bool]] = {}
    for chunk in metrica.iter_canonical_polars_chunks(ds, idx, frames_per_chunk=2500):
        selected = chunk.filter((chunk["entity_type"] == "player") & (~chunk["is_goalkeeper"]))
        # Avoid making Arrow an undeclared execution dependency.
        q = pd.DataFrame(selected.to_dicts())
        for key, g in q.groupby("player_key", sort=False):
            traces.setdefault(key, []).append(g[["period","frame_id_provider","time_match_s","x_m","y_m","support_state","coordinate_valid"]])
            meta[key] = (str(g["team_key"].iloc[0]), bool(g["is_goalkeeper"].iloc[0]))
    blocks: list[Block] = []; ledger = []; block_no = 0
    for key in sorted(traces):
        tr = pd.concat(traces[key], ignore_index=True)
        team = meta[key][0]; player = key.rsplit(":",1)[1]
        for period, g in tr.groupby("period", sort=True):
            g = g.sort_values("time_match_s").copy(); frame = g.frame_id_provider.astype(int)
            valid = g.coordinate_valid & g.support_state.eq("observed") & g[["x_m","y_m"]].notna().all(axis=1)
            if team == "metrica:Home" and player == "10" and int(period) == 1:
                valid &= ~frame.between(2911,2945)
            if (team, player, int(period)) in {("metrica:Home","3",2),("metrica:Away","22",2)}:
                valid[:] = False
            continuity = frame.diff().eq(1) & g.time_match_s.diff().sub(.04).abs().le(1e-9)
            starts = valid & (~valid.shift(fill_value=False) | ~continuity)
            ids = starts.cumsum()
            for _, b in g[valid].groupby(ids[valid], sort=True):
                block_no += 1; bid = f"B{block_no:04d}"
                raw_xy=b[["x_m","y_m"]].to_numpy(float); times=b.time_match_s.to_numpy(float); frames=b.frame_id_provider.astype(int).to_numpy()
                q25=smooth_velocity(raw_xy,times,frames) if len(b)>=8 else {"velocity":np.empty((0,2))}
                nv=len(q25["velocity"])
                status="segmented" if nv>=20 else ("untested_short_regime" if nv>=10 else "unsupported_short_block")
                ledger.append({"block_id":bid,"player_key":key,"team_key":team,"period":int(period),"raw_rows":len(b),"velocity_observations_25hz":nv,"status":status,
                               "raw_start_s":float(times[0]),"raw_end_s":float(times[-1])})
                if nv>=20:
                    blocks.append(Block(bid,key,team,int(period),frames,times,raw_xy,q25))
    provenance=metrica.canonical_provenance(ds,home,away)
    return blocks,pd.DataFrame(ledger),provenance


def radial_sigma(blocks: list[dict]) -> tuple[float,int]:
    d=[np.linalg.norm(np.diff(q["velocity"],axis=0),axis=1) for q in blocks if len(q["velocity"])>=2]
    values=np.concatenate(d)
    return float(np.median(values)/(2*np.sqrt(np.log(2)))), int(len(values))


def geometry(q: dict, a: int, b: int) -> dict:
    pos=q["positions"][a:b+1]; inc=np.diff(pos,axis=0); lengths=np.linalg.norm(inc,axis=1)
    path=float(lengths.sum()); delta=pos[-1]-pos[0]; disp=float(np.linalg.norm(delta)); vel=q["velocity"][a:b]
    speed=np.linalg.norm(vel,axis=1); valid=(lengths>1e-9)&(speed>=.5)
    headings=np.arctan2(inc[:,1],inc[:,0])[valid]
    if len(headings)>=2:
        changes=np.diff(np.unwrap(headings)); signed=float(np.degrees(changes.sum())); absolute=float(np.degrees(np.abs(changes).sum()))
    else: signed=absolute=0.0
    if disp>1e-9:
        u=delta/disp; closest=pos[0]+np.outer((pos-pos[0])@u,u); chord=float(np.linalg.norm(pos-closest,axis=1).max())
    else: chord=float(np.linalg.norm(pos-pos[0],axis=1).max())
    moving=vel[speed>=.5]; resultant=float(np.linalg.norm(np.mean(moving/np.linalg.norm(moving,axis=1)[:,None],axis=0))) if len(moving) else np.nan
    meanv=vel.mean(axis=0)
    return {"duration_s":float(b-a)/25.0,"path_m":path,"displacement_m":disp,"delta_x_m":float(delta[0]),"delta_y_m":float(delta[1]),
            "peak_speed_mps":float(speed.max()),"mean_speed_mps":float(speed.mean()),"mean_vx_mps":float(meanv[0]),"mean_vy_mps":float(meanv[1]),
            "mean_velocity_magnitude_mps":float(np.linalg.norm(meanv)),"displacement_path_ratio":disp/path if path>1e-9 else np.nan,
            "max_chord_deviation_m":chord,"signed_heading_change_deg":signed,"absolute_heading_change_deg":absolute,"moving_direction_resultant":resultant,
            "within_regime_sse":float(np.sum((vel-meanv)**2))}


def segment_blocks(blocks: list[Block], sigma: float) -> tuple[pd.DataFrame,pd.DataFrame]:
    regimes=[]; boundaries=[]
    for block in blocks:
        q=block.q25; cps=exact_pelt(q["velocity"],sigma,MIN25); cuts=(0,*cps,len(q["velocity"]))
        for cp in cps:
            boundaries.append({"block_id":block.block_id,"player_key":block.player_key,"period":block.period,"boundary_index":cp,"boundary_time_s":float(q["position_times"][cp]),"frequency_hz":25})
        for j,(a,b) in enumerate(zip(cuts[:-1],cuts[1:]),1):
            row=geometry(q,a,b); low=row["mean_velocity_magnitude_mps"]<.5
            row.update({"regime_id":f"{block.block_id}-R{j:04d}","block_id":block.block_id,"player_key":block.player_key,"team_key":block.team_key,"period":block.period,
                        "start_index":a,"end_index_exclusive":b,"start_frame":int(q["position_frames"][a]),"end_frame":int(q["position_frames"][b]),
                        "start_s":float(q["position_times"][a]),"end_s":float(q["position_times"][b]),"regime_type":"low_motion_regime" if low else "directional_movement_segment",
                        "valid_support":True})
            regimes.append(row)
    r=pd.DataFrame(regimes)
    r["diag_short"]=r.duration_s<=1.5+1e-9; r["diag_tiny_path"]=r.path_m<=1+1e-9; r["diag_tiny_displacement"]=r.displacement_m<=.5+1e-9
    r["diag_fragmentation_any"]=r[["diag_short","diag_tiny_path","diag_tiny_displacement"]].any(axis=1)
    r["diag_long"]=r.duration_s>=8-1e-9; r["diag_low_displacement_path_ratio"]=r.displacement_path_ratio<=.5+1e-12
    r["diag_direction_change"]=(r.path_m>=3-1e-9)&(r.absolute_heading_change_deg>=180-1e-9)
    r["diag_merging_any"]=r[["diag_long","diag_low_displacement_path_ratio","diag_direction_change"]].any(axis=1)
    r["diag_lower_speed_meaningful_displacement"]=(r.peak_speed_mps<5.5)&(r.displacement_m>=3)
    r["diag_resultant_le_0_5"]=r.moving_direction_resultant<=.5
    return r,pd.DataFrame(boundaries)


def resample10(block: Block) -> dict:
    q=block.q25; t=q["position_times"]; start=float(t[0]); end=float(t[-1])
    grid=start+0.1*np.arange(int(np.floor((end-start)/.1+1e-10))+1)
    pos=np.column_stack([np.interp(grid,t,q["positions"][:,j]) for j in range(2)])
    return {"positions":pos,"position_times":grid,"position_frames":np.full(len(grid),-1),"velocity":np.diff(pos,axis=0)/.1,
            "velocity_times":grid[1:],"velocity_frames":np.full(max(0,len(grid)-1),-1)}


def sensitivity10(blocks: list[Block], boundaries25: pd.DataFrame) -> tuple[pd.DataFrame,dict,float,int]:
    qmap={b.block_id:resample10(b) for b in blocks}; sigma,nscale=radial_sigma(list(qmap.values()))
    rows=[]
    for b in blocks:
        q=qmap[b.block_id]
        if len(q["velocity"])<8: continue
        for cp in exact_pelt(q["velocity"],sigma,MIN10):
            rows.append({"block_id":b.block_id,"player_key":b.player_key,"period":b.period,"boundary_index":cp,"boundary_time_s":float(q["position_times"][cp]),"frequency_hz":10})
    b10=pd.DataFrame(rows); matched=[]; nmatch=0
    for bid in sorted(set(boundaries25.block_id)|set(b10.block_id)):
        a=boundaries25.loc[boundaries25.block_id.eq(bid),"boundary_time_s"].to_numpy(); c=b10.loc[b10.block_id.eq(bid),"boundary_time_s"].to_numpy()
        if len(a) and len(c):
            costmat=np.abs(a[:,None]-c[None,:]); ii,jj=linear_sum_assignment(costmat)
            for i,j in zip(ii,jj):
                ok=costmat[i,j]<=.20+1e-12; nmatch+=int(ok)
                matched.append({"block_id":bid,"boundary_25_s":a[i],"boundary_10_s":c[j],"absolute_offset_s":costmat[i,j],"accepted":bool(ok)})
    n25=len(boundaries25); n10=len(b10); precision=nmatch/n10 if n10 else 1.; recall=nmatch/n25 if n25 else 1.; f1=2*precision*recall/(precision+recall) if precision+recall else 0.
    metrics={"boundaries_25hz":n25,"boundaries_10hz":n10,"matched_boundaries":nmatch,"unmatched_25hz":n25-nmatch,"unmatched_10hz":n10-nmatch,
             "precision":precision,"recall":recall,"f1":f1,"segment_count_25hz":n25+len(blocks),"segment_count_10hz":n10+len(blocks)}
    metrics["absolute_segment_count_difference_rate"]=abs(metrics["segment_count_10hz"]-metrics["segment_count_25hz"])/metrics["segment_count_25hz"]
    accepted=[x["absolute_offset_s"] for x in matched if x["accepted"]]
    metrics["median_matched_offset_s"]=float(np.median(accepted)) if accepted else None; metrics["max_matched_offset_s"]=float(np.max(accepted)) if accepted else None
    return pd.DataFrame(matched),metrics,sigma,nscale


def quantiles(s: pd.Series) -> dict:
    q=s.quantile([.25,.5,.75])
    return {"min":float(s.min()),"q25":float(q.loc[.25]),"median":float(q.loc[.5]),"q75":float(q.loc[.75]),"max":float(s.max())}


def main(output: Path) -> None:
    output.mkdir(parents=True,exist_ok=True)
    blocks,ledger,provenance=load_blocks(); sigma,nscale=radial_sigma([b.q25 for b in blocks])
    fixtures=pd.DataFrame(run_fixtures())
    noise_fixture=run_noise_estimator_fixture()
    if not fixtures.required_pass.all() or not noise_fixture["pass"]: raise RuntimeError("Frozen fixture failure")
    regimes,b25=segment_blocks(blocks,sigma); matches,sens,sigma10,nscale10=sensitivity10(blocks,b25)
    frag_n=int(regimes.diag_fragmentation_any.sum()); merge_n=int(regimes.diag_merging_any.sum()); den=len(regimes)
    frag=frag_n/den; merging=merge_n/den
    hard=bool(fixtures.required_pass.all() and noise_fixture["pass"] and regimes.valid_support.all() and (regimes.duration_s>=.4-1e-9).all())
    gates={"hard_qc":hard,"fragmentation":frag<=.33776+1e-12,"merging_direction":merging<=.0397+1e-12,
           "frequency_precision":sens["precision"]>=.9-1e-12,"frequency_recall":sens["recall"]>=.9-1e-12,"frequency_f1":sens["f1"]>=.9-1e-12,
           "frequency_segment_count":sens["absolute_segment_count_difference_rate"]<=.10+1e-12}
    if all(gates.values()): classification="A"
    elif not hard or ((frag>=.4222-1e-12) and not gates["merging_direction"]): classification="C"
    else: classification="B"
    supported_seconds=float(sum(len(b.q25["velocity"])/25 for b in blocks))
    summary={"classification":classification,"eligible_players":int(regimes.player_key.nunique()),"eligible_segmented_blocks":len(blocks),"supported_duration_s":supported_seconds,
             "total_regimes":den,"directional_movement_regimes":int(regimes.regime_type.eq("directional_movement_segment").sum()),"low_motion_regimes":int(regimes.regime_type.eq("low_motion_regime").sum()),
             "noise_scale_25hz_mps":sigma,"noise_scale_source_pairs_25hz":nscale,"noise_scale_10hz_mps":sigma10,"noise_scale_source_pairs_10hz":nscale10,
             "duration_s":quantiles(regimes.duration_s),"path_m":quantiles(regimes.path_m),"displacement_m":quantiles(regimes.displacement_m),"mean_speed_mps":quantiles(regimes.mean_speed_mps),
             "fragmentation":{"numerator":frag_n,"denominator":den,"rate":frag,"historical_baseline":.4222,"frozen_limit":.33776,"pass":gates["fragmentation"]},
             "merging_direction":{"numerator":merge_n,"denominator":den,"rate":merging,"historical_numerator":763,"historical_denominator":38651,"historical_rate":763/38651,"frozen_limit":.0397,"pass":gates["merging_direction"]},
             "frequency_sensitivity":sens,"gates":gates,"regimes_per_supported_minute":den/(supported_seconds/60),
             "lower_speed_peak_below_5_5_count":int((regimes.peak_speed_mps<5.5).sum()),"lower_speed_peak_below_5_5_displacement_ge_3_count":int(regimes.diag_lower_speed_meaningful_displacement.sum()),
             "moving_direction_resultant_le_0_5_count":int(regimes.diag_resultant_le_0_5.sum())}
    ledger.to_csv(output/"support_blocks.csv",index=False); fixtures.to_csv(output/"fixtures.csv",index=False); regimes.to_csv(output/"regimes.csv",index=False,float_format="%.12g")
    (output/"noise_estimator_fixture.json").write_text(json.dumps(noise_fixture,indent=2,sort_keys=True)+"\n")
    b25.to_csv(output/"boundaries_25hz.csv",index=False,float_format="%.12g"); matches.to_csv(output/"boundary_matches_10hz.csv",index=False,float_format="%.12g")
    (output/"results.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    manifest={"protocol":"docs/protocols/attacking_directional_segmentation_v1.md","protocol_sha256":sha256(ROOT/"docs/protocols/attacking_directional_segmentation_v1.md"),
              "source_sha256":sha256(Path(__file__)),"canonical_provenance":provenance,"scientific_output_files":["support_blocks.csv","fixtures.csv","noise_estimator_fixture.json","regimes.csv","boundaries_25hz.csv","boundary_matches_10hz.csv","results.json"]}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,default=ROOT/"outputs/attacking_directional_segmentation_game1_v1")
    args=parser.parse_args(); main(args.output)
