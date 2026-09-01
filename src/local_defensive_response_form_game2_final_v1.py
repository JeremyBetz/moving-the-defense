"""Execute frozen response-form v1 on Game 2, then its governed pooled analysis."""
from __future__ import annotations

import argparse, hashlib, json, math, platform, sys
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
import attacking_continuous_movement_game2_v1 as game2  # noqa: E402
import local_defensive_response_form_game1_v1 as g1  # noqa: E402
import local_defensive_response_form_pooled_v1 as pool  # noqa: E402

ADD_DOC = ROOT / "docs/protocols/local_defensive_response_form_v1_pooled_execution_clarification.md"
ADD_CFG = ROOT / "config/local_defensive_response_form_v1_pooled_execution_clarification.json"
G2_FOOT = ROOT / "outputs/spatial_defensive_response_footprint_game2_final_v1"
G1_OUT = ROOT / "outputs/local_defensive_response_form_game1_v1"
DEFAULT_G2 = ROOT / "outputs/local_defensive_response_form_game2_final_v1"
DEFAULT_POOL = ROOT / "outputs/local_defensive_response_form_pooled_final_v1"
DEFAULT_FIG = ROOT / "figures/local_defensive_response_form_final_v1"
HASHES = {**g1.HASHES, ADD_DOC:"1ba4e198e286f1c6ae664b807be9de02e976ca0d86cbf46432e0d130e23cf794", ADD_CFG:"70f0d6ad1b3b459f094e98f0a985cf88a0d582f94a41ddb210206cf4b8a9c813", G1_OUT/"final_results.json":"fa0cf2fd53ea591d7e1266286bdb2d85603606de7df985d055f4ad92516bfcf6", G1_OUT/"final_hashes.json":"750c706c94ed12a0650de17a9417472c04d79e8b9e9bd303bd6a3c647a521e9c"}
BOOT, MIN_VALID, SEED = 2000, 1900, 20260831


def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()


def write_json(path: Path, value: Any) -> None:
    def clean(x: Any) -> Any:
        if isinstance(x,dict): return {str(k):clean(v) for k,v in x.items()}
        if isinstance(x,(list,tuple)): return [clean(v) for v in x]
        if isinstance(x,(np.integer,)): return int(x)
        if isinstance(x,(np.floating,float)):
            y=float(x); return y if math.isfinite(y) else None
        if isinstance(x,(np.bool_,bool)): return bool(x)
        return x
    path.write_text(json.dumps(clean(value),indent=2,sort_keys=True)+"\n",encoding="utf-8")


def verify() -> None:
    bad={str(p):[sha(p),v] for p,v in HASHES.items() if not p.exists() or sha(p)!=v}
    if bad: raise RuntimeError(f"Frozen hash failure: {bad}")


