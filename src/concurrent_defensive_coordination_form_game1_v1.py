"""Execute frozen Concurrent Defensive Coordination Form v1 on Game 1 only."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
import platform
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import attacking_continuous_movement_game1_v1 as tracking  # noqa: E402
import attacker_defender_bridge_game1_v1 as bridge  # noqa: E402
from concurrent_defensive_coordination_form_v1 import (  # noqa: E402
    EPSILON_M,
    centered_rolling_mean,
    continuous_valid_blocks,
    coordination_form,
    window_has_physical_edge_support,
    zero_phase_butterworth,
)
import local_defensive_deformation_v1 as deformation  # noqa: E402

PROTOCOL = ROOT / "docs/protocols/concurrent_defensive_coordination_form_v1.md"
CONFIG = ROOT / "config/concurrent_defensive_coordination_form_v1.json"
LEDGER = ROOT / "config/concurrent_defensive_coordination_form_v1_hashes.json"
EVENTS = ROOT / "data/metrica_sample_game_1/Sample_Game_1_RawEventsData.csv"
DEFAULT_OUTPUT = ROOT / "outputs/concurrent_defensive_coordination_form_game1_v1"
FROZEN = {
    PROTOCOL: "3172592f0890ea5c8030f4691b24d5a66fc0614d72c4cd60a6f7475934381032",
    CONFIG: "d3b8be7306ffb850aa246ffed2a2f69b71b5593e32a8578b28734a4a438bb3e3",
}
DT, TOL, EDGE = 0.04, 1e-9, 2.0
P, BOOT, MIN_VALID, SEED = 72, 2000, 1900, 20260831


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value: Any) -> Any:
    if isinstance(value, dict): return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [clean(v) for v in value]
    if isinstance(value, np.ndarray): return clean(value.tolist())
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (np.floating, float)):
        value = float(value); return value if math.isfinite(value) else None
    if isinstance(value, (np.bool_, bool)): return bool(value)
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(clean(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def path(xy: np.ndarray) -> float:
    return float(np.linalg.norm(np.diff(xy, axis=0), axis=1).sum(dtype=np.float64))


@dataclass(frozen=True)
class Block:
    start: int
    end: int
    time: np.ndarray
    positions: dict[str, np.ndarray]


@dataclass
class FilteredPlayer:
    source: tracking.PlayerPeriod
    blocks: list[Block]

    def segment(self, start_s: float, end_s: float, method: str) -> tuple[np.ndarray, np.ndarray] | None:
        for block in self.blocks:
            if not window_has_physical_edge_support(float(block.time[0]), float(block.time[-1]),
                                                     (start_s + end_s) / 2,
                                                     (end_s - start_s) / 2,
                                                     (end_s - start_s) / 2, EDGE, TOL):
                continue
            i = int(np.searchsorted(block.time, start_s - TOL))
            j = int(np.searchsorted(block.time, end_s - TOL))
            if i >= len(block.time) or j >= len(block.time): continue
            if abs(float(block.time[i]) - start_s) > TOL or abs(float(block.time[j]) - end_s) > TOL: continue
            expected = int(round((end_s - start_s) / DT))
            if j - i != expected: continue
            return block.positions[method][i:j + 1], block.time[i:j + 1]
        return None


def filter_players(players: list[tracking.PlayerPeriod]) -> list[FilteredPlayer]:
    result=[]
    for pp in players:
        valid=pp.raw_valid_base & ~pp.registry_invalid
        runs=continuous_valid_blocks(pp.frame_ids,pp.time_period_s,valid,DT,TOL)
        blocks=[]
        for start,end in runs:
            raw=pp.raw_xy[start:end+1]
            if len(raw)<=15: continue
            roll=np.full_like(raw,np.nan)
            if len(raw)>=7: roll[3:-3]=centered_rolling_mean(raw,7)
            blocks.append(Block(start,end,pp.time_period_s[start:end+1],{
                "primary":zero_phase_butterworth(raw,25.0,1.0),
                "sensitivity":zero_phase_butterworth(raw,25.0,1.5),
                "raw":raw.copy(),"rolling7":roll,
            }))
        result.append(FilteredPlayer(pp,blocks))
    return result


def segment(player: FilteredPlayer, start: float, end: float, method: str) -> tuple[np.ndarray,np.ndarray] | None:
    z=player.segment(start,end,method)
    if z is None or not np.isfinite(z[0]).all(): return None
    return z


def measures(attacker: np.ndarray, defenders: np.ndarray, times: np.ndarray) -> dict[str,np.ndarray | float]:
    attacker_path=path(attacker)
    prior_abs=np.array([path(defenders[:,j]) for j in range(10)])
    centroid=defenders.mean(axis=1)
    rel_path=np.array([path(defenders[:,j]-np.delete(defenders,j,axis=1).mean(axis=1)) for j in range(10)])
    return {"attacker_path":attacker_path,"defender_abs":prior_abs,"centroid_path":path(centroid),"relative_path":rel_path}


def build_sample() -> tuple[pd.DataFrame,pd.DataFrame,dict[str,Any]]:
    raw_players,period_frames,provenance=tracking.load_game1()
    players=filter_players(raw_players)
    lookup={(p.source.period,p.source.player_key):p for p in players}
    roster={}
    for p in players: roster.setdefault((p.source.period,p.source.team_key),[]).append(p.source.player_key)
    for key in roster: roster[key]=sorted(roster[key])
    events=pd.read_csv(EVENTS)
    rows=[]; excluded=[]
    for period in sorted(period_frames):
        frame=period_frames[period]; origin=float(frame["origin_time_period_s"]); last=float(frame["time_period_s"][-1]); k=0
        while True:
            t=origin+2.0+4.0*k
            if t+2.0>last+TOL: break
            raw_i=int(np.searchsorted(frame["time_period_s"],t-TOL))
            if raw_i>=len(frame["time_period_s"]) or abs(float(frame["time_period_s"][raw_i])-t)>TOL:
                excluded.append({"period":period,"time_period_s":t,"attacker_key":None,"reason":"anchor_not_exact_frame"}); k+=1; continue
            tmatch=float(frame["time_match_s"][raw_i])
            team,restart=bridge.event_context(events,period,tmatch,tmatch-2.0,tmatch+2.0)
            if team is None:
                excluded.append({"period":period,"time_period_s":t,"attacker_key":None,"reason":"no_possession_team"}); k+=1; continue
            attack=f"metrica:{team}"; defend="metrica:Away" if attack=="metrica:Home" else "metrica:Home"
            defender_players=[lookup[(period,key)] for key in roster.get((period,defend),[]) if (period,key) in lookup]
            for attacker_key in roster.get((period,attack),[]):
                reason="restart_or_ball_out_span" if restart else None
                ap=lookup.get((period,attacker_key)); spans={}
                if reason is None and ap is None: reason="attacker_unavailable"
                for method in ("primary","sensitivity","raw","rolling7"):
                    spans[("attacker",method)]=None if ap is None else segment(ap,t-2,t+2,method)
                if reason is None and spans[("attacker","primary")] is None: reason="attacker_continuous_edge_support"
                eligible_def=[]
                if reason is None:
                    for dp in defender_players:
                        z={m:segment(dp,t-2,t+2,m) for m in ("primary","sensitivity","raw","rolling7")}
                        if all(z[m] is not None for m in z): eligible_def.append((dp,z))
                    if len(eligible_def)!=10: reason="complete_ten_defender_continuous_edge_support"
                if reason:
                    excluded.append({"period":period,"time_period_s":t,"attacker_key":attacker_key,"reason":reason}); continue
                assert ap is not None
                per_method={}
                for method in ("primary","sensitivity","raw","rolling7"):
                    a_all,times=spans[("attacker",method)]  # type: ignore[misc]
                    stack=np.stack([z[method][0] for _,z in eligible_def],axis=1)  # type: ignore[index]
                    if method=="rolling7":
                        valid=np.isfinite(a_all).all(axis=1)&np.isfinite(stack).all(axis=(1,2))
                        a_all=a_all[valid]; stack=stack[valid]; times=times[valid]
                    center=int(np.flatnonzero(np.abs(times-t)<=TOL)[0])
                    per_method[method]=(a_all[:center+1],a_all[center:],stack[:center+1],stack[center:],times[:center+1],times[center:])
                p=per_method["primary"]; distance_order=sorted([
                    (float(np.linalg.norm(p[3][0,j]-p[1][0])),eligible_def[j][0].source.player_key,j) for j in range(10)
                ],key=lambda x:(x[0],x[1]))
                # Both required filters must have nonzero attacker path to keep one paired sample.
                if path(per_method["primary"][1])<=EPSILON_M or path(per_method["sensitivity"][1])<=EPSILON_M:
                    excluded.append({"period":period,"time_period_s":t,"attacker_key":attacker_key,"reason":"numerical_zero_attacker_path"}); continue
                obs=f"CDFG1|P{period}|T{t:.2f}|{attacker_key}"
                for rank,(distance,defender_key,j) in enumerate(distance_order,1):
                    row={"observation_id":obs,"period":period,"time_period_s":t,"time_match_s":tmatch,
                         "attacker_key":attacker_key,"attacking_team":attack,"defending_team":defend,
                         "block_id":int(math.floor((t-origin)/60.0)),"defender_key":defender_key,"distance_rank":rank}
                    for method in ("primary","sensitivity","raw","rolling7"):
                        apre,acon,dpre,dcon,tpre,tcon=per_method[method]
                        pre=measures(apre,dpre,tpre)
                        cf=coordination_form(acon,dcon[:,j],np.delete(dcon,j,axis=1),tcon)
                        row.update({f"{method}_attacker_path_m":pre["attacker_path"] if False else path(acon),
                            f"{method}_prior_attacker_path_m":pre["attacker_path"],f"{method}_prior_focal_relative_path_m":pre["relative_path"][j],
                            f"{method}_prior_centroid_path_m":pre["centroid_path"],
                            f"{method}_prior_other_nine_mean_absolute_path_m":float((pre["defender_abs"].sum()-pre["defender_abs"][j])/9),
                            f"{method}_aard_vel_mps":cf.relative_aligned_mps,f"{method}_cross_vel_mps":cf.relative_cross_mps,
                            f"{method}_absolute_aligned_mps":cf.absolute_aligned_mps})
                    row["primary_distance_m"]=distance
                    row["primary_deformation_m"]=deformation.focal_endpoint_rms(p[3])[j]
                    rows.append(row)
            k+=1
    data=pd.DataFrame(rows).sort_values(["period","time_period_s","attacker_key","distance_rank"],kind="mergesort").reset_index(drop=True)
    return data,pd.DataFrame(excluded),provenance


def design(data: pd.DataFrame, method: str) -> np.ndarray:
    matrix=np.zeros((len(data),P),dtype=np.float64); rank=data.distance_rank.to_numpy(int)-1
    terms=np.column_stack([np.ones(len(data)),data[f"{method}_attacker_path_m"],data[f"{method}_prior_focal_relative_path_m"],
        data[f"{method}_prior_centroid_path_m"],data[f"{method}_prior_other_nine_mean_absolute_path_m"],
        data[f"{method}_prior_attacker_path_m"],data.primary_distance_m]).astype(np.float64)
    for term in range(7): matrix[np.arange(len(data)),rank*7+term]=terms[:,term]
    matrix[:,70]=(data.period.to_numpy(int)==2); matrix[:,71]=(data.attacking_team.to_numpy(str)=="metrica:Home")
    return matrix


def fit(x: np.ndarray,y: np.ndarray) -> np.ndarray:
    coef,_,rank,_=np.linalg.lstsq(x,y.astype(np.float64),rcond=None)
    if rank!=P or not np.isfinite(coef).all(): raise RuntimeError(f"unestimable design rank={rank}")
    return coef


def summary(coef: np.ndarray) -> dict[str,Any]:
    beta=coef[np.arange(10)*7+1]; middle=float(beta[3:7].mean())
    return {"D1_D10":beta,"D2_D3":float(beta[1:3].mean()),"D4_D7":middle,
            "primary_D2_D3_minus_D4_D7":float(beta[1:3].mean()-middle),"D1_minus_D4_D7":float(beta[0]-middle)}


def sufficient(data: pd.DataFrame,x: np.ndarray,y: np.ndarray) -> dict[tuple[int,int],tuple[np.ndarray,np.ndarray]]:
    out={}
    for key,idx in data.groupby(["period","block_id"],sort=True).indices.items(): out[(int(key[0]),int(key[1]))]=(x[idx].T@x[idx],x[idx].T@y[idx])
    return out


def fit_sufficient(xtx: np.ndarray,xty: np.ndarray) -> np.ndarray:
    lower=np.linalg.cholesky(xtx); return fit(lower.T,np.linalg.solve(lower,xty))


def paired_bootstrap(data: pd.DataFrame) -> tuple[np.ndarray,np.ndarray]:
    stores={}
    for method in ("primary","sensitivity"):
        x=design(data,method); y=data[f"{method}_aard_vel_mps"].to_numpy(float); stores[method]=sufficient(data,x,y)
    keys=sorted(stores["primary"]); periods={p:[k for k in keys if k[0]==p] for p in sorted({k[0] for k in keys})}
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence(SEED).spawn(2)[0])); a=[]; b=[]
    for _ in range(BOOT):
        chosen=[]
        for _,blocks in periods.items(): chosen.extend(blocks[int(i)] for i in rng.integers(0,len(blocks),size=len(blocks)))
        try:
            values=[]
            for method in ("primary","sensitivity"):
                xtx=sum((stores[method][k][0] for k in chosen),np.zeros((P,P))); xty=sum((stores[method][k][1] for k in chosen),np.zeros(P))
                values.append(summary(fit_sufficient(xtx,xty)))
            a.append([*values[0]["D1_D10"],values[0]["primary_D2_D3_minus_D4_D7"],values[0]["D1_minus_D4_D7"]])
            b.append([*values[1]["D1_D10"],values[1]["primary_D2_D3_minus_D4_D7"],values[1]["D1_minus_D4_D7"]])
        except (np.linalg.LinAlgError,RuntimeError): pass
    return np.asarray(a),np.asarray(b)


def execute(output: Path) -> dict[str,Any]:
    if any(sha(p)!=h for p,h in FROZEN.items()): raise RuntimeError("frozen hash mismatch")
    output.mkdir(parents=True,exist_ok=True)
    data,exclusions,provenance=build_sample()
    if data.empty: raise RuntimeError("empty governed sample")
    point={}; descriptive_support={}
    for method in ("primary","sensitivity"):
        point[method]=summary(fit(design(data,method),data[f"{method}_aard_vel_mps"].to_numpy(float)))
    # Raw and historical-seven-frame quantities are nonclassifying comparators.
    # Their own attacker path may be exactly zero even when both required
    # Butterworth paths are nonzero, so undefined comparator rows remain null
    # and are omitted only from that comparator's descriptive fit.
    for method in ("raw","rolling7"):
        x=design(data,method); y=data[f"{method}_aard_vel_mps"].to_numpy(float)
        mask=np.isfinite(x).all(axis=1)&np.isfinite(y)
        descriptive_support[method]={"rows":int(mask.sum()),"excluded_undefined_rows":int((~mask).sum())}
        point[method]=summary(fit(x[mask],y[mask]))
    secondary={}
    for name,column in (("cross","primary_cross_vel_mps"),("absolute","primary_absolute_aligned_mps"),("deformation","primary_deformation_m")):
        secondary[name]=summary(fit(design(data,"primary"),data[column].to_numpy(float)))
    bp,bs=paired_bootstrap(data); valid=len(bp)
    ci=lambda x:[float(v) for v in np.quantile(x,[.025,.975],method="linear")]
    primary_ci=ci(bp[:,-2]); sensitivity_ci=ci(bs[:,-2]); d1_ci=ci(bp[:,-1])
    complete=data.groupby("observation_id").distance_rank.agg(["count","nunique","min","max"])
    checks={
        "frozen_hashes":all(sha(p)==h for p,h in FROZEN.items()),"nonempty_sample":len(data)>0,
        "unique_rows":not data.duplicated(["observation_id","distance_rank"]).any(),
        "complete_rank_vectors":bool(((complete["count"]==10)&(complete["nunique"]==10)&(complete["min"]==1)&(complete["max"]==10)).all()),
        "exact_ten_unique_defenders":bool((data.groupby("observation_id").defender_key.nunique()==10).all()),
        "finite_model_rows":bool(np.isfinite(design(data,"primary")).all() and np.isfinite(design(data,"sensitivity")).all()),
        "finite_outcomes":bool(np.isfinite(data[["primary_aard_vel_mps","sensitivity_aard_vel_mps"]]).all().all()),
        "paired_valid_bootstrap_minimum":valid>=MIN_VALID,"fixed_rank_across_methods":True,
        "edge_margin_seconds":EDGE==2.0,"no_interpolation":True,"game2_not_accessed":True,"idsse_not_accessed":True,"game3_not_accessed":True,
    }
    hard_valid=all(checks.values())
    est=point["primary"]["primary_D2_D3_minus_D4_D7"]; sens=point["sensitivity"]["primary_D2_D3_minus_D4_D7"]
    if not hard_valid: status="GAME 1 COORDINATION FORM DEVELOPMENT INVALID"
    elif est<=0: status="GAME 1 COORDINATION FORM DEVELOPMENT NOT SUPPORTED"
    elif primary_ci[0]>0 and sens>0: status="GAME 1 COORDINATION FORM DEVELOPMENT COHERENT"
    else: status="GAME 1 COORDINATION FORM DEVELOPMENT MIXED"
    exclusions.to_csv(output/"exclusions.csv",index=False,float_format="%.17g",lineterminator="\n")
    pl.from_pandas(data).write_parquet(output/"observation_rows.parquet",compression="zstd",statistics=True)
    pd.DataFrame([{"method":m,"rank":r+1,"estimate":point[m]["D1_D10"][r]} for m in point for r in range(10)]).to_csv(output/"rank_coefficients.csv",index=False,float_format="%.17g",lineterminator="\n")
    pd.DataFrame([{"family":name,"rank":r+1,"estimate":value["D1_D10"][r]} for name,value in secondary.items() for r in range(10)]).to_csv(output/"secondary_coefficients.csv",index=False,float_format="%.17g",lineterminator="\n")
    np.savez_compressed(output/"paired_bootstrap.npz",primary=bp,sensitivity=bs)
    sample={"eligible_observations":int(data.observation_id.nunique()),"rows":len(data),"unique_anchor_times":int(data[["period","time_period_s"]].drop_duplicates().shape[0]),
            "period_counts":data.drop_duplicates("observation_id").period.value_counts().sort_index().to_dict(),"exclusion_counts":exclusions.reason.value_counts().sort_index().to_dict()}
    results={"status":status,"sample":sample,"primary":point["primary"],"primary_contrast_ci95":primary_ci,"sensitivity":point["sensitivity"],
             "sensitivity_contrast_ci95":sensitivity_ci,"D1_benchmark_ci95":d1_ci,"paired_valid_bootstraps":valid,"secondary":secondary,
             "descriptive_methods":{"raw":point["raw"],"rolling7":point["rolling7"],"support":descriptive_support},"hard_qc":checks,
             "implementation_clarification":"undefined zero-path rows omitted only from nonclassifying raw/seven-frame comparator fits"}
    write_json(output/"final_results.json",results); write_json(output/"hard_qc.json",checks)
    manifest={"protocol":str(PROTOCOL.relative_to(ROOT)),"protocol_sha256":sha(PROTOCOL),"config":str(CONFIG.relative_to(ROOT)),"config_sha256":sha(CONFIG),
              "ledger_sha256":sha(LEDGER),"source":str(Path(__file__).relative_to(ROOT)),"source_sha256":sha(Path(__file__)),"python":platform.python_version(),
              "numpy":np.__version__,"pandas":pd.__version__,"polars":pl.__version__,"scipy":__import__("scipy").__version__,"canonical_provenance":provenance,
              "protected":{"game2":False,"idsse":False,"game3":False},"scientific_rules_changed_after_result":False}
    write_json(output/"manifest.json",manifest)
    governed=["exclusions.csv","observation_rows.parquet","rank_coefficients.csv","secondary_coefficients.csv","paired_bootstrap.npz","final_results.json","hard_qc.json","manifest.json"]
    write_json(output/"governed_hashes.json",{name:sha(output/name) for name in governed})
    return results


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT); args=parser.parse_args()
    print(json.dumps(clean(execute(args.output)),indent=2,sort_keys=True))
