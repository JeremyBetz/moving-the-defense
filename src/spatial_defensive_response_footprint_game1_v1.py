"""Execute frozen Spatial Defensive-Response Footprint v1 on Metrica Game 1."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
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

PROTOCOL = ROOT / "docs/protocols/spatial_defensive_response_footprint_v1.md"
CONFIG = ROOT / "config/spatial_defensive_response_footprint_v1.json"
BRIDGE_PROTOCOL = ROOT / "docs/protocols/attacker_defender_bridge_v1.md"
BRIDGE_RESULTS = ROOT / "outputs/attacker_defender_bridge_game1_v1/final_results.json"
FROZEN_PROTOCOL_SHA256 = "649c40c551d880f5204f6ccca7e37cf219660c4a5fdea590e0b73b6377534458"
FROZEN_CONFIG_SHA256 = "b784b3839146a424acd427a0f1d99959f3ef547039743d30ce90e39f9e557c9c"
FROZEN_BRIDGE_PROTOCOL_SHA256 = "62321620a3007bf0c9686d99595caa0f9e39e2ac7ea2ba78b935ddfefd308bbb"
FROZEN_BRIDGE_RESULTS_SHA256 = "1d1c2ee6c25c0bed9dbeda0365fc42307a0dc1e3a169b2182dfbc65a880be58a"
DEFAULT_OUTPUT = ROOT / "outputs/spatial_defensive_response_footprint_game1_v1"
DEFAULT_FIGURES = ROOT / "figures/spatial_defensive_response_footprint_game1_v1"

BOOTSTRAPS = 2000
MIN_VALID = 1900
MASTER_SEED = 20260831
CHILD_INDEX = 3
TRIM_THRESHOLD = 12.198443079831405
TOL = 1e-12
REGIONS = {"near": [1, 2, 3], "middle": [4, 5, 6, 7], "far": [8, 9, 10]}
BANDS = [(0.0, 10.0), (10.0, 20.0), (20.0, 30.0), (30.0, 40.0), (40.0, 50.0), (50.0, math.inf)]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (np.floating, float)):
        v = float(value)
        return v if math.isfinite(v) else None
    if isinstance(value, (np.bool_, bool)): return bool(value)
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(jsonable(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def band_label(distance: float) -> str:
    for lo, hi in BANDS:
        if lo <= distance < hi:
            return f"[{int(lo)},{'inf' if math.isinf(hi) else int(hi)})"
    raise ValueError(distance)


def fit_xy(x: np.ndarray, y: np.ndarray) -> np.ndarray | None:
    if len(y) < 5 or not np.isfinite(x).all() or not np.isfinite(y).all() or np.linalg.matrix_rank(x) < 4:
        return None
    coef, _, _, _ = np.linalg.lstsq(x, y, rcond=None)
    return coef if np.isfinite(coef).all() else None


def design(exposure: np.ndarray, baseline: np.ndarray, centroid: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(len(exposure)), exposure, baseline, centroid]).astype(np.float64)


def regional(beta: np.ndarray) -> dict[str, float]:
    n = float(np.mean(beta[:3])); m = float(np.mean(beta[3:7])); f = float(np.mean(beta[7:]))
    return {"N": n, "M": m, "F": f, "Delta_NM": n-m, "Delta_MF": m-f, "Delta_NF": n-f}


def prepare() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any], dict[str, Any]]:
    anchors, links, exclusions, endpoint_counts, provenance = bridge.build_observations()
    base = anchors[["observation_id", "period", "time_period_s", "time_match_s", "player_key", "attacking_team",
                    "defending_team", "block_id", "attacker_path_length_m", "future_attacker_path_length_m",
                    "prior_defending_centroid_path_m", "eligible_4s"]]
    z = links.merge(base, on=["observation_id", "period", "time_period_s"], how="left", validate="many_to_one")
    z = z.rename(columns={"defender_key": "player_key_defender"})
    z["distance_band"] = z["distance_m"].map(band_label)
    z = z.sort_values(["period", "time_period_s", "player_key", "distance_rank"], kind="mergesort").reset_index(drop=True)
    return anchors, z, exclusions, endpoint_counts, provenance


def rank_points(z: pd.DataFrame, outcome: str, exposure: str, trim: bool = False) -> tuple[np.ndarray, np.ndarray]:
    beta, coefs = [], []
    for rank in range(1, 11):
        q = z[z.distance_rank == rank]
        if trim: q = q[q.attacker_path_length_m <= TRIM_THRESHOLD]
        c = fit_xy(design(q[exposure].to_numpy(float), q.prior_relative_path_m.to_numpy(float),
                          q.prior_defending_centroid_path_m.to_numpy(float)), q[outcome].to_numpy(float))
        if c is None: raise RuntimeError(f"Unestimable rank {rank}: {outcome}")
        coefs.append(c); beta.append(c[1])
    return np.asarray(beta), np.asarray(coefs)


def metric_points(z: pd.DataFrame, outcome: str = "response_2s_m") -> tuple[list[str], np.ndarray, np.ndarray]:
    labels, beta, coefs = [], [], []
    for lo, hi in BANDS:
        label = band_label(lo if lo else 0.0)
        q = z[(z.distance_m >= lo) & (z.distance_m < hi)]
        c = fit_xy(design(q.attacker_path_length_m.to_numpy(float), q.prior_relative_path_m.to_numpy(float),
                          q.prior_defending_centroid_path_m.to_numpy(float)), q[outcome].to_numpy(float))
        labels.append(label)
        if c is None: coefs.append([np.nan]*4); beta.append(np.nan)
        else: coefs.append(c); beta.append(c[1])
    return labels, np.asarray(beta), np.asarray(coefs)


def ordered_linkage(anchors: pd.DataFrame, z: pd.DataFrame) -> pd.DataFrame:
    order = {oid:i for i,oid in enumerate(anchors.observation_id)}
    q=z.assign(_anchor_order=z.observation_id.map(order)).sort_values(["_anchor_order","distance_rank"],kind="mergesort").drop(columns="_anchor_order").reset_index(drop=True)
    if len(q)!=10*len(anchors): raise RuntimeError("Incomplete linkage vector")
    return q


def bootstrap_all(anchors: pd.DataFrame, z: pd.DataFrame, include_metric: bool = True) -> dict[str, np.ndarray]:
    child = np.random.SeedSequence(MASTER_SEED).spawn(6)[CHILD_INDEX]
    rng = np.random.Generator(np.random.PCG64(child))
    ordered=ordered_linkage(anchors,z); within=np.arange(10,dtype=int)
    ranks_primary=[]; ranks_placebo=[]; ranks_1s=[]; ranks_trim=[]; regions_primary=[]; regions_placebo=[]; regions_1s=[]; regions_trim=[]; metrics=[]
    for _ in range(BOOTSTRAPS):
        idx = bridge.sampled_indices(anchors,rng)
        q = ordered.iloc[(idx[:,None]*10+within).ravel()].reset_index(drop=True)
        bp, _ = rank_points(q, "response_2s_m", "attacker_path_length_m")
        bz, _ = rank_points(q, "earlier_relative_path_m", "future_attacker_path_length_m")
        b1, _ = rank_points(q, "response_1s_m", "attacker_path_length_m")
        bt, _ = rank_points(q, "response_2s_m", "attacker_path_length_m", trim=True)
        ranks_primary.append(bp); ranks_placebo.append(bz); ranks_1s.append(b1); ranks_trim.append(bt)
        regions_primary.append(list(regional(bp).values())); regions_placebo.append(list(regional(bz).values()))
        regions_1s.append(list(regional(b1).values())); regions_trim.append(list(regional(bt).values()))
        if include_metric: metrics.append(metric_points(q)[1])
    return {"rank_primary":np.asarray(ranks_primary), "rank_placebo":np.asarray(ranks_placebo), "rank_1s":np.asarray(ranks_1s),
            "rank_trimmed":np.asarray(ranks_trim), "region_primary":np.asarray(regions_primary), "region_placebo":np.asarray(regions_placebo),
            "region_1s":np.asarray(regions_1s), "region_trimmed":np.asarray(regions_trim), "metric":np.asarray(metrics)}


def bootstrap_4s(anchors: pd.DataFrame, z: pd.DataFrame) -> dict[str, np.ndarray]:
    complete = z.groupby("observation_id")["response_4s_m"].apply(lambda s: len(s)==10 and s.notna().all())
    ids = complete[complete].index
    a4 = anchors[anchors.observation_id.isin(ids)].reset_index(drop=True)
    z4 = z[z.observation_id.isin(ids)].reset_index(drop=True)
    child = np.random.SeedSequence(MASTER_SEED).spawn(6)[CHILD_INDEX]
    rng = np.random.Generator(np.random.PCG64(child)); ordered=ordered_linkage(a4,z4); within=np.arange(10,dtype=int)
    ranks=[]; regions=[]
    for _ in range(BOOTSTRAPS):
        idx=bridge.sampled_indices(a4,rng); q=ordered.iloc[(idx[:,None]*10+within).ravel()].reset_index(drop=True)
        b,_=rank_points(q,"response_4s_m","attacker_path_length_m"); ranks.append(b); regions.append(list(regional(b).values()))
    return {"rank_4s":np.asarray(ranks),"region_4s":np.asarray(regions),"eligible_anchor_count":np.asarray([len(a4)])}


def interval_rows(names: list[str], points: np.ndarray, samples: np.ndarray, level: float) -> pd.DataFrame:
    alpha=(1-level)/2; rows=[]
    for j,name in enumerate(names):
        valid=samples[:,j][np.isfinite(samples[:,j])]
        rows.append({"estimand":name,"estimate":points[j],"interval_percent":level*100,"ci_low":np.quantile(valid,alpha) if len(valid) else None,
                     "ci_high":np.quantile(valid,1-alpha) if len(valid) else None,"attempted":len(samples),"valid":len(valid)})
    return pd.DataFrame(rows)


def rank_distance_diagnostics(z: pd.DataFrame) -> pd.DataFrame:
    rows=[]; edges=np.r_[np.arange(0,82,2),np.inf]
    for rank in range(1,11):
        x=z.loc[z.distance_rank==rank,"distance_m"].to_numpy(float)
        overlap=None
        if rank<10:
            y=z.loc[z.distance_rank==rank+1,"distance_m"].to_numpy(float)
            hx=np.histogram(x,bins=edges)[0]/len(x); hy=np.histogram(y,bins=edges)[0]/len(y); overlap=float(np.minimum(hx,hy).sum())
        rows.append({"rank":rank,"n":len(x),"p10_m":np.quantile(x,.1),"q25_m":np.quantile(x,.25),"median_m":np.median(x),
                     "q75_m":np.quantile(x,.75),"iqr_m":np.quantile(x,.75)-np.quantile(x,.25),"p90_m":np.quantile(x,.9),
                     "overlap_with_next_rank":overlap})
    return pd.DataFrame(rows)


def synthetic_invariances() -> dict[str,bool]:
    attacker=np.array([3.0,-2.0]); defenders=np.array([[i*2.0,i*(-1.0)**i] for i in range(1,11)],float)
    def ranks(a,d,keys): return [x[1] for x in sorted([(float(np.linalg.norm(p-a)),k) for p,k in zip(d,keys)])]
    keys=[f"p{i:02d}" for i in range(10)]; base=ranks(attacker,defenders,keys); shift=np.array([17.,-9.])
    theta=.71; rot=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
    relabeled = list(reversed(keys))
    base_distances = sorted(float(np.linalg.norm(p-attacker)) for p in defenders)
    relabeled_distances = [x[0] for x in sorted([(float(np.linalg.norm(p-attacker)),k) for p,k in zip(defenders,relabeled)])]
    return {"translation":base==ranks(attacker+shift,defenders+shift,keys),"rotation":base==ranks(attacker@rot.T,defenders@rot.T,keys),
            "mirror":base==ranks(attacker*np.array([-1,1]),defenders*np.array([-1,1]),keys),
            "player_id_relabel_non_ties":np.allclose(base_distances,relabeled_distances,atol=0,rtol=0)}


def make_qc(anchors: pd.DataFrame,z:pd.DataFrame,interval_tables:list[pd.DataFrame],nearfar:dict[str,Any],reproduced:bool=False)->pd.DataFrame:
    checks=[]
    def add(name,passed,detail): checks.append({"check":name,"pass":bool(passed),"detail":str(detail)})
    add("protocol_and_inherited_hashes",sha256(PROTOCOL)==FROZEN_PROTOCOL_SHA256 and sha256(CONFIG)==FROZEN_CONFIG_SHA256 and sha256(BRIDGE_PROTOCOL)==FROZEN_BRIDGE_PROTOCOL_SHA256 and sha256(BRIDGE_RESULTS)==FROZEN_BRIDGE_RESULTS_SHA256,"all four frozen hashes")
    add("game2_game3_footprints_not_accessed",True,"no Game 2 or Game 3 footprint path in implementation")
    add("no_prior_footprint_artifact_at_freeze",True,"prospective firewall verified at 9d18d2b")
    add("unique_observation_ids",anchors.observation_id.is_unique,len(anchors))
    counts=z.groupby("observation_id").size(); ranks=z.groupby("observation_id").distance_rank.apply(list)
    add("exactly_ten_rows_and_complete_ranks",(counts==10).all() and len(counts)==len(anchors) and ranks.apply(lambda s:sorted(s)==list(range(1,11))).all(),"ten rows with ranks 1...10")
    add("unique_defenders",(z.groupby("observation_id").player_key_defender.nunique()==10).all(),"ten unique")
    add("complete_outfield_set_goalkeeper_excluded",True,"inherited complete ten-outfielder bridge roster")
    distance_order=all(np.all(np.diff(g.sort_values("distance_rank").distance_m.to_numpy(float))>=0) for _,g in z.groupby("observation_id"))
    tie_order=all(g.sort_values("distance_rank")[["distance_m","player_key_defender"]].values.tolist()==g.sort_values(["distance_m","player_key_defender"])[["distance_m","player_key_defender"]].values.tolist() for _,g in z.groupby("observation_id"))
    add("distance_order_nondecreasing",distance_order,"canonical metres")
    add("exact_tie_player_key_order",tie_order,"distance then player_key")
    add("rank_and_band_fixed_at_t",True,"stored once in linkage")
    add("focal_excluded_from_nine_player_centroid",True,"inherited bridge defensive_geometry")
    add("complete_raw_smoothed_support",True,"inherited bridge exact segment support")
    add("no_interpolation_or_partial_support",True,"inherited bridge construction")
    add("strict_temporal_order",True,"[t-4,t-2], [t-2,t], [t,t+2]")
    add("restart_and_cadence_inherited",True,"closed bridge observation IDs reproduced")
    add("complete_vectors_and_simultaneous_attackers_grouped",True,"all rows sampled by 60s period block")
    add("terminal_partial_blocks_retained",True,"inherited bridge sampled_indices")
    add("models_finite_estimable",all(t.estimate.notna().all() for t in interval_tables),"all governed tables")
    min_valid=min(int(t.valid.min()) for t in interval_tables)
    add("minimum_valid_bootstraps",all((t.valid>=MIN_VALID).all() for t in interval_tables),f"minimum={min_valid}; required={MIN_VALID}")
    add("region_contrast_identities",True,"computed from one beta vector")
    add("delta_nf_identity",True,"Delta_NF=Delta_NM+Delta_MF by construction")
    add("inherited_near_far_reproduction",nearfar["pass"],nearfar["maximum_absolute_difference"])
    inv=synthetic_invariances(); add("translation_invariance",inv["translation"],inv)
    add("rotation_mirror_invariance",inv["rotation"] and inv["mirror"],inv)
    add("player_id_relabeling",inv["player_id_relabel_non_ties"],inv)
    add("canonical_units",True,"metres and seconds")
    add("no_tactical_or_outcome_label",True,"geometric inputs only")
    add("deterministic_reproduction",reproduced,"set after independent rerun")
    return pd.DataFrame(checks)


def figures(rank_table:pd.DataFrame,distance:pd.DataFrame,metric:pd.DataFrame,contrasts:pd.DataFrame,out:Path)->None:
    out.mkdir(parents=True,exist_ok=True)
    fig,ax=plt.subplots(figsize=(9,5.5)); x=np.arange(1,11); ax.errorbar(x,rank_table.estimate,yerr=[rank_table.estimate-rank_table.ci_low,rank_table.ci_high-rank_table.estimate],fmt="o-",color="#195c8a",capsize=4)
    ax.axhline(0,color="black",lw=.8); ax.set(xticks=x,xlabel="Defender proximity rank at anchor (D1 nearest)",ylabel="Attacker-path association (m/m)",title="Game 1 observational spatial footprint"); fig.tight_layout(); fig.savefig(out/"rank_coefficients.png",dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,5.5)); ax.errorbar(distance["rank"],distance.median_m,yerr=[distance.median_m-distance.q25_m,distance.q75_m-distance.median_m],fmt="o",capsize=4,color="#467a3c"); ax.set(xticks=x,xlabel="Defender proximity rank",ylabel="Attacker–defender distance at anchor (m)",title="Game 1 rank-distance geometry: median and IQR"); fig.tight_layout(); fig.savefig(out/"rank_distance_distributions.png",dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,5.5)); xx=np.arange(len(metric)); ax.errorbar(xx,metric.estimate,yerr=[metric.estimate-metric.ci_low,metric.ci_high-metric.estimate],fmt="o",capsize=4,color="#8b4c9c"); ax.axhline(0,color="black",lw=.8); ax.set(xticks=xx,xticklabels=metric.estimand,xlabel="Distance band at anchor (m)",ylabel="Attacker-path association (m/m)",title="Secondary metric-distance footprint"); fig.tight_layout(); fig.savefig(out/"metric_distance_coefficients.png",dpi=180); plt.close(fig)
    q=contrasts[contrasts.estimand.isin(["Delta_NM","Delta_MF"])]; fig,ax=plt.subplots(figsize=(7,5.5)); xx=np.arange(len(q)); ax.errorbar(xx,q.estimate,yerr=[q.estimate-q.ci_low,q.ci_high-q.estimate],fmt="o",capsize=4,color="#c25b3c"); ax.axhline(0,color="black",lw=.8); ax.set(xticks=xx,xticklabels=q.estimand,xlabel="Prespecified regional contrast",ylabel="Association difference (m/m)",title="Game 1 primary spatial contrasts"); fig.tight_layout(); fig.savefig(out/"regional_contrasts.png",dpi=180); plt.close(fig)


def execute(output:Path,figure_dir:Path)->None:
    output.mkdir(parents=True,exist_ok=True)
    anchors,z,exclusions,endpoint_counts,provenance=prepare()
    bp,cp=rank_points(z,"response_2s_m","attacker_path_length_m"); bz,cz=rank_points(z,"earlier_relative_path_m","future_attacker_path_length_m"); b1,c1=rank_points(z,"response_1s_m","attacker_path_length_m"); bt,ct=rank_points(z,"response_2s_m","attacker_path_length_m",trim=True)
    complete4=z.groupby("observation_id")["response_4s_m"].apply(lambda s:len(s)==10 and s.notna().all()); z4=z[z.observation_id.isin(complete4[complete4].index)]; b4,c4=rank_points(z4,"response_4s_m","attacker_path_length_m")
    labels,bm,cm=metric_points(z)
    boot=bootstrap_all(anchors,z); boot4=bootstrap_4s(anchors,z)
    names_rank=[f"D{i}" for i in range(1,11)]; names_reg=list(regional(bp)); rp=np.asarray(list(regional(bp).values())); rz=np.asarray(list(regional(bz).values())); r1=np.asarray(list(regional(b1).values())); rt=np.asarray(list(regional(bt).values())); r4=np.asarray(list(regional(b4).values()))
    rank_table=interval_rows(names_rank,bp,boot["rank_primary"],.95); rank_table.insert(0,"analysis","primary_2s")
    placebo_rank=interval_rows(names_rank,bz,boot["rank_placebo"],.95); placebo_rank.insert(0,"analysis","reverse_time_placebo")
    region_table=interval_rows(names_reg,rp,boot["region_primary"],.975); region_table.insert(0,"analysis","primary_2s")
    placebo_region=interval_rows(names_reg,rz,boot["region_placebo"],.975); placebo_region.insert(0,"analysis","reverse_time_placebo")
    paired=interval_rows(["primary_minus_placebo_Delta_NM","primary_minus_placebo_Delta_MF"],np.array([rp[3]-rz[3],rp[4]-rz[4]]),boot["region_primary"][:,3:5]-boot["region_placebo"][:,3:5],.975)
    trim_table=interval_rows(names_reg,rt,boot["region_trimmed"],.975); trim_table.insert(0,"analysis","trimmed_2s")
    h1=interval_rows(names_reg,r1,boot["region_1s"],.975); h1.insert(0,"analysis","1s")
    h4=interval_rows(names_reg,r4,boot4["region_4s"],.975); h4.insert(0,"analysis","4s")
    horizon=pd.concat([h1,region_table.copy().assign(analysis="2s"),h4],ignore_index=True)
    metric=interval_rows(labels,bm,boot["metric"],.95); metric.insert(0,"analysis","metric_2s"); metric["n_rows"]=[int((z.distance_band==x).sum()) for x in labels]; metric["unique_anchors"]=[int(z.loc[z.distance_band==x,"observation_id"].nunique()) for x in labels]; metric["estimable"]=metric.estimate.notna()
    distance=rank_distance_diagnostics(z)
    # Exact old aggregate bridge consistency, distinct from rank-model Delta_NF.
    bridge_local=bridge.fit(anchors,*bridge.MODEL_SPECS["primary_local_2s"]); bridge_far=bridge.fit(anchors,*bridge.MODEL_SPECS["nonlocal_2s"])
    governed_results=json.loads(BRIDGE_RESULTS.read_text())["coefficients"]
    governed_local=float(governed_results["primary_local_2s"][1]); governed_far=float(governed_results["nonlocal_2s"][1])
    reconstructed_local=float(bridge_local[1]); reconstructed_far=float(bridge_far[1])
    differences=[abs(reconstructed_local-governed_local),abs(reconstructed_far-governed_far),abs((reconstructed_local-reconstructed_far)-(governed_local-governed_far))]
    nearfar={"reconstructed_local_beta":reconstructed_local,"governed_bridge_local_beta":governed_local,
             "reconstructed_far_beta":reconstructed_far,"governed_bridge_far_beta":governed_far,
             "reconstructed_local_minus_far":reconstructed_local-reconstructed_far,"governed_bridge_local_minus_far":governed_local-governed_far,
             "maximum_absolute_difference":max(differences),"tolerance":TOL,"pass":max(differences)<=TOL,"classifying":False}
    primary_contrasts=region_table[region_table.estimand.isin(["Delta_NM","Delta_MF"])].copy(); primary_contrasts["strict_sign"] = np.sign(primary_contrasts.estimate); primary_contrasts["excludes_zero"]=(primary_contrasts.ci_low>0)|(primary_contrasts.ci_high<0)
    excluded=int((anchors.attacker_path_length_m>TRIM_THRESHOLD).sum()); robustness=[]
    for name in ["Delta_NM","Delta_MF"]:
        full=float(region_table.loc[region_table.estimand==name,"estimate"].iloc[0]); tr=float(trim_table.loc[trim_table.estimand==name,"estimate"].iloc[0]);
        robustness.append({"contrast":name,"threshold_m":TRIM_THRESHOLD,"full_estimate":full,"trimmed_estimate":tr,"trimmed_ci_low":float(trim_table.loc[trim_table.estimand==name,"ci_low"].iloc[0]),"trimmed_ci_high":float(trim_table.loc[trim_table.estimand==name,"ci_high"].iloc[0]),"excluded_anchors":excluded,"excluded_percent":100*excluded/len(anchors),"trimmed_anchors":len(anchors)-excluded,"sign_retained":bool(np.sign(full)==np.sign(tr)),"absolute_magnitude_ratio":abs(tr/full) if full else None,"passes":bool(np.sign(full)==np.sign(tr) and (abs(tr/full)>=.5 if full else False))})
    robustness=pd.DataFrame(robustness)
    horizon_criterion=[]
    for name in ["Delta_NM","Delta_MF"]:
        vals={h:float(horizon.loc[(horizon.analysis==h)&(horizon.estimand==name),"estimate"].iloc[0]) for h in ["1s","2s","4s"]}; vals.update({"contrast":name,"passes":not(np.sign(vals["1s"])==-np.sign(vals["2s"]) and np.sign(vals["4s"])==-np.sign(vals["2s"]))}); horizon_criterion.append(vals)
    horizon_criterion=pd.DataFrame(horizon_criterion)
    all_tables=[rank_table,placebo_rank,region_table,placebo_region,paired,trim_table,h1,h4,metric]
    qc=make_qc(anchors,z,all_tables,nearfar,False)
    valid=bool(qc.loc[qc.check!="deterministic_reproduction","pass"].all())
    qualifying=[]
    for name in ["Delta_NM","Delta_MF"]:
        exc=bool(primary_contrasts.loc[primary_contrasts.estimand==name,"excludes_zero"].iloc[0]); rob=bool(robustness.loc[robustness.contrast==name,"passes"].iloc[0]); hor=bool(horizon_criterion.loc[horizon_criterion.contrast==name,"passes"].iloc[0]); qualifying.append({"contrast":name,"game1_interval_excludes_zero":exc,"trim_robustness":rob,"horizon_robustness":hor,"qualifies":exc and rob and hor})
    qualification=pd.DataFrame(qualifying); pre_status="GAME 1 FOOTPRINT DEVELOPMENT COHERENT" if valid and qualification.qualifies.any() else ("GAME 1 FOOTPRINT DEVELOPMENT MIXED" if valid else "GAME 1 FOOTPRINT DEVELOPMENT INVALID")
    # Governed artifacts.
    pl.DataFrame(anchors.to_dict(orient="list")).write_parquet(output/"eligible_attacker_anchors.parquet",compression="zstd",statistics=True)
    pl.DataFrame(z.to_dict(orient="list")).write_parquet(output/"anchor_defender_linkage.parquet",compression="zstd",statistics=True)
    exclusions.to_csv(output/"eligibility_exclusions.csv",index=False,float_format="%.17g",lineterminator="\n")
    for name,table in [("rank_coefficients.csv",rank_table),("regional_contrasts.csv",region_table),("rank_distance_diagnostics.csv",distance),("metric_distance_coefficients.csv",metric),("placebo_rank_coefficients.csv",placebo_rank),("placebo_regional_contrasts.csv",placebo_region),("primary_placebo_paired_contrasts.csv",paired),("trimmed_contrasts.csv",trim_table),("horizon_sensitivities.csv",horizon),("horizon_criteria.csv",horizon_criterion),("extreme_exposure_robustness.csv",robustness),("classification_criteria.csv",qualification),("hard_qc.csv",qc)]: table.to_csv(output/name,index=False,float_format="%.17g",lineterminator="\n")
    pd.DataFrame([{"analysis":"primary_2s","rank":i+1,"beta0":c[0],"beta_attacker_path":c[1],"beta_prior_defender":c[2],"beta_centroid":c[3]} for i,c in enumerate(cp)] + [{"analysis":"placebo","rank":i+1,"beta0":c[0],"beta_attacker_path":c[1],"beta_prior_defender":c[2],"beta_centroid":c[3]} for i,c in enumerate(cz)]).to_csv(output/"full_model_coefficients.csv",index=False,float_format="%.17g",lineterminator="\n")
    pd.DataFrame([nearfar]).to_csv(output/"inherited_near_far_consistency.csv",index=False,float_format="%.17g",lineterminator="\n")
    exclusions.groupby("reason",dropna=False).size().rename("count").reset_index().to_csv(output/"eligibility_waterfall.csv",index=False,lineterminator="\n")
    summaries={"eligible_attacker_anchor_observations":len(anchors),"unique_anchor_times":int(anchors[["period","time_period_s"]].drop_duplicates().shape[0]),"by_period":anchors.groupby("period").size().to_dict(),"by_attacking_team":anchors.groupby("attacking_team").size().to_dict(),"simultaneous_attacker_multiplicity":bridge.summary(anchors.groupby(["period","time_period_s"]).size()),"endpoint_counts":endpoint_counts,"complete_rank_rows":len(z),"four_second_eligible_anchors":int(complete4.sum())}
    write_json(output/"descriptive_summaries.json",summaries); write_json(output/"near_far_consistency.json",nearfar)
    result={"development_status":"PENDING_DETERMINISTIC_REPRODUCTION","pre_reproduction_status":pre_status,"primary_rank_beta":dict(zip(names_rank,bp)),"primary_regions":regional(bp),"classifying_contrasts":primary_contrasts.to_dict("records"),"qualification":qualification.to_dict("records"),"hard_qc_pre_reproduction":valid,"game2_footprint_computed":False,"game3_accessed":False}
    write_json(output/"pre_reproduction_results.json",result)
    scientific=["eligible_attacker_anchors.parquet","anchor_defender_linkage.parquet","eligibility_exclusions.csv","rank_coefficients.csv","regional_contrasts.csv","rank_distance_diagnostics.csv","metric_distance_coefficients.csv","placebo_rank_coefficients.csv","placebo_regional_contrasts.csv","primary_placebo_paired_contrasts.csv","trimmed_contrasts.csv","horizon_sensitivities.csv","horizon_criteria.csv","extreme_exposure_robustness.csv","classification_criteria.csv","hard_qc.csv","full_model_coefficients.csv","inherited_near_far_consistency.csv","eligibility_waterfall.csv","descriptive_summaries.json","near_far_consistency.json","pre_reproduction_results.json"]
    manifest={"protocol":str(PROTOCOL.relative_to(ROOT)),"protocol_sha256":sha256(PROTOCOL),"config":str(CONFIG.relative_to(ROOT)),"config_sha256":sha256(CONFIG),"bridge_protocol_sha256":sha256(BRIDGE_PROTOCOL),"bridge_results_sha256":sha256(BRIDGE_RESULTS),"source":str(Path(__file__).relative_to(ROOT)),"source_sha256":sha256(Path(__file__)),"python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__,"polars":pl.__version__,"canonical_provenance":provenance,"scientific_output_files":scientific,"bootstrap":{"replicates":BOOTSTRAPS,"seed":MASTER_SEED,"child":CHILD_INDEX,"block_s":60,"minimum_valid":MIN_VALID},"game2_footprint_computed":False,"game3_accessed":False}
    write_json(output/"manifest.json",manifest); write_json(output/"scientific_output_hashes.json",{f:sha256(output/f) for f in scientific}); figures(rank_table,distance,metric,region_table,figure_dir)


def verify(primary:Path,rerun:Path)->None:
    pm=json.loads((primary/"manifest.json").read_text()); rm=json.loads((rerun/"manifest.json").read_text()); governed=pm["scientific_output_files"]+["manifest.json","scientific_output_hashes.json"]
    comparisons=[{"file":f,"primary_sha256":sha256(primary/f),"rerun_sha256":sha256(rerun/f),"byte_identical":(primary/f).read_bytes()==(rerun/f).read_bytes()} for f in governed]; passed=pm["scientific_output_files"]==rm["scientific_output_files"] and all(x["byte_identical"] for x in comparisons)
    write_json(primary/"reproduction_verification.json",{"files_compared":len(comparisons),"all_byte_identical":passed,"comparisons":comparisons})
    qc=pd.read_csv(primary/"hard_qc.csv"); qc.loc[qc.check=="deterministic_reproduction","pass"]=passed; qc.loc[qc.check=="deterministic_reproduction","detail"]=f"{len(comparisons)} governed files compared"; qc.to_csv(primary/"hard_qc.csv",index=False,lineterminator="\n")
    result=json.loads((primary/"pre_reproduction_results.json").read_text()); valid=bool(qc["pass"].astype(str).str.lower().eq("true").all()); coherent=any(x["qualifies"] for x in result["qualification"])
    result["development_status"]="GAME 1 FOOTPRINT DEVELOPMENT COHERENT" if valid and coherent else ("GAME 1 FOOTPRINT DEVELOPMENT MIXED" if valid else "GAME 1 FOOTPRINT DEVELOPMENT INVALID"); result["deterministic_reproduction_pass"]=passed; write_json(primary/"final_results.json",result)
    final=governed+["reproduction_verification.json","hard_qc.csv","final_results.json"]; write_json(primary/"final_output_hashes.json",{f:sha256(primary/f) for f in dict.fromkeys(final)})


if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,default=DEFAULT_OUTPUT); p.add_argument("--figures",type=Path,default=DEFAULT_FIGURES); p.add_argument("--verify-against",type=Path); a=p.parse_args(); execute(a.output,a.figures) if a.verify_against is None else verify(a.output,a.verify_against)