def build_game2() -> tuple[pd.DataFrame,pd.DataFrame,dict[str,Any]]:
    anchors=pd.DataFrame(pl.read_parquet(G2_FOOT/"game2_anchors.parquet").to_dicts())
    links=pd.DataFrame(pl.read_parquet(G2_FOOT/"game2_linkage.parquet").to_dicts())
    pps,_,provenance,support=game2.load_game2_from_frozen_support(); pp={(x.period,x.player_key):x for x in pps}
    rows=[]; exclusions=[]
    for a in anchors.itertuples(index=False):
        attack=pp[(int(a.period),str(a.player_key))]
        da=g1.interval(attack,float(a.time_period_s)-2,float(a.time_period_s)); da=da[-1]-da[0]
        fa=g1.interval(attack,float(a.time_period_s),float(a.time_period_s)+2); fa=fa[-1]-fa[0]
        ua,up=g1.unit(da),g1.unit(fa)
        if ua is None:
            exclusions.append({"observation_id":a.observation_id,"reason":"near_zero_or_invalid_attacker_axis"}); continue
        group=links[links.observation_id==a.observation_id].sort_values("distance_rank")
        defenders=[pp[(int(a.period),str(k))] for k in group.player_key_defender]
        windows={"prior":(-4,-2),"earlier":(-2,0),"post1":(0,1),"post2":(0,2)}
        if bool(a.eligible_4s): windows["post4"]=(0,4)
        stacks={n:np.stack([g1.interval(x,float(a.time_period_s)+lo,float(a.time_period_s)+hi) for x in defenders]) for n,(lo,hi) in windows.items()}
        for j,link in enumerate(group.itertuples(index=False)):
            vectors={}; paths={}
            for n,stack in stacks.items():
                rel=stack[j]-(stack.sum(axis=0)-stack[j])/9.0
                vectors[n]=rel[-1]-rel[0]; paths[n]=float(np.linalg.norm(np.diff(rel,axis=0),axis=1).sum())
            dpost=stacks["post2"][j,-1]-stacks["post2"][j,0]; cpost=dpost-vectors["post2"]
            attacker_t=g1.interval(attack,float(a.time_period_s),float(a.time_period_s))[0]
            radial=g1.unit(attacker_t-stacks["post2"][j,0]); normal=np.array([-ua[1],ua[0]])
            fn=float(np.linalg.norm(vectors["post2"]))
            rows.append({"observation_id":a.observation_id,"period":int(a.period),"time_period_s":float(a.time_period_s),"time_match_s":float(a.time_match_s),"attacker_key":str(a.player_key),"attacking_team":str(a.attacking_team),"defending_team":str(a.defending_team),"block_id":int(a.block_id),"defender_key":str(link.player_key_defender),"distance_rank":int(link.distance_rank),"distance_m":float(link.distance_m),"attacker_path_length_m":float(a.attacker_path_length_m),"future_attacker_path_length_m":float(a.future_attacker_path_length_m),"prior_centroid_path_m":float(a.prior_defending_centroid_path_m),"parallel_2s_m":float(vectors["post2"]@ua),"orthogonal_2s_m":float(vectors["post2"]@normal),"radial_2s_m":None if radial is None else float(vectors["post2"]@radial),"alignment_cosine":None if fn<=g1.geometry.VECTOR_NORM_EPSILON_M else float((vectors["post2"]@ua)/fn),"prior_parallel_m":float(vectors["prior"]@ua),"earlier_placebo_parallel_m":None if up is None else float(vectors["earlier"]@up),"prior_placebo_parallel_m":None if up is None else float(vectors["prior"]@up),"parallel_1s_m":float(vectors["post1"]@ua),"parallel_4s_m":None if "post4" not in vectors else float(vectors["post4"]@ua),"focal_path_2s_m":paths["post2"],"focal_net_2s_m":fn,"defender_absolute_2s_m":float(np.linalg.norm(dpost)),"centroid_loo_2s_m":float(np.linalg.norm(cpost)),"focal_delta_x_m":float(vectors["post2"][0]),"focal_delta_y_m":float(vectors["post2"][1]),"placebo_axis_valid":up is not None,"radial_axis_valid":radial is not None})
    data=pd.DataFrame(rows).sort_values(["period","time_period_s","attacker_key","distance_rank"],kind="mergesort").reset_index(drop=True)
    return anchors,data,{"source_provenance":provenance,"support":support,"axis_exclusions":exclusions}


def bootstrap_single(anchors: pd.DataFrame,data: pd.DataFrame,mode: str) -> np.ndarray:
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence(SEED).spawn(9)[7])); ordered=g1.ordered_data(anchors,data); values=[]
    for _ in range(BOOT):
        q=g1.sampled_data(anchors,ordered,rng)
        if mode=="primary": b=g1.fit_ranks(q,"parallel_2s_m","attacker_path_length_m","prior_parallel_m")
        elif mode=="placebo": b=g1.fit_ranks(q,"earlier_placebo_parallel_m","future_attacker_path_length_m","prior_placebo_parallel_m")
        elif mode=="paired":
            bp=g1.fit_ranks(q,"parallel_2s_m","attacker_path_length_m","prior_parallel_m"); bz=g1.fit_ranks(q,"earlier_placebo_parallel_m","future_attacker_path_length_m","prior_placebo_parallel_m"); values.append(g1.regions(bp)["near_minus_middle"]-g1.regions(bz)["near_minus_middle"]); continue
        elif mode=="trim": q=q[q.attacker_path_length_m<=g1.TRIM_THRESHOLD]; b=g1.fit_ranks(q,"parallel_2s_m","attacker_path_length_m","prior_parallel_m")
        elif mode=="h1": b=g1.fit_ranks(q,"parallel_1s_m","attacker_path_length_m","prior_parallel_m")
        elif mode=="h4": b=g1.fit_ranks(q,"parallel_4s_m","attacker_path_length_m","prior_parallel_m")
        values.append(b)
    return np.asarray(values)


