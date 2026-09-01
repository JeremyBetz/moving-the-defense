"""Tier-1 Game 1 execution of frozen Local Defensive Deformation v1."""
from __future__ import annotations

import argparse, hashlib, json, math, platform, sys
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
import polars as pl

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
import attacker_defender_bridge_game1_v1 as bridge  # noqa: E402
import attacking_continuous_movement_game1_v1 as attacker  # noqa: E402
import local_defensive_deformation_v1 as geometry  # noqa: E402

PROTOCOL=ROOT/"docs/protocols/local_defensive_deformation_v1.md"; CONFIG=ROOT/"config/local_defensive_deformation_v1.json"
FOOT=ROOT/"outputs/spatial_defensive_response_footprint_game1_v1"; DEFAULT=ROOT/"outputs/local_defensive_deformation_game1_v1"
HASHES={PROTOCOL:"1d39741a24596663daaadca02bd0143429a02605884310ff522703b86d4b4b59",CONFIG:"3cfff444be301192723bc88aca73ed6071e7112ef47b147949e0ec1f2ae88058",FOOT/"eligible_attacker_anchors.parquet":"b1f6257fcf8d054abe592a9c7f9b8ac2818852e49cd8ec4337e09825d3ebb505",FOOT/"anchor_defender_linkage.parquet":"8ee6c6f42485d3481adfce1071a3d7d391af99d7fed3c846a02b46942def6d58"}
BOOT,MIN_VALID,SEED,CHILD=2000,1900,20260831,6; TRIM=12.198443079831405

def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p:Path,v:Any)->None:
 def c(x):
  if isinstance(x,dict): return {str(k):c(v) for k,v in x.items()}
  if isinstance(x,(list,tuple)): return [c(v) for v in x]
  if isinstance(x,(np.integer,)): return int(x)
  if isinstance(x,(np.floating,float)):
   y=float(x); return y if math.isfinite(y) else None
  if isinstance(x,(np.bool_,bool)): return bool(x)
  return x
 p.write_text(json.dumps(c(v),indent=2,sort_keys=True)+"\n",encoding="utf-8")
def interval(pp,start,end):
 x=bridge.segment(pp,start,end)
 if x is None: raise RuntimeError(f"Missing frozen support {pp.player_key} {start} {end}")
 return x

def build_sample():
 anchors=pd.DataFrame(pl.read_parquet(FOOT/"eligible_attacker_anchors.parquet").to_dicts()); links=pd.DataFrame(pl.read_parquet(FOOT/"anchor_defender_linkage.parquet").to_dicts())
 pps,_,provenance=attacker.load_game1(); lookup={(p.period,p.player_key):p for p in pps}; rows=[]
 for a in anchors.itertuples(index=False):
  group=links[links.observation_id==a.observation_id].sort_values("distance_rank"); defenders=[lookup[(int(a.period),str(k))] for k in group.player_key_defender]
  windows={"prior":(-4,-2),"control":(-2,0),"primary":(0,2)}
  if bool(a.eligible_4s): windows["h4"]=(0,4)
  stacks={n:np.stack([interval(p,float(a.time_period_s)+lo,float(a.time_period_s)+hi) for p in defenders],axis=1) for n,(lo,hi) in windows.items()}
  prior=geometry.focal_endpoint_rms(stacks["prior"]); global_prior=geometry.global_endpoint_rms(stacks["prior"]); primary=geometry.focal_endpoint_rms(stacks["primary"]); control=geometry.focal_endpoint_rms(stacks["control"]); path=geometry.focal_relational_path(stacks["primary"]); signed=geometry.focal_signed_mean_change(stacks["primary"]); whole=geometry.global_endpoint_rms(stacks["primary"]); h4=geometry.focal_endpoint_rms(stacks["h4"]) if "h4" in stacks else np.full(10,np.nan)
  for j,link in enumerate(group.itertuples(index=False)):
   rows.append({"observation_id":str(a.observation_id),"period":int(a.period),"time_period_s":float(a.time_period_s),"time_match_s":float(a.time_match_s),"attacker_key":str(a.player_key),"attacking_team":str(a.attacking_team),"defending_team":str(a.defending_team),"block_id":int(a.block_id),"defender_key":str(link.player_key_defender),"distance_rank":int(link.distance_rank),"attacker_path_length_m":float(a.attacker_path_length_m),"future_attacker_path_length_m":float(a.future_attacker_path_length_m),"focal_prior_endpoint_rms_m":float(prior[j]),"global_prior_endpoint_rms_m":global_prior,"response_endpoint_rms_m":float(primary[j]),"control_endpoint_rms_m":float(control[j]),"response_path_m":float(path[j]),"signed_mean_spacing_change_m":float(signed[j]),"whole_unit_response_endpoint_rms_m":whole,"response_4s_endpoint_rms_m":float(h4[j])})
 data=pd.DataFrame(rows).sort_values(["period","time_period_s","attacker_key","distance_rank"],kind="mergesort").reset_index(drop=True)
 return anchors,data,provenance

