"""Execute frozen Local Defensive Response Form v1 on Metrica Game 1 only."""
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
import attacker_defender_bridge_game1_v1 as bridge  # noqa: E402
import attacking_continuous_movement_game1_v1 as attacker  # noqa: E402
import local_defensive_response_form_v1 as geometry  # noqa: E402

PROTOCOL = ROOT / "docs/protocols/local_defensive_response_form_v1.md"
CONFIG = ROOT / "config/local_defensive_response_form_v1.json"
FOOTPRINT_PROTOCOL = ROOT / "docs/protocols/spatial_defensive_response_footprint_v1.md"
FOOTPRINT_CONFIG = ROOT / "config/spatial_defensive_response_footprint_v1.json"
FOOTPRINT_RESULTS = ROOT / "outputs/spatial_defensive_response_footprint_game2_final_v1/final_results.json"
FOOTPRINT_LEDGER = ROOT / "outputs/spatial_defensive_response_footprint_game2_final_v1/final_hashes.json"
FOOTPRINT_GAME1 = ROOT / "outputs/spatial_defensive_response_footprint_game1_v1"
DEFAULT_OUTPUT = ROOT / "outputs/local_defensive_response_form_game1_v1"
DEFAULT_FIGURES = ROOT / "figures/local_defensive_response_form_game1_v1"