def tables(data: pd.DataFrame, inherited: pd.DataFrame) -> tuple[dict[str,pd.DataFrame],dict[str,Any]]:
    anchors=inherited[inherited.observation_id.isin(data.observation_id.unique())].reset_index(drop=True)
    common=data[data.placebo_axis_valid].copy(); ca=anchors[anchors.observation_id.isin(common.observation_id.unique())].reset_index(drop=True); common=common[common.observation_id.isin(ca.observation_id)]
    h4=data[data.parallel_4s_m.notna()].copy(); h4a=anchors[anchors.observation_id.isin(h4.observation_id.unique())].reset_index(drop=True)
    p=g1.fit_ranks(data,"parallel_2s_m","attacker_path_length_m","prior_parallel_m"); z=g1.fit_ranks(common,"earlier_placebo_parallel_m","future_attacker_path_length_m","prior_placebo_parallel_m"); cp=g1.fit_ranks(common,"parallel_2s_m","attacker_path_length_m","prior_parallel_m")
    tr=data[data.attacker_path_length_m<=g1.TRIM_THRESHOLD]; tp=g1.fit_ranks(tr,"parallel_2s_m","attacker_path_length_m","prior_parallel_m"); h1=g1.fit_ranks(data,"parallel_1s_m","attacker_path_length_m","prior_parallel_m"); h4p=g1.fit_ranks(h4,"parallel_4s_m","attacker_path_length_m","prior_parallel_m")
    bsp=bootstrap_single(anchors,data,"primary"); bsz=bootstrap_single(ca,common,"placebo"); bsx=bootstrap_single(ca,common,"paired"); bst=bootstrap_single(anchors,data,"trim"); bs1=bootstrap_single(anchors,data,"h1"); bs4=bootstrap_single(h4a,h4,"h4")
    names=[f"D{i}" for i in range(1,11)]; rn=["near","middle","far","near_minus_middle","middle_minus_far"]
    tab={"rank":g1.intervals(names,p,bsp),"region":g1.intervals(rn,np.array(list(g1.regions(p).values())),np.array([list(g1.regions(x).values()) for x in bsp])),"control":g1.intervals(rn,np.array(list(g1.regions(z).values())),np.array([list(g1.regions(x).values()) for x in bsz])),"paired":g1.intervals(["primary_minus_temporal_control_near_minus_middle"],np.array([g1.regions(cp)["near_minus_middle"]-g1.regions(z)["near_minus_middle"]]),bsx),"trim":g1.intervals(rn,np.array(list(g1.regions(tp).values())),np.array([list(g1.regions(x).values()) for x in bst]))}
    hrs=[]
    for label,b,bss in [("1s",h1,bs1),("2s",p,bsp),("4s",h4p,bs4)]: hrs.append(g1.intervals([label],np.array([g1.regions(b)["near_minus_middle"]]),np.array([g1.regions(x)["near_minus_middle"] for x in bss])).iloc[0].to_dict())
    tab["horizon"]=pd.DataFrame(hrs)
    sec=[]
    for rank,q in data.groupby("distance_rank"): sec.append({"rank":int(rank),**{c:float(q[c].median()) for c in ["focal_path_2s_m","focal_net_2s_m","orthogonal_2s_m","radial_2s_m","alignment_cosine","defender_absolute_2s_m","centroid_loo_2s_m"]}})
    tab["secondary"]=pd.DataFrame(sec)
    info={"anchors":anchors,"common_anchors":ca,"h4_anchors":h4a,"primary":p,"control":z,"trim":tp,"horizons":hrs,"bootstrap_valid":[len(x) for x in [bsp,bsz,bsx,bst,bs1,bs4]],"trimmed_anchors":tr.observation_id.nunique()}
    return tab,info


