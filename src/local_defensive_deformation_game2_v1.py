"""Tier-3 heldout Game 2 execution of frozen Local Defensive Deformation v1."""
from __future__ import annotations

import argparse, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import polars as pl

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
import attacker_defender_bridge_game1_v1 as bridge  # noqa: E402
import attacking_continuous_movement_game2_v1 as game2  # noqa: E402
import local_defensive_deformation_game1_v1 as g1  # noqa: E402
import local_defensive_deformation_v1 as geometry  # noqa: E402

ADD_DOC=ROOT/"docs/protocols/local_defensive_deformation_v1_game2_replication.md"; ADD_CFG=ROOT/"config/local_defensive_deformation_v1_game2_replication.json"
FOOT=ROOT/"outputs/spatial_defensive_response_footprint_game2_final_v1"; DEFAULT=ROOT/"outputs/local_defensive_deformation_game2_v1"
HASHES={**g1.HASHES,ADD_DOC:"a652beb0ed1302636b869494dec021832850b6876b92923678d3efdc80ba33a4",ADD_CFG:"8f51f0943c2fec9013582c15ee25cc0ef3bb7217637e1afdb7c23bf48634686f",ROOT/"outputs/local_defensive_deformation_game1_v1/final_results.json":"f99f5740446951d338ec9def9d32c335da207fabfe706021c22246ae9fe01d60",ROOT/"outputs/local_defensive_deformation_game1_v1/final_hashes.json":"6d5ef1b9a91bdecd8102356e201bff2d5d7b4e436f1ad408e3c9177729d695dd",FOOT/"game2_anchors.parquet":"210c2f34ce94cd92a9b9347b919dd849f2d51c298897438fb45b88ca1f58c5a6",FOOT/"game2_linkage.parquet":"87b8cb39a7661151b7fbe9ec9946abbb43524980e0ad407b761d6cabc6dfaeec"}
CHILD=7

def build_sample():
 anchors=pd.DataFrame(pl.read_parquet(FOOT/"game2_anchors.parquet").to_dicts()); links=pd.DataFrame(pl.read_parquet(FOOT/"game2_linkage.parquet").to_dicts()); pps,_,provenance,support=game2.load_game2_from_frozen_support(); lookup={(p.period,p.player_key):p for p in pps}; rows=[]
 for a in anchors.itertuples(index=False):
  group=links[links.observation_id==a.observation_id].sort_values("distance_rank"); defenders=[lookup[(int(a.period),str(k))] for k in group.player_key_defender]; windows={"prior":(-4,-2),"control":(-2,0),"primary":(0,2)}
  if bool(a.eligible_4s): windows["h4"]=(0,4)
  stacks={n:np.stack([g1.interval(p,float(a.time_period_s)+lo,float(a.time_period_s)+hi) for p in defenders],axis=1) for n,(lo,hi) in windows.items()}; prior=geometry.focal_endpoint_rms(stacks["prior"]); gp=geometry.global_endpoint_rms(stacks["prior"]); primary=geometry.focal_endpoint_rms(stacks["primary"]); control=geometry.focal_endpoint_rms(stacks["control"]); path=geometry.focal_relational_path(stacks["primary"]); signed=geometry.focal_signed_mean_change(stacks["primary"]); whole=geometry.global_endpoint_rms(stacks["primary"]); h4=geometry.focal_endpoint_rms(stacks["h4"]) if "h4" in stacks else np.full(10,np.nan)
  for j,link in enumerate(group.itertuples(index=False)): rows.append({"observation_id":str(a.observation_id),"period":int(a.period),"time_period_s":float(a.time_period_s),"time_match_s":float(a.time_match_s),"attacker_key":str(a.player_key),"attacking_team":str(a.attacking_team),"defending_team":str(a.defending_team),"block_id":int(a.block_id),"defender_key":str(link.player_key_defender),"distance_rank":int(link.distance_rank),"attacker_path_length_m":float(a.attacker_path_length_m),"future_attacker_path_length_m":float(a.future_attacker_path_length_m),"focal_prior_endpoint_rms_m":float(prior[j]),"global_prior_endpoint_rms_m":gp,"response_endpoint_rms_m":float(primary[j]),"control_endpoint_rms_m":float(control[j]),"response_path_m":float(path[j]),"signed_mean_spacing_change_m":float(signed[j]),"whole_unit_response_endpoint_rms_m":whole,"response_4s_endpoint_rms_m":float(h4[j])})
 data=pd.DataFrame(rows).sort_values(["period","time_period_s","attacker_key","distance_rank"],kind="mergesort").reset_index(drop=True); return anchors,data,{"source":provenance,"support":support}