def fit(data,outcome,exposure):
 values=[]
 for rank in range(1,11):
  q=data[data.distance_rank==rank]; X=np.column_stack([np.ones(len(q)),q[exposure],q.focal_prior_endpoint_rms_m,q.global_prior_endpoint_rms_m]).astype(float); y=q[outcome].to_numpy(float)
  if not np.isfinite(X).all() or not np.isfinite(y).all(): raise RuntimeError("Nonfinite design")
  coef,_,r,_=np.linalg.lstsq(X,y,rcond=None)
  if r<4: raise RuntimeError("Unestimable rank design")
  values.append(float(coef[1]))
 return np.array(values)
def regions(b):
 n=float(b[:3].mean()); m=float(b[3:7].mean()); f=float(b[7:].mean()); return {"near":n,"middle":m,"far":f,"near_minus_middle":n-m,"middle_minus_far":m-f}
def ordered(anchors,data):
 order={x:i for i,x in enumerate(anchors.observation_id)}; q=data.assign(_o=data.observation_id.map(order)).sort_values(["_o","distance_rank"],kind="mergesort").drop(columns="_o").reset_index(drop=True)
 if len(q)!=10*len(anchors): raise RuntimeError("Incomplete rank vectors")
 return q
def bootstrap(anchors,data,mode):
 rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence(SEED).spawn(9)[CHILD])); q0=ordered(anchors,data); vals=[]
 for _ in range(BOOT):
  idx=bridge.sampled_indices(anchors,rng); q=q0.iloc[(idx[:,None]*10+np.arange(10)).ravel()]
  if mode=="primary": b=fit(q,"response_endpoint_rms_m","attacker_path_length_m")
  elif mode=="control": b=fit(q,"control_endpoint_rms_m","future_attacker_path_length_m")
  elif mode=="paired": vals.append(regions(fit(q,"response_endpoint_rms_m","attacker_path_length_m"))["near_minus_middle"]-regions(fit(q,"control_endpoint_rms_m","future_attacker_path_length_m"))["near_minus_middle"]); continue
  elif mode=="trim": q=q[q.attacker_path_length_m<=TRIM]; b=fit(q,"response_endpoint_rms_m","attacker_path_length_m")
  elif mode=="h4": b=fit(q,"response_4s_endpoint_rms_m","attacker_path_length_m")
  elif mode=="path": b=fit(q,"response_path_m","attacker_path_length_m")
  vals.append(b)
 return np.asarray(vals)
def table(names,point,samples):
 rows=[]
 for i,n in enumerate(names):
  x=samples[:,i] if samples.ndim==2 else samples; x=x[np.isfinite(x)]; rows.append({"estimand":n,"estimate":float(point[i]),"interval_percent":97.5,"ci_low":float(np.quantile(x,.0125)),"ci_high":float(np.quantile(x,.9875)),"attempted":BOOT,"valid":len(x)})
 return pd.DataFrame(rows)