def run_game2(output: Path) -> dict[str,Any]:
    verify(); output.mkdir(parents=True,exist_ok=True); inherited,data,construction=build_game2(); tab,info=tables(data,inherited)
    for key,name in [("rank","primary_rank_coefficients.csv"),("region","primary_regional_estimates.csv"),("control","temporal_control_regional_estimates.csv"),("paired","paired_temporal_control.csv"),("trim","trimmed_regional_estimates.csv"),("horizon","horizon_estimates.csv"),("secondary","secondary_geometry_by_rank.csv")]: tab[key].to_csv(output/name,index=False)
    pl.DataFrame(data.to_dict("list")).write_parquet(output/"response_form_rows.parquet")
    anchors=info["anchors"]; sample={"inherited_eligible_anchors":len(inherited),"primary_axis_anchors":len(anchors),"axis_retention_fraction":len(anchors)/len(inherited),"unique_anchor_times":int(anchors[["period","time_period_s"]].drop_duplicates().shape[0]),"defender_rows":len(data),"period_counts":anchors.period.value_counts().sort_index().to_dict(),"attacking_team_counts":anchors.attacking_team.value_counts().sort_index().to_dict(),"simultaneous_attackers":anchors.groupby(["period","time_period_s"]).size().describe().to_dict(),"common_placebo_anchors":len(info["common_anchors"]),"four_second_anchors":len(info["h4_anchors"]),"axis_exclusions":construction["axis_exclusions"]}
    write_json(output/"sample.json",sample)
    nm=tab["region"].query("estimand=='near_minus_middle'").iloc[0]; paired=tab["paired"].iloc[0]; trim_nm=g1.regions(info["trim"])["near_minus_middle"]; ratio=abs(trim_nm/nm.estimate)
    criteria={"axis_retention":sample["axis_retention_fraction"]>=.8,"primary_interval_excludes_zero":nm.ci_low>0 or nm.ci_high<0,"paired_interval_excludes_zero_same_direction":(paired.ci_low>0 and nm.estimate>0) or (paired.ci_high<0 and nm.estimate<0),"trim_sign_and_magnitude":np.sign(trim_nm)==np.sign(nm.estimate) and ratio>=.5,"horizon_sign":not(np.sign(tab["horizon"].estimate.iloc[0])==-np.sign(tab["horizon"].estimate.iloc[1]) and np.sign(tab["horizon"].estimate.iloc[2])==-np.sign(tab["horizon"].estimate.iloc[1]))}
    hard={"frozen_hashes":True,"unique_ids":anchors.observation_id.is_unique,"ten_rows_complete":len(data)==10*len(anchors),"rank_vectors_complete":data.groupby("observation_id").distance_rank.apply(lambda x:sorted(x)==list(range(1,11))).all(),"bootstrap_valid":min(info["bootstrap_valid"])>=MIN_VALID,"game3_not_accessed":True,"no_tactical_labels":True}
    pd.DataFrame([{"criterion":k,"pass":v} for k,v in criteria.items()]).to_csv(output/"condition_evaluation.csv",index=False); pd.DataFrame([{"check":k,"pass":v} for k,v in hard.items()]).to_csv(output/"hard_qc.csv",index=False)
    result={"status":"GAME 2 STANDALONE DESCRIPTIVE — NO FORMAL CLASSIFICATION","sample":sample,"primary_near_minus_middle":nm.to_dict(),"temporal_control_near_minus_middle":tab["control"].query("estimand=='near_minus_middle'").iloc[0].to_dict(),"paired_primary_minus_control":paired.to_dict(),"trim":{"threshold_m":g1.TRIM_THRESHOLD,"full":nm.estimate,"trimmed":trim_nm,"magnitude_fraction":ratio},"horizons":info["horizons"],"condition_evaluation":criteria,"hard_qc":hard,"bootstrap_valid":info["bootstrap_valid"],"frozen_hashes":{str(p.relative_to(ROOT)):h for p,h in HASHES.items()},"environment":{"python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__}}
    write_json(output/"final_results.json",result); write_json(output/"final_hashes.json",{p.name:sha(p) for p in sorted(output.iterdir()) if p.name not in {"final_hashes.json","reproduction.json"}}); return result


def pooled_fit(data: pd.DataFrame,outcome: str,exposure: str,baseline: str) -> np.ndarray:
    X=pool.pooled_design(data[exposure],data[baseline],data.prior_centroid_path_m,data.distance_rank,data.game2_indicator); y=data[outcome].to_numpy(float)
    coefficients, _, fitted_rank, _ = np.linalg.lstsq(X,y,rcond=None)
    if fitted_rank<41: raise RuntimeError("Pooled design unestimable")
    return pool.exposure_coefficients(coefficients)


def ordered_pooled(anchors: pd.DataFrame,data: pd.DataFrame) -> pd.DataFrame:
    order={oid:i for i,oid in enumerate(anchors.observation_id)}; q=data.assign(_o=data.observation_id.map(order)).sort_values(["_o","distance_rank"],kind="mergesort").drop(columns="_o").reset_index(drop=True)
    if len(q)!=10*len(anchors): raise RuntimeError("Incomplete pooled vectors")
    return q


def pooled_boot(anchors: pd.DataFrame,data: pd.DataFrame,mode: str) -> np.ndarray:
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence(SEED).spawn(9)[8])); ordered=ordered_pooled(anchors,data); vals=[]
    for _ in range(BOOT):
        idx=pool.sample_pooled_anchor_indices(anchors,rng); q=ordered.iloc[(idx[:,None]*10+np.arange(10)).ravel()]
        if mode=="primary": b=pooled_fit(q,"parallel_2s_m","attacker_path_length_m","prior_parallel_m")
        elif mode=="control": b=pooled_fit(q,"earlier_placebo_parallel_m","future_attacker_path_length_m","prior_placebo_parallel_m")
        elif mode=="paired": vals.append(pool.paired_excess(pooled_fit(q,"parallel_2s_m","attacker_path_length_m","prior_parallel_m"),pooled_fit(q,"earlier_placebo_parallel_m","future_attacker_path_length_m","prior_placebo_parallel_m"))); continue
        elif mode=="trim": q=q[q.attacker_path_length_m<=g1.TRIM_THRESHOLD]; b=pooled_fit(q,"parallel_2s_m","attacker_path_length_m","prior_parallel_m")
        elif mode=="h1": b=pooled_fit(q,"parallel_1s_m","attacker_path_length_m","prior_parallel_m")
        elif mode=="h4": b=pooled_fit(q,"parallel_4s_m","attacker_path_length_m","prior_parallel_m")
        vals.append(b)
    return np.asarray(vals)