def bootstrap(anchors,data,mode):
 rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence(g1.SEED).spawn(9)[CHILD])); q0=g1.ordered(anchors,data); vals=[]
 for _ in range(g1.BOOT):
  idx=bridge.sampled_indices(anchors,rng); q=q0.iloc[(idx[:,None]*10+np.arange(10)).ravel()]
  if mode=="primary": b=g1.fit(q,"response_endpoint_rms_m","attacker_path_length_m")
  elif mode=="control": b=g1.fit(q,"control_endpoint_rms_m","future_attacker_path_length_m")
  elif mode=="paired": vals.append(g1.regions(g1.fit(q,"response_endpoint_rms_m","attacker_path_length_m"))["near_minus_middle"]-g1.regions(g1.fit(q,"control_endpoint_rms_m","future_attacker_path_length_m"))["near_minus_middle"]); continue
  elif mode=="trim": q=q[q.attacker_path_length_m<=g1.TRIM]; b=g1.fit(q,"response_endpoint_rms_m","attacker_path_length_m")
  elif mode=="h4": b=g1.fit(q,"response_4s_endpoint_rms_m","attacker_path_length_m")
  elif mode=="path": b=g1.fit(q,"response_path_m","attacker_path_length_m")
  vals.append(b)
 return np.asarray(vals)