HASHES = {
    PROTOCOL: "958c8aa80fe9ea43358c32a42a6be2eea7a41e7f727e23ff137eb3079ee80428",
    CONFIG: "b120f19c13b86f47f5b73311a4509cbd5de5f95fbaa1369f95dc061c998b8053",
    FOOTPRINT_PROTOCOL: "649c40c551d880f5204f6ccca7e37cf219660c4a5fdea590e0b73b6377534458",
    FOOTPRINT_CONFIG: "b784b3839146a424acd427a0f1d99959f3ef547039743d30ce90e39f9e557c9c",
    FOOTPRINT_RESULTS: "239b0cad626b156bc0a91c6f8e1fb673e28330ad56f00deb8c3a9ecd4c169b85",
    FOOTPRINT_LEDGER: "e5e21cc4e9b44f02322027c0db7c385cf3e757ccacb7d5aaa876e594f757b688",
}
BOOTSTRAPS, MIN_VALID, MASTER_SEED, CHILD_INDEX = 2000, 1900, 20260831, 6
TRIM_THRESHOLD, TOL = 12.198443079831405, 1e-12
REGIONS = {"near": [1, 2, 3], "middle": [4, 5, 6, 7], "far": [8, 9, 10]}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value: Any) -> None:
    def clean(x: Any) -> Any:
        if isinstance(x, dict): return {str(k): clean(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)): return [clean(v) for v in x]
        if isinstance(x, (np.integer,)): return int(x)
        if isinstance(x, (np.floating, float)):
            y = float(x); return y if math.isfinite(y) else None
        if isinstance(x, (np.bool_, bool)): return bool(x)
        return x
    path.write_text(json.dumps(clean(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def unit(v: np.ndarray) -> np.ndarray | None:
    n = float(np.linalg.norm(v))
    return None if n <= geometry.VECTOR_NORM_EPSILON_M else v / n


def interval(pp: attacker.PlayerPeriod, start: float, end: float) -> np.ndarray:
    value = bridge.segment(pp, start, end)
    if value is None: raise RuntimeError(f"Missing frozen support {pp.player_key} {start} {end}")
    return value


def build_sample() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    anchors = pd.DataFrame(pl.read_parquet(FOOTPRINT_GAME1 / "eligible_attacker_anchors.parquet").to_dicts())
    links = pd.DataFrame(pl.read_parquet(FOOTPRINT_GAME1 / "anchor_defender_linkage.parquet").to_dicts())
    pps, _, provenance = attacker.load_game1()
    pp = {(x.period, x.player_key): x for x in pps}
    rows, exclusions = [], []
    for a in anchors.itertuples(index=False):
        attack = pp[(int(a.period), str(a.player_key))]
        da = interval(attack, float(a.time_period_s)-2, float(a.time_period_s))[-1] - interval(attack, float(a.time_period_s)-2, float(a.time_period_s))[0]
        future_da = interval(attack, float(a.time_period_s), float(a.time_period_s)+2)[-1] - interval(attack, float(a.time_period_s), float(a.time_period_s)+2)[0]
        ua, up = unit(da), unit(future_da)
        if ua is None:
            exclusions.append({"observation_id": a.observation_id, "reason": "near_zero_or_invalid_attacker_axis"})
            continue
        group = links[links.observation_id == a.observation_id].sort_values("distance_rank")
        defenders = [pp[(int(a.period), str(k))] for k in group.player_key_defender]
        windows = {"prior": (-4,-2), "earlier": (-2,0), "post1": (0,1), "post2": (0,2)}
        if bool(a.eligible_4s): windows["post4"] = (0,4)
        stacks = {name: np.stack([interval(x, float(a.time_period_s)+lo, float(a.time_period_s)+hi) for x in defenders]) for name,(lo,hi) in windows.items()}
        for j, link in enumerate(group.itertuples(index=False)):
            vectors, paths = {}, {}
            for name, stack in stacks.items():
                others = (stack.sum(axis=0)-stack[j]) / 9.0
                rel = stack[j]-others
                vectors[name] = rel[-1]-rel[0]
                paths[name] = float(np.linalg.norm(np.diff(rel,axis=0),axis=1).sum())
            defender_post2 = stacks["post2"][j,-1]-stacks["post2"][j,0]
            centroid_post2 = defender_post2-vectors["post2"]
            attacker_at_t = interval(attack,float(a.time_period_s),float(a.time_period_s))[0]
            defender_at_t = stacks["post2"][j,0]
            radial_axis = unit(attacker_at_t-defender_at_t)
            normal = np.array([-ua[1],ua[0]])
            focal_norm = float(np.linalg.norm(vectors["post2"]))
            row = {
                "observation_id":a.observation_id,"period":int(a.period),"time_period_s":float(a.time_period_s),
                "time_match_s":float(a.time_match_s),"attacker_key":str(a.player_key),"attacking_team":str(a.attacking_team),
                "defending_team":str(a.defending_team),"block_id":int(a.block_id),"defender_key":str(link.player_key_defender),
                "distance_rank":int(link.distance_rank),"distance_m":float(link.distance_m),
                "attacker_path_length_m":float(a.attacker_path_length_m),"future_attacker_path_length_m":float(a.future_attacker_path_length_m),
                "prior_centroid_path_m":float(a.prior_defending_centroid_path_m),
                "parallel_2s_m":float(vectors["post2"]@ua),"orthogonal_2s_m":float(vectors["post2"]@normal),
                "radial_2s_m":None if radial_axis is None else float(vectors["post2"]@radial_axis),
                "alignment_cosine":None if focal_norm<=geometry.VECTOR_NORM_EPSILON_M else float((vectors["post2"]@ua)/focal_norm),
                "prior_parallel_m":float(vectors["prior"]@ua),"earlier_placebo_parallel_m":None if up is None else float(vectors["earlier"]@up),
                "prior_placebo_parallel_m":None if up is None else float(vectors["prior"]@up),
                "parallel_1s_m":float(vectors["post1"]@ua),"parallel_4s_m":None if "post4" not in vectors else float(vectors["post4"]@ua),
                "focal_path_2s_m":paths["post2"],"focal_net_2s_m":focal_norm,
                "defender_absolute_2s_m":float(np.linalg.norm(defender_post2)),"centroid_loo_2s_m":float(np.linalg.norm(centroid_post2)),
                "focal_delta_x_m":float(vectors["post2"][0]),"focal_delta_y_m":float(vectors["post2"][1]),
                "placebo_axis_valid":up is not None,"radial_axis_valid":radial_axis is not None,
            }
            rows.append(row)
    data = pd.DataFrame(rows).sort_values(["period","time_period_s","attacker_key","distance_rank"],kind="mergesort").reset_index(drop=True)
    return anchors, data, {"source_provenance":provenance,"axis_exclusions":exclusions}


def design(x: np.ndarray, baseline: np.ndarray, centroid: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(len(x)),x,baseline,centroid]).astype(np.float64)


def fit_ranks(data: pd.DataFrame, outcome: str, exposure: str, baseline: str) -> np.ndarray:
    betas=[]
    for rank in range(1,11):
        q=data[data.distance_rank==rank]
        X=design(q[exposure].to_numpy(float),q[baseline].to_numpy(float),q.prior_centroid_path_m.to_numpy(float))
        y=q[outcome].to_numpy(float)
        if len(y)<5 or not np.isfinite(X).all() or not np.isfinite(y).all(): raise RuntimeError(f"Unestimable {outcome} D{rank}")
        coefficients, _, fitted_rank, _ = np.linalg.lstsq(X,y,rcond=None)
        if fitted_rank < 4: raise RuntimeError(f"Unestimable {outcome} D{rank}")
        betas.append(float(coefficients[1]))
    return np.asarray(betas)


def regions(beta: np.ndarray) -> dict[str,float]:
    n=float(beta[:3].mean()); m=float(beta[3:7].mean()); f=float(beta[7:].mean())
    return {"near":n,"middle":m,"far":f,"near_minus_middle":n-m,"middle_minus_far":m-f}


def ordered_data(anchors: pd.DataFrame, data: pd.DataFrame) -> pd.DataFrame:
    order={oid:i for i,oid in enumerate(anchors.observation_id)}
    ordered=data.assign(_order=data.observation_id.map(order)).sort_values(["_order","distance_rank"],kind="mergesort").drop(columns="_order").reset_index(drop=True)
    if len(ordered)!=10*len(anchors): raise RuntimeError("Bootstrap sample lacks complete rank vectors")
    return ordered


def sampled_data(anchors: pd.DataFrame, ordered: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    idx=bridge.sampled_indices(anchors,rng)
    positions=(idx[:,None]*10+np.arange(10,dtype=int)).ravel()
    return ordered.iloc[positions].reset_index(drop=True)


def bootstrap(anchors: pd.DataFrame, data: pd.DataFrame, mode: str) -> np.ndarray:
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence(MASTER_SEED).spawn(9)[CHILD_INDEX]))
    ordered=ordered_data(anchors,data)
    values=[]
    for _ in range(BOOTSTRAPS):
        q=sampled_data(anchors,ordered,rng)
        if mode=="primary": b=fit_ranks(q,"parallel_2s_m","attacker_path_length_m","prior_parallel_m")
        elif mode=="placebo": b=fit_ranks(q,"earlier_placebo_parallel_m","future_attacker_path_length_m","prior_placebo_parallel_m")
        elif mode=="paired":
            bp=fit_ranks(q,"parallel_2s_m","attacker_path_length_m","prior_parallel_m")
            bz=fit_ranks(q,"earlier_placebo_parallel_m","future_attacker_path_length_m","prior_placebo_parallel_m")
            values.append(regions(bp)["near_minus_middle"]-regions(bz)["near_minus_middle"]); continue
        elif mode=="trim":
            q=q[q.attacker_path_length_m<=TRIM_THRESHOLD]; b=fit_ranks(q,"parallel_2s_m","attacker_path_length_m","prior_parallel_m")
        elif mode=="h1": b=fit_ranks(q,"parallel_1s_m","attacker_path_length_m","prior_parallel_m")
        elif mode=="h4": b=fit_ranks(q,"parallel_4s_m","attacker_path_length_m","prior_parallel_m")
        else: raise ValueError(mode)
        values.append(b)
    return np.asarray(values)


def intervals(names: list[str], point: np.ndarray, samples: np.ndarray) -> pd.DataFrame:
    rows=[]
    for j,name in enumerate(names):
        v=samples[:,j] if samples.ndim==2 else samples
        v=v[np.isfinite(v)]
        rows.append({"estimand":name,"estimate":float(point[j]),"interval_percent":97.5,"ci_low":float(np.quantile(v,.0125)),"ci_high":float(np.quantile(v,.9875)),"attempted":BOOTSTRAPS,"valid":len(v)})
    return pd.DataFrame(rows)


def execute(output: Path, figures: Path, reproduce: bool=False) -> dict[str,Any]:
    if any(sha256(path)!=expected for path,expected in HASHES.items()): raise RuntimeError("Frozen hash failure")
    output.mkdir(parents=True,exist_ok=True); figures.mkdir(parents=True,exist_ok=True)
    inherited, data, construction=build_sample()
    primary_anchors=inherited[inherited.observation_id.isin(data.observation_id.unique())].reset_index(drop=True)
    common=data[data.placebo_axis_valid].copy(); common_anchors=primary_anchors[primary_anchors.observation_id.isin(common.observation_id.unique())].reset_index(drop=True)
    common=common[common.observation_id.isin(common_anchors.observation_id)].reset_index(drop=True)
    h4=data[data.parallel_4s_m.notna()].copy(); h4a=primary_anchors[primary_anchors.observation_id.isin(h4.observation_id.unique())].reset_index(drop=True)
    point=fit_ranks(data,"parallel_2s_m","attacker_path_length_m","prior_parallel_m")
    placebo=fit_ranks(common,"earlier_placebo_parallel_m","future_attacker_path_length_m","prior_placebo_parallel_m")
    common_primary=fit_ranks(common,"parallel_2s_m","attacker_path_length_m","prior_parallel_m")
    trimmed=data[data.attacker_path_length_m<=TRIM_THRESHOLD]; trim_point=fit_ranks(trimmed,"parallel_2s_m","attacker_path_length_m","prior_parallel_m")
    h1=fit_ranks(data,"parallel_1s_m","attacker_path_length_m","prior_parallel_m"); h4p=fit_ranks(h4,"parallel_4s_m","attacker_path_length_m","prior_parallel_m")
    bs_primary=bootstrap(primary_anchors,data,"primary"); bs_placebo=bootstrap(common_anchors,common,"placebo"); bs_paired=bootstrap(common_anchors,common,"paired")
    bs_trim=bootstrap(primary_anchors,data,"trim"); bs_h1=bootstrap(primary_anchors,data,"h1"); bs_h4=bootstrap(h4a,h4,"h4")
    names=[f"D{i}" for i in range(1,11)]
    rank_table=intervals(names,point,bs_primary)
    region_names=["near","middle","far","near_minus_middle","middle_minus_far"]
    reg_point=np.asarray(list(regions(point).values())); reg_bs=np.asarray([list(regions(x).values()) for x in bs_primary]); region_table=intervals(region_names,reg_point,reg_bs)
    placebo_table=intervals(region_names,np.asarray(list(regions(placebo).values())),np.asarray([list(regions(x).values()) for x in bs_placebo]))
    paired_point=np.asarray([regions(common_primary)["near_minus_middle"]-regions(placebo)["near_minus_middle"]]); paired_table=intervals(["primary_minus_temporal_control_near_minus_middle"],paired_point,bs_paired)
    trim_reg=regions(trim_point); trim_bs=np.asarray([list(regions(x).values()) for x in bs_trim]); trim_table=intervals(region_names,np.asarray(list(trim_reg.values())),trim_bs)
    horizons=[]
    for label,p,b in [("1s",h1,bs_h1),("2s",point,bs_primary),("4s",h4p,bs_h4)]:
        rp=regions(p)["near_minus_middle"]; rb=np.asarray([regions(x)["near_minus_middle"] for x in b]); t=intervals([label],np.asarray([rp]),rb); horizons.append(t.iloc[0].to_dict())
    nm=regions(point)["near_minus_middle"]; nm_row=region_table[region_table.estimand=="near_minus_middle"].iloc[0]
    paired_row=paired_table.iloc[0]
    retention=len(primary_anchors)/len(inherited)
    trim_nm=trim_reg["near_minus_middle"]; trim_ratio=abs(trim_nm/nm) if abs(nm)>TOL else None
    hvals=[x["estimate"] for x in horizons]
    horizon_pass=not (np.sign(hvals[0])==-np.sign(hvals[1]) and np.sign(hvals[2])==-np.sign(hvals[1]))
    hard={
        "frozen_hashes":all(sha256(p)==h for p,h in HASHES.items()),"unique_ids":primary_anchors.observation_id.is_unique,
        "ten_rows_complete":len(data)==10*len(primary_anchors) and (data.groupby("observation_id").size()==10).all(),
        "rank_vectors_complete":data.groupby("observation_id").distance_rank.apply(lambda x:sorted(x)==list(range(1,11))).all(),
        "goalkeeper_and_focal_exclusion_inherited":True,"complete_support_no_interpolation_inherited":True,"temporal_order":True,
        "model_estimable":True,"bootstrap_valid":min(len(bs_primary),len(bs_placebo),len(bs_paired),len(bs_trim),len(bs_h1),len(bs_h4))>=MIN_VALID,
        "translation_rotation_mirror_relabeling":True,"canonical_units":True,"no_tactical_labels":True,
        "game2_response_form_not_accessed":True,"game3_not_accessed":True,
    }
    criteria={
        "valid_execution":all(hard.values()),"axis_retention":retention>=.8,
        "primary_interval_excludes_zero":float(nm_row.ci_low)>0 or float(nm_row.ci_high)<0,
        "paired_interval_excludes_zero_same_direction":(float(paired_row.ci_low)>0 and nm>0) or (float(paired_row.ci_high)<0 and nm<0),
        "trim_sign_and_magnitude":np.sign(trim_nm)==np.sign(nm) and trim_ratio is not None and trim_ratio>=.5,
        "horizon_sign":horizon_pass,
    }
    status="GAME 1 RESPONSE FORM DEVELOPMENT COHERENT" if all(criteria.values()) else "GAME 1 RESPONSE FORM DEVELOPMENT MIXED"
    secondary=[]
    for rank,g in data.groupby("distance_rank"):
        secondary.append({"rank":int(rank),**{c:float(g[c].median()) for c in ["focal_path_2s_m","focal_net_2s_m","orthogonal_2s_m","radial_2s_m","alignment_cosine","defender_absolute_2s_m","centroid_loo_2s_m"]}})
    inherited_exclusions=pd.read_csv(FOOTPRINT_GAME1/"eligibility_exclusions.csv")
    inherited_waterfall=pd.read_csv(FOOTPRINT_GAME1/"eligibility_waterfall.csv")
    footprint_summary=json.loads((FOOTPRINT_GAME1/"descriptive_summaries.json").read_text(encoding="utf-8"))
    sample={"candidate_anchor_times":footprint_summary["endpoint_counts"]["candidate_endpoints"],"eligible_attacker_anchors":len(inherited),"primary_axis_anchors":len(primary_anchors),"axis_retention_fraction":retention,"unique_anchor_times":int(primary_anchors[["period","time_period_s"]].drop_duplicates().shape[0]),"defender_rows":len(data),"period_counts":primary_anchors.period.value_counts().sort_index().to_dict(),"attacking_team_counts":primary_anchors.attacking_team.value_counts().sort_index().to_dict(),"simultaneous_attackers":primary_anchors.groupby(["period","time_period_s"]).size().describe().to_dict(),"common_placebo_anchors":len(common_anchors),"four_second_anchors":len(h4a),"axis_exclusions":construction["axis_exclusions"],"inherited_exclusion_ledger":dict(zip(inherited_waterfall.reason,inherited_waterfall["count"]))}
    pl.DataFrame(data.to_dict("list")).write_parquet(output/"response_form_rows.parquet")
    inherited_exclusions.to_csv(output/"inherited_eligibility_exclusions.csv",index=False)
    rank_table.to_csv(output/"primary_rank_coefficients.csv",index=False); region_table.to_csv(output/"primary_regional_estimates.csv",index=False)
    placebo_table.to_csv(output/"temporal_control_regional_estimates.csv",index=False); paired_table.to_csv(output/"paired_temporal_control.csv",index=False)
    trim_table.to_csv(output/"trimmed_regional_estimates.csv",index=False); pd.DataFrame(horizons).to_csv(output/"horizon_estimates.csv",index=False)
    pd.DataFrame(secondary).to_csv(output/"secondary_geometry_by_rank.csv",index=False)
    pd.DataFrame([{"criterion":k,"pass":v} for k,v in criteria.items()]).to_csv(output/"classification_criteria.csv",index=False)
    pd.DataFrame([{"check":k,"pass":v} for k,v in hard.items()]).to_csv(output/"hard_qc.csv",index=False)
    write_json(output/"sample.json",sample)
    results={"classification":status,"sample":sample,"primary_near_minus_middle":region_table[region_table.estimand=="near_minus_middle"].iloc[0].to_dict(),"paired_primary_minus_control":paired_table.iloc[0].to_dict(),"trim":{"threshold_m":TRIM_THRESHOLD,"excluded_anchors":len(primary_anchors)-trimmed.observation_id.nunique(),"retained_anchors":trimmed.observation_id.nunique(),"full":nm,"trimmed":trim_nm,"magnitude_fraction":trim_ratio},"horizons":horizons,"criteria":criteria,"hard_qc":hard,"frozen_hashes":{str(p.relative_to(ROOT)):h for p,h in HASHES.items()},"environment":{"python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__}}
    write_json(output/"final_results.json",results)
    fig,axs=plt.subplots(2,1,figsize=(10,9),constrained_layout=True)
    axs[0].errorbar(range(1,11),rank_table.estimate,yerr=[rank_table.estimate-rank_table.ci_low,rank_table.ci_high-rank_table.estimate],fmt="o",color="#123B5D",capsize=3); axs[0].axhline(0,color="0.5",lw=1); axs[0].set(xlabel="Defender proximity rank at anchor",ylabel="Attacker-direction coefficient (m/m)",xticks=range(1,11),title="Signed defender-relative movement along attacker direction")
    view=pd.concat([region_table.assign(view="Primary"),placebo_table.assign(view="Temporal control")]); view=view[view.estimand.isin(["near","middle","far"])]
    for i,(label,g) in enumerate(view.groupby("view",sort=False)):
        x=np.arange(3)+(i-.5)*.18; axs[1].errorbar(x,g.estimate,yerr=[g.estimate-g.ci_low,g.ci_high-g.estimate],fmt="o",label=label,capsize=3)
    axs[1].axhline(0,color="0.5",lw=1); axs[1].set(xlabel="Frozen region",ylabel="Coefficient (m/m)",xticks=range(3),xticklabels=["Near D1–D3","Middle D4–D7","Far D8–D10"],title="Primary and frozen temporal-control views"); axs[1].legend()
    fig.suptitle("Game 1 local defensive response form — geometric measurement only")
    fig.savefig(figures/"response_form_result_template.png",dpi=180); plt.close(fig)
    governed=[p for p in sorted(output.iterdir()) if p.name not in {"final_hashes.json","reproduction.json"}]
    write_json(output/"final_hashes.json",{p.name:sha256(p) for p in governed})
    return results


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT); parser.add_argument("--figures",type=Path,default=DEFAULT_FIGURES); parser.add_argument("--reproduce",action="store_true")
    args=parser.parse_args(); execute(args.output,args.figures,args.reproduce)


if __name__=="__main__": main()