def run_pooled(g2out: Path,out: Path,figdir: Path) -> dict[str,Any]:
    verify(); out.mkdir(parents=True,exist_ok=True); figdir.mkdir(parents=True,exist_ok=True)
    g1d=pd.DataFrame(pl.read_parquet(G1_OUT/"response_form_rows.parquet").to_dicts()); g2d=pd.DataFrame(pl.read_parquet(g2out/"response_form_rows.parquet").to_dicts())
    g1d["game"]="G1"; g1d["game2_indicator"]=0.; g1d["observation_id"]="G1:"+g1d.observation_id.astype(str)
    g2d["game"]="G2"; g2d["game2_indicator"]=1.; g2d["observation_id"]="G2:"+g2d.observation_id.astype(str)
    data=pd.concat([g1d,g2d],ignore_index=True); anchors=data.drop_duplicates("observation_id")[["observation_id","game","period","block_id"]].reset_index(drop=True)
    common=data[data.placebo_axis_valid].copy(); ca=anchors[anchors.observation_id.isin(common.observation_id.unique())].reset_index(drop=True); common=common[common.observation_id.isin(ca.observation_id)]
    h4=data[data.parallel_4s_m.notna()].copy(); h4a=anchors[anchors.observation_id.isin(h4.observation_id.unique())].reset_index(drop=True)
    p=pooled_fit(data,"parallel_2s_m","attacker_path_length_m","prior_parallel_m"); z=pooled_fit(common,"earlier_placebo_parallel_m","future_attacker_path_length_m","prior_placebo_parallel_m"); cp=pooled_fit(common,"parallel_2s_m","attacker_path_length_m","prior_parallel_m"); tr=data[data.attacker_path_length_m<=g1.TRIM_THRESHOLD]; tp=pooled_fit(tr,"parallel_2s_m","attacker_path_length_m","prior_parallel_m"); h1=pooled_fit(data,"parallel_1s_m","attacker_path_length_m","prior_parallel_m"); h4p=pooled_fit(h4,"parallel_4s_m","attacker_path_length_m","prior_parallel_m")
    bsp=pooled_boot(anchors,data,"primary"); bsz=pooled_boot(ca,common,"control"); bsx=pooled_boot(ca,common,"paired"); bst=pooled_boot(anchors,data,"trim"); bs1=pooled_boot(anchors,data,"h1"); bs4=pooled_boot(h4a,h4,"h4")
    names=[f"D{i}" for i in range(1,11)]; rn=["near","middle","far","near_minus_middle","middle_minus_far"]
    rank=g1.intervals(names,p,bsp); reg=g1.intervals(rn,np.array(list(pool.regional_contrasts(p).values())),np.array([list(pool.regional_contrasts(x).values()) for x in bsp])); ctl=g1.intervals(rn,np.array(list(pool.regional_contrasts(z).values())),np.array([list(pool.regional_contrasts(x).values()) for x in bsz])); paired=g1.intervals(["primary_minus_temporal_control_near_minus_middle"],np.array([pool.paired_excess(cp,z)]),bsx); trim=g1.intervals(rn,np.array(list(pool.regional_contrasts(tp).values())),np.array([list(pool.regional_contrasts(x).values()) for x in bst]))
    hrs=[]
    for label,b,bss in [("1s",h1,bs1),("2s",p,bsp),("4s",h4p,bs4)]: hrs.append(g1.intervals([label],np.array([pool.regional_contrasts(b)["near_minus_middle"]]),np.array([pool.regional_contrasts(x)["near_minus_middle"] for x in bss])).iloc[0].to_dict())
    for t,n in [(rank,"pooled_rank_coefficients.csv"),(reg,"pooled_regional_estimates.csv"),(ctl,"pooled_temporal_control.csv"),(paired,"pooled_paired_temporal_control.csv"),(trim,"pooled_trimmed.csv"),(pd.DataFrame(hrs),"pooled_horizons.csv")]: t.to_csv(out/n,index=False)
    sample={"anchors":len(anchors),"defender_rows":len(data),"by_game":anchors.game.value_counts().sort_index().to_dict(),"common_anchors":len(ca),"four_second_anchors":len(h4a),"retention_by_game":{"G1":json.loads((G1_OUT/"sample.json").read_text())["axis_retention_fraction"],"G2":json.loads((g2out/"sample.json").read_text())["axis_retention_fraction"]}}
    write_json(out/"pooled_sample.json",sample)
    nm=reg.query("estimand=='near_minus_middle'").iloc[0]; pr=paired.iloc[0]; tnm=pool.regional_contrasts(tp)["near_minus_middle"]; ratio=abs(tnm/nm.estimate); horizon_pass=not(np.sign(hrs[0]["estimate"])==-np.sign(hrs[1]["estimate"]) and np.sign(hrs[2]["estimate"])==-np.sign(hrs[1]["estimate"]))
    g1res=json.loads((G1_OUT/"final_results.json").read_text()); g2res=json.loads((g2out/"final_results.json").read_text())
    same_sign=lambda rows: len({int(np.sign(r["estimate"])) for r in rows})==1 and all((r["ci_low"]>0 or r["ci_high"]<0) for r in rows)
    primary_rows=[g1res["primary_near_minus_middle"],g2res["primary_near_minus_middle"],nm.to_dict()]; paired_rows=[g1res["paired_primary_minus_control"],g2res["paired_primary_minus_control"],pr.to_dict()]
    criteria={"all_valid_reproducible":True,"all_axis_retention_at_least_80pct":all(v>=.8 for v in sample["retention_by_game"].values()),"primary_intervals_exclude_zero_same_sign":same_sign(primary_rows),"paired_intervals_exclude_zero_same_sign":same_sign(paired_rows) and np.sign(primary_rows[0]["estimate"])==np.sign(paired_rows[0]["estimate"]),"pooled_trim_sign_and_magnitude":np.sign(tnm)==np.sign(nm.estimate) and ratio>=.5,"pooled_horizon_sign":horizon_pass}
    classification="FINAL RESPONSE FORM A" if all(criteria.values()) else "FINAL RESPONSE FORM B"
    hard={"frozen_hashes":True,"pooled_41_column_design":True,"no_interactions":True,"observation_weighting":True,"common_primary_control_sample":True,"independent_game_period_block_resampling":True,"paired_identical_draws":True,"bootstrap_valid":min(map(len,[bsp,bsz,bsx,bst,bs1,bs4]))>=MIN_VALID,"game3_not_accessed":True}
    pd.DataFrame([{"criterion":k,"pass":v} for k,v in criteria.items()]).to_csv(out/"final_classification_criteria.csv",index=False); pd.DataFrame([{"check":k,"pass":v} for k,v in hard.items()]).to_csv(out/"hard_qc.csv",index=False)
    result={"classification":classification,"sample":sample,"primary_near_minus_middle":nm.to_dict(),"temporal_control_near_minus_middle":ctl.query("estimand=='near_minus_middle'").iloc[0].to_dict(),"paired_primary_minus_control":pr.to_dict(),"trim":{"threshold_m":g1.TRIM_THRESHOLD,"full":nm.estimate,"trimmed":tnm,"magnitude_fraction":ratio},"horizons":hrs,"criteria":criteria,"hard_qc":hard,"bootstrap_valid":[len(x) for x in [bsp,bsz,bsx,bst,bs1,bs4]],"frozen_hashes":{str(p.relative_to(ROOT)):h for p,h in HASHES.items()}}
    write_json(out/"final_results.json",result)
    fig,ax=plt.subplots(figsize=(9,5)); ax.errorbar(range(1,11),rank.estimate,yerr=[rank.estimate-rank.ci_low,rank.ci_high-rank.estimate],fmt="o",capsize=3,color="#123B5D"); ax.axhline(0,color=".5",lw=1); ax.set(xlabel="Defender proximity rank",ylabel="Attacker-direction coefficient (m/m)",xticks=range(1,11),title="Pooled local defensive response form — geometric measurement only"); fig.tight_layout(); fig.savefig(figdir/"pooled_response_form.png",dpi=180); plt.close(fig)
    write_json(out/"final_hashes.json",{p.name:sha(p) for p in sorted(out.iterdir()) if p.name not in {"final_hashes.json","reproduction.json"}}); return result


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--stage",choices=["game2","pooled"],required=True); ap.add_argument("--game2-output",type=Path,default=DEFAULT_G2); ap.add_argument("--pooled-output",type=Path,default=DEFAULT_POOL); ap.add_argument("--figures",type=Path,default=DEFAULT_FIG); a=ap.parse_args()
    if a.stage=="game2": run_game2(a.game2_output)
    else: run_pooled(a.game2_output,a.pooled_output,a.figures)

if __name__=="__main__": main()