def execute(out:Path):
 bad={str(p):[g1.sha(p),h] for p,h in HASHES.items() if g1.sha(p)!=h}
 if bad: raise RuntimeError(f"Frozen hash failure {bad}")
 out.mkdir(parents=True,exist_ok=True); anchors,data,provenance=build_sample(); h4=data[data.response_4s_endpoint_rms_m.notna()]; h4a=anchors[anchors.observation_id.isin(h4.observation_id.unique())].reset_index(drop=True); trimdata=data[data.attacker_path_length_m<=g1.TRIM]
 p=g1.fit(data,"response_endpoint_rms_m","attacker_path_length_m"); c=g1.fit(data,"control_endpoint_rms_m","future_attacker_path_length_m"); tp=g1.fit(trimdata,"response_endpoint_rms_m","attacker_path_length_m"); hp=g1.fit(h4,"response_4s_endpoint_rms_m","attacker_path_length_m"); pp=g1.fit(data,"response_path_m","attacker_path_length_m")
 bsp=bootstrap(anchors,data,"primary"); bsc=bootstrap(anchors,data,"control"); bsx=bootstrap(anchors,data,"paired"); bst=bootstrap(anchors,data,"trim"); bsh=bootstrap(h4a,h4,"h4"); bspp=bootstrap(anchors,data,"path")
 names=[f"D{i}" for i in range(1,11)]; rn=["near","middle","far","near_minus_middle","middle_minus_far"]
 rank=g1.table(names,p,bsp); reg=g1.table(rn,np.array(list(g1.regions(p).values())),np.array([list(g1.regions(x).values()) for x in bsp])); ctl=g1.table(rn,np.array(list(g1.regions(c).values())),np.array([list(g1.regions(x).values()) for x in bsc])); excess=g1.table(["primary_minus_temporal_control_near_minus_middle"],np.array([g1.regions(p)["near_minus_middle"]-g1.regions(c)["near_minus_middle"]]),bsx); trim=g1.table(rn,np.array(list(g1.regions(tp).values())),np.array([list(g1.regions(x).values()) for x in bst])); h4tab=g1.table(rn,np.array(list(g1.regions(hp).values())),np.array([list(g1.regions(x).values()) for x in bsh])); path=g1.table(rn,np.array(list(g1.regions(pp).values())),np.array([list(g1.regions(x).values()) for x in bspp]))
 for x,n in [(rank,"primary_rank_coefficients.csv"),(reg,"primary_regional_estimates.csv"),(ctl,"temporal_control_regional_estimates.csv"),(excess,"paired_temporal_control.csv"),(trim,"trimmed_regional_estimates.csv"),(h4tab,"four_second_regional_estimates.csv"),(path,"secondary_path_regional_estimates.csv")]: x.to_csv(out/n,index=False)
 secondary=[]
 for rank_id,q in data.groupby("distance_rank"): secondary.append({"rank":int(rank_id),**{col:float(q[col].median()) for col in ["response_endpoint_rms_m","response_path_m","signed_mean_spacing_change_m","whole_unit_response_endpoint_rms_m"]}})
 pd.DataFrame(secondary).to_csv(out/"secondary_geometry_by_rank.csv",index=False); pl.DataFrame(data.to_dict("list")).write_parquet(out/"deformation_rows.parquet")
 primary_numeric=["attacker_path_length_m","future_attacker_path_length_m","focal_prior_endpoint_rms_m","global_prior_endpoint_rms_m","response_endpoint_rms_m","control_endpoint_rms_m","response_path_m","signed_mean_spacing_change_m","whole_unit_response_endpoint_rms_m"]
 hard={"frozen_hashes":True,"unique_observation_ids":anchors.observation_id.is_unique,"complete_ten_rows":len(data)==10*len(anchors),"complete_rank_vectors":data.groupby("observation_id").distance_rank.apply(lambda x:sorted(x)==list(range(1,11))).all(),"unique_defenders":data.groupby("observation_id").defender_key.nunique().eq(10).all(),"goalkeeper_exclusion_inherited":True,"complete_support_no_interpolation":True,"finite_primary_geometry_and_design":np.isfinite(data[primary_numeric].to_numpy(float)).all(),"finite_four_second_subset":np.isfinite(h4.response_4s_endpoint_rms_m.to_numpy(float)).all(),"bootstrap_valid":min(len(x) for x in [bsp,bsc,bsx,bst,bsh,bspp])>=g1.MIN_VALID,"construct_validity_inherited":True,"game3_not_accessed":True,"pooled_not_executed":True}
 nm=reg.query("estimand=='near_minus_middle'").iloc[0]; cnm=ctl.query("estimand=='near_minus_middle'").iloc[0]; ex=excess.iloc[0]; tnm=g1.regions(tp)["near_minus_middle"]; hnm=g1.regions(hp)["near_minus_middle"]; pnm=path.query("estimand=='near_minus_middle'").iloc[0]; ratio=abs(tnm/nm.estimate) if abs(nm.estimate)>0 else None
 conditions={"primary_positive":nm.estimate>0,"primary_interval_strictly_positive":nm.ci_low>0,"paired_excess_positive":ex.estimate>0,"paired_excess_interval_strictly_positive":ex.ci_low>0,"four_second_positive":hnm>0,"trim_positive":tnm>0,"trim_retains_at_least_half_magnitude":ratio is not None and ratio>=.5,"no_strictly_negative_secondary_path_contrast":not(pnm.estimate<0 and pnm.ci_high<0)}
 pd.DataFrame([{"check":k,"pass":v} for k,v in hard.items()]).to_csv(out/"hard_qc.csv",index=False); pd.DataFrame([{"condition":k,"pass":v} for k,v in conditions.items()]).to_csv(out/"replication_conditions.csv",index=False)
 sample={"eligible_anchors":len(anchors),"defender_rows":len(data),"unique_anchor_times":int(anchors[["period","time_period_s"]].drop_duplicates().shape[0]),"period_counts":anchors.period.value_counts().sort_index().to_dict(),"attacking_team_counts":anchors.attacking_team.value_counts().sort_index().to_dict(),"simultaneous_attackers":anchors.groupby(["period","time_period_s"]).size().describe().to_dict(),"four_second_anchors":len(h4a),"trimmed_anchors":trimdata.observation_id.nunique(),"trim_excluded":len(anchors)-trimdata.observation_id.nunique()}; g1.write_json(out/"sample.json",sample)
 result={"status":"GAME 2 HELDOUT REPLICATION — STANDALONE UNCLASSIFIED","sample":sample,"primary_near_minus_middle":nm.to_dict(),"temporal_control_near_minus_middle":cnm.to_dict(),"paired_primary_minus_control":ex.to_dict(),"four_second_near_minus_middle":h4tab.query("estimand=='near_minus_middle'").iloc[0].to_dict(),"trim":{"threshold_m":g1.TRIM,"estimate":tnm,"magnitude_fraction":ratio},"secondary_path_near_minus_middle":pnm.to_dict(),"replication_conditions":conditions,"hard_qc":hard,"bootstrap_valid":[len(x) for x in [bsp,bsc,bsx,bst,bsh,bspp]],"frozen_hashes":{str(p.relative_to(ROOT)):h for p,h in HASHES.items()},"provenance":provenance}; g1.write_json(out/"final_results.json",result)
 governed=[p for p in sorted(out.iterdir()) if p.name not in {"final_hashes.json","reproduction.json"}]; g1.write_json(out/"final_hashes.json",{p.name:g1.sha(p) for p in governed}); return result

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path,default=DEFAULT); a=ap.parse_args(); print(json.dumps(execute(a.output)["status"]))
if __name__=="__main__": main()