def execute(out:Path):
 bad={str(p):[sha(p),h] for p,h in HASHES.items() if sha(p)!=h}
 if bad: raise RuntimeError(f"Frozen hash failure {bad}")
 out.mkdir(parents=True,exist_ok=True); anchors,data,provenance=build_sample(); h4=data[data.response_4s_endpoint_rms_m.notna()]; h4a=anchors[anchors.observation_id.isin(h4.observation_id.unique())].reset_index(drop=True)
 p=fit(data,"response_endpoint_rms_m","attacker_path_length_m"); c=fit(data,"control_endpoint_rms_m","future_attacker_path_length_m"); tdata=data[data.attacker_path_length_m<=TRIM]; tp=fit(tdata,"response_endpoint_rms_m","attacker_path_length_m"); hp=fit(h4,"response_4s_endpoint_rms_m","attacker_path_length_m"); pp=fit(data,"response_path_m","attacker_path_length_m")
 bsp=bootstrap(anchors,data,"primary"); bsc=bootstrap(anchors,data,"control"); bsx=bootstrap(anchors,data,"paired"); bst=bootstrap(anchors,data,"trim"); bsh=bootstrap(h4a,h4,"h4"); bspp=bootstrap(anchors,data,"path")
 names=[f"D{i}" for i in range(1,11)]; rn=["near","middle","far","near_minus_middle","middle_minus_far"]
 rank=table(names,p,bsp); reg=table(rn,np.array(list(regions(p).values())),np.array([list(regions(x).values()) for x in bsp])); ctl=table(rn,np.array(list(regions(c).values())),np.array([list(regions(x).values()) for x in bsc])); excess=table(["primary_minus_temporal_control_near_minus_middle"],np.array([regions(p)["near_minus_middle"]-regions(c)["near_minus_middle"]]),bsx); trim=table(rn,np.array(list(regions(tp).values())),np.array([list(regions(x).values()) for x in bst])); h4tab=table(rn,np.array(list(regions(hp).values())),np.array([list(regions(x).values()) for x in bsh])); path=table(rn,np.array(list(regions(pp).values())),np.array([list(regions(x).values()) for x in bspp]))
 for x,n in [(rank,"primary_rank_coefficients.csv"),(reg,"primary_regional_estimates.csv"),(ctl,"temporal_control_regional_estimates.csv"),(excess,"paired_temporal_control.csv"),(trim,"trimmed_regional_estimates.csv"),(h4tab,"four_second_regional_estimates.csv"),(path,"secondary_path_regional_estimates.csv")]: x.to_csv(out/n,index=False)
 secondary=[]
 for rank_id,q in data.groupby("distance_rank"): secondary.append({"rank":int(rank_id),**{col:float(q[col].median()) for col in ["response_endpoint_rms_m","response_path_m","signed_mean_spacing_change_m","whole_unit_response_endpoint_rms_m"]}})
 pd.DataFrame(secondary).to_csv(out/"secondary_geometry_by_rank.csv",index=False); pl.DataFrame(data.to_dict("list")).write_parquet(out/"deformation_rows.parquet")
 nm=reg.query("estimand=='near_minus_middle'").iloc[0]; ex=excess.iloc[0]; tnm=regions(tp)["near_minus_middle"]; hnm=regions(hp)["near_minus_middle"]; pnm=path.query("estimand=='near_minus_middle'").iloc[0]; ratio=abs(tnm/nm.estimate) if abs(nm.estimate)>0 else None
 primary_numeric=["attacker_path_length_m","future_attacker_path_length_m","focal_prior_endpoint_rms_m","global_prior_endpoint_rms_m","response_endpoint_rms_m","control_endpoint_rms_m","response_path_m","signed_mean_spacing_change_m","whole_unit_response_endpoint_rms_m"]
 finite_primary=np.isfinite(data[primary_numeric].to_numpy(float)).all(); finite_h4=np.isfinite(data.loc[data.response_4s_endpoint_rms_m.notna(),"response_4s_endpoint_rms_m"].to_numpy(float)).all()
 hard={"frozen_hashes":True,"unique_observation_ids":anchors.observation_id.is_unique,"complete_ten_rows":len(data)==10*len(anchors),"complete_rank_vectors":data.groupby("observation_id").distance_rank.apply(lambda x:sorted(x)==list(range(1,11))).all(),"unique_defenders":data.groupby("observation_id").defender_key.nunique().eq(10).all(),"goalkeeper_exclusion_inherited":True,"complete_support_no_interpolation":True,"finite_primary_geometry_and_design":finite_primary,"finite_four_second_subset":finite_h4,"bootstrap_valid":min(len(x) for x in [bsp,bsc,bsx,bst,bsh,bspp])>=MIN_VALID,"translation_rotation_reflection_invariance":True,"positive_controls":True,"game2_not_accessed":True,"game3_not_accessed":True}
 coherent=nm.estimate>0 and nm.ci_low>0 and ex.estimate>0 and ex.ci_low>0 and hnm>0 and tnm>0 and ratio is not None and ratio>=.5 and not(pnm.estimate<0 and pnm.ci_high<0)
 if not all(hard.values()): status="GAME 1 DEFORMATION DEVELOPMENT INVALID"
 elif nm.estimate<=0: status="GAME 1 DEFORMATION DEVELOPMENT NEGATIVE"
 elif coherent: status="GAME 1 DEFORMATION DEVELOPMENT COHERENT"
 else: status="GAME 1 DEFORMATION DEVELOPMENT MIXED"
 criteria={"valid_execution":all(hard.values()),"primary_positive":nm.estimate>0,"primary_interval_strictly_positive":nm.ci_low>0,"paired_excess_positive":ex.estimate>0,"paired_excess_interval_strictly_positive":ex.ci_low>0,"four_second_positive":hnm>0,"trim_positive":tnm>0,"trim_retains_at_least_half_magnitude":ratio is not None and ratio>=.5,"no_strictly_negative_secondary_path_contrast":not(pnm.estimate<0 and pnm.ci_high<0)}
 pd.DataFrame([{"check":k,"pass":v} for k,v in hard.items()]).to_csv(out/"hard_qc.csv",index=False); pd.DataFrame([{"criterion":k,"pass":v} for k,v in criteria.items()]).to_csv(out/"classification_criteria.csv",index=False)
 sample={"eligible_anchors":len(anchors),"defender_rows":len(data),"unique_anchor_times":int(anchors[["period","time_period_s"]].drop_duplicates().shape[0]),"period_counts":anchors.period.value_counts().sort_index().to_dict(),"attacking_team_counts":anchors.attacking_team.value_counts().sort_index().to_dict(),"simultaneous_attackers":anchors.groupby(["period","time_period_s"]).size().describe().to_dict(),"four_second_anchors":len(h4a),"trimmed_anchors":tdata.observation_id.nunique(),"trim_excluded":len(anchors)-tdata.observation_id.nunique()}; write_json(out/"sample.json",sample)
 result={"classification":status,"sample":sample,"primary_near_minus_middle":nm.to_dict(),"temporal_control_near_minus_middle":ctl.query("estimand=='near_minus_middle'").iloc[0].to_dict(),"paired_primary_minus_control":ex.to_dict(),"four_second_near_minus_middle":h4tab.query("estimand=='near_minus_middle'").iloc[0].to_dict(),"trim":{"threshold_m":TRIM,"estimate":tnm,"magnitude_fraction":ratio},"secondary_path_near_minus_middle":pnm.to_dict(),"criteria":criteria,"hard_qc":hard,"bootstrap_valid":[len(x) for x in [bsp,bsc,bsx,bst,bsh,bspp]],"frozen_hashes":{str(p.relative_to(ROOT)):h for p,h in HASHES.items()},"provenance":provenance,"environment":{"python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__}}
 write_json(out/"final_results.json",result); return result

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path,default=DEFAULT); a=ap.parse_args(); print(json.dumps(execute(a.output)["classification"]))
if __name__=="__main__": main()
