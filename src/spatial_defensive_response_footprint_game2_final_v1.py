"""Execute frozen footprint v1 on Game 2, then pooled Games 1+2."""
from __future__ import annotations
import argparse, hashlib, json, math, platform
from pathlib import Path
import numpy as np, pandas as pd, polars as pl
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import spatial_defensive_response_footprint_game1_v1 as f1
import attacker_defender_bridge_game2_v1 as b2

ROOT=Path(__file__).resolve().parents[1]
CLAR=ROOT/"docs/protocols/spatial_defensive_response_footprint_v1_execution_clarification.md"
G1OUT=ROOT/"outputs/spatial_defensive_response_footprint_game1_v1"
OUT=ROOT/"outputs/spatial_defensive_response_footprint_game2_final_v1"
FIG=ROOT/"figures/spatial_defensive_response_footprint_game2_final_v1"
CLAR_HASH="60678b0f90128c5905ed2535a81aab37b562fe8a6b8aa6a9c9ff1f7642dcf37e"
G1_RESULT_HASH="a17ed8b68be79d05992202de88b08a78baf72989352153a135e3ce23863383e6"
G1_LEDGER_HASH="ac0fb093470b81c922010068b762fc534236c56c1c2c5cb30cdcc6b2d970cbbd"

def prepare2():
    a,l,e,c,p,_=b2.build_game2_observations()
    base=a[["observation_id","period","time_period_s","time_match_s","player_key","attacking_team","defending_team","block_id","attacker_path_length_m","future_attacker_path_length_m","prior_defending_centroid_path_m","eligible_4s"]]
    z=l.merge(base,on=["observation_id","period","time_period_s"],how="left",validate="many_to_one").rename(columns={"defender_key":"player_key_defender"})
    z["distance_band"]=z.distance_m.map(f1.band_label)
    return a,z.sort_values(["period","time_period_s","player_key","distance_rank"],kind="mergesort").reset_index(drop=True),e,c,p

def fit_rank(z,outcome,exposure,trim=False,pooled=False):
    beta=[]; coef=[]
    for rank in range(1,11):
        q=z[z.distance_rank==rank]
        if trim:q=q[q.attacker_path_length_m<=f1.TRIM_THRESHOLD]
        x=f1.design(q[exposure].to_numpy(float),q.prior_relative_path_m.to_numpy(float),q.prior_defending_centroid_path_m.to_numpy(float))
        if pooled:x=np.column_stack([x,q.game2_indicator.to_numpy(float)])
        c=np.linalg.lstsq(x,q[outcome].to_numpy(float),rcond=None)[0]
        coef.append(c);beta.append(c[1])
    return np.array(beta),np.array(coef)

def fit_metric(z,outcome="response_2s_m",pooled=False):
    labels=[];beta=[]
    for lo,hi in f1.BANDS:
        label=f1.band_label(lo);q=z[(z.distance_m>=lo)&(z.distance_m<hi)]
        x=f1.design(q.attacker_path_length_m.to_numpy(float),q.prior_relative_path_m.to_numpy(float),q.prior_defending_centroid_path_m.to_numpy(float))
        if pooled:x=np.column_stack([x,q.game2_indicator.to_numpy(float)])
        c=np.linalg.lstsq(x,q[outcome].to_numpy(float),rcond=None)[0];labels.append(label);beta.append(c[1])
    return labels,np.array(beta)

def sample_pooled(a,rng):
    out=[]
    for game in sorted(a.game.unique()):
      for period in sorted(a.loc[a.game==game,"period"].unique()):
        q=a[(a.game==game)&(a.period==period)];blocks=sorted(q.block_id.unique())
        for draw in rng.integers(0,len(blocks),size=len(blocks)):out.append(q.index[q.block_id==blocks[int(draw)]].to_numpy())
    return np.concatenate(out)

def bootstrap(a,z,child,pooled=False):
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence(f1.MASTER_SEED).spawn(6)[child]));ordered=f1.ordered_linkage(a,z);w=np.arange(10)
    rp=[];rz=[];r1=[];rt=[];met=[]
    for _ in range(f1.BOOTSTRAPS):
        idx=sample_pooled(a,rng) if pooled else b2.g1.sampled_indices(a,rng);q=ordered.iloc[(idx[:,None]*10+w).ravel()].reset_index(drop=True)
        bp,_=fit_rank(q,"response_2s_m","attacker_path_length_m",pooled=pooled);bz,_=fit_rank(q,"earlier_relative_path_m","future_attacker_path_length_m",pooled=pooled);b1,_=fit_rank(q,"response_1s_m","attacker_path_length_m",pooled=pooled);bt,_=fit_rank(q,"response_2s_m","attacker_path_length_m",True,pooled)
        rp.append(list(f1.regional(bp).values()));rz.append(list(f1.regional(bz).values()));r1.append(list(f1.regional(b1).values()));rt.append(list(f1.regional(bt).values()));met.append(fit_metric(q,pooled=pooled)[1])
    return {"rp":np.array(rp),"rz":np.array(rz),"r1":np.array(r1),"rt":np.array(rt),"met":np.array(met)}

def bootstrap4(a,z,child,pooled=False):
    ok=z.groupby("observation_id").response_4s_m.apply(lambda s:len(s)==10 and s.notna().all());ids=ok[ok].index;a=a[a.observation_id.isin(ids)].reset_index(drop=True);z=z[z.observation_id.isin(ids)].reset_index(drop=True)
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence(f1.MASTER_SEED).spawn(6)[child]));ordered=f1.ordered_linkage(a,z);w=np.arange(10);rr=[]
    for _ in range(f1.BOOTSTRAPS):
        idx=sample_pooled(a,rng) if pooled else b2.g1.sampled_indices(a,rng);q=ordered.iloc[(idx[:,None]*10+w).ravel()].reset_index(drop=True);b,_=fit_rank(q,"response_4s_m","attacker_path_length_m",pooled=pooled);rr.append(list(f1.regional(b).values()))
    return np.array(rr),len(a)

def tables(a,z,child,pooled=False):
    bp,cp=fit_rank(z,"response_2s_m","attacker_path_length_m",pooled=pooled);bz,_=fit_rank(z,"earlier_relative_path_m","future_attacker_path_length_m",pooled=pooled);b1,_=fit_rank(z,"response_1s_m","attacker_path_length_m",pooled=pooled);bt,_=fit_rank(z,"response_2s_m","attacker_path_length_m",True,pooled)
    ok=z.groupby("observation_id").response_4s_m.apply(lambda s:len(s)==10 and s.notna().all());z4=z[z.observation_id.isin(ok[ok].index)];b4,_=fit_rank(z4,"response_4s_m","attacker_path_length_m",pooled=pooled)
    labels,bm=fit_metric(z,pooled=pooled);boot=bootstrap(a,z,child,pooled);boot4,n4=bootstrap4(a,z,child,pooled);rn=list(f1.regional(bp));
    rank=f1.interval_rows([f"D{i}" for i in range(1,11)],bp,np.empty((0,10)),.95) if False else pd.DataFrame({"estimand":[f"D{i}" for i in range(1,11)],"estimate":bp})
    # Rank bootstrap coefficients are not needed for classification, but frozen reporting requires them: derive in one paired pass below.
    return bp,bz,b1,bt,b4,bm,boot,boot4,n4,labels,cp

def execute(output=OUT,figdir=FIG):
    assert f1.sha256(f1.PROTOCOL)==f1.FROZEN_PROTOCOL_SHA256 and f1.sha256(f1.CONFIG)==f1.FROZEN_CONFIG_SHA256 and f1.sha256(CLAR)==CLAR_HASH and f1.sha256(G1OUT/"final_results.json")==G1_RESULT_HASH and f1.sha256(G1OUT/"final_output_hashes.json")==G1_LEDGER_HASH
    output.mkdir(parents=True,exist_ok=True);figdir.mkdir(parents=True,exist_ok=True)
    a2,z2,e2,counts,prov=prepare2();a1=pd.DataFrame(pl.read_parquet(G1OUT/"eligible_attacker_anchors.parquet").to_dicts());z1=pd.DataFrame(pl.read_parquet(G1OUT/"anchor_defender_linkage.parquet").to_dicts())
    # Close Game 2 quantities first.
    bp2,bz2,b12,bt2,b42,bm2,bo2,bo42,n42,labels,cp2=tables(a2,z2,4,False)
    # Rank bootstrap uses the same child and grouped draws, independently reconstructed.
    f1.CHILD_INDEX=4;rb=f1.bootstrap_all(a2,z2);f1.CHILD_INDEX=3
    rank2=f1.interval_rows([f"D{i}" for i in range(1,11)],bp2,rb["rank_primary"],.95);place_rank2=f1.interval_rows([f"D{i}" for i in range(1,11)],bz2,rb["rank_placebo"],.95);reg2=f1.interval_rows(list(f1.regional(bp2)),np.array(list(f1.regional(bp2).values())),bo2["rp"],.975);place2=f1.interval_rows(list(f1.regional(bz2)),np.array(list(f1.regional(bz2).values())),bo2["rz"],.975);metric2=f1.interval_rows(labels,bm2,bo2["met"],.95);metric2["rows"]=[(z2.distance_band==x).sum() for x in labels];metric2["anchors"]=[z2.loc[z2.distance_band==x,"observation_id"].nunique() for x in labels]
    h2=pd.concat([f1.interval_rows(list(f1.regional(b12)),np.array(list(f1.regional(b12).values())),bo2["r1"],.975).assign(horizon="1s"),reg2.assign(horizon="2s"),f1.interval_rows(list(f1.regional(b42)),np.array(list(f1.regional(b42).values())),bo42,.975).assign(horizon="4s")])
    tr2=f1.interval_rows(list(f1.regional(bt2)),np.array(list(f1.regional(bt2).values())),bo2["rt"],.975)
    pair2=f1.interval_rows(["primary_minus_placebo_Delta_NM","primary_minus_placebo_Delta_MF"],np.array([f1.regional(bp2)["Delta_NM"]-f1.regional(bz2)["Delta_NM"],f1.regional(bp2)["Delta_MF"]-f1.regional(bz2)["Delta_MF"]]),bo2["rp"][:,3:5]-bo2["rz"][:,3:5],.975)
    governed2=json.loads((ROOT/"outputs/attacker_defender_bridge_game2_v1/final_results.json").read_text())["game2_coefficients"]
    loc=b2.g1.fit(a2,*b2.GAME2_SPECS["primary_local_2s"]);far=b2.g1.fit(a2,*b2.GAME2_SPECS["nonlocal_2s"]);dl=float(loc[1]);df=float(far[1]);gl=float(governed2["primary_local_2s"][1]);gf=float(governed2["nonlocal_2s"][1]);md=max(abs(dl-gl),abs(df-gf),abs((dl-df)-(gl-gf)))
    nearfar2={"reconstructed_local_beta":dl,"governed_local_beta":gl,"reconstructed_far_beta":df,"governed_far_beta":gf,"reconstructed_local_minus_far":dl-df,"governed_local_minus_far":gl-gf,"maximum_absolute_difference":md,"tolerance":f1.TOL,"pass":md<=f1.TOL,"classifying":False}
    excluded2=int((a2.attacker_path_length_m>f1.TRIM_THRESHOLD).sum());rob2=[]
    for name in ["Delta_NM","Delta_MF"]:
        full=f1.regional(bp2)[name];trim=f1.regional(bt2)[name];rob2.append({"contrast":name,"threshold_m":f1.TRIM_THRESHOLD,"excluded":excluded2,"excluded_percent":100*excluded2/len(a2),"retained":len(a2)-excluded2,"full":full,"trimmed":trim,"trim_ci_low":float(tr2[tr2.estimand==name].ci_low.iloc[0]),"trim_ci_high":float(tr2[tr2.estimand==name].ci_high.iloc[0]),"sign_retained":np.sign(full)==np.sign(trim),"magnitude_ratio":abs(trim/full) if full else None,"passes":np.sign(full)==np.sign(trim) and abs(trim/full)>=.5})
    # Freeze Game 2 files before pooled construction.
    pl.DataFrame(a2.to_dict(orient="list")).write_parquet(output/"game2_anchors.parquet",compression="zstd");pl.DataFrame(z2.to_dict(orient="list")).write_parquet(output/"game2_linkage.parquet",compression="zstd")
    e2.to_csv(output/"game2_exclusions.csv",index=False,float_format="%.17g");rank2.to_csv(output/"game2_rank_coefficients.csv",index=False,float_format="%.17g");place_rank2.to_csv(output/"game2_placebo_rank.csv",index=False,float_format="%.17g");reg2.to_csv(output/"game2_regional.csv",index=False,float_format="%.17g");place2.to_csv(output/"game2_placebo.csv",index=False,float_format="%.17g");pair2.to_csv(output/"game2_primary_placebo_paired.csv",index=False,float_format="%.17g");metric2.to_csv(output/"game2_metric.csv",index=False,float_format="%.17g");h2.to_csv(output/"game2_horizons.csv",index=False,float_format="%.17g");tr2.to_csv(output/"game2_trimmed.csv",index=False,float_format="%.17g");pd.DataFrame(rob2).to_csv(output/"game2_robustness.csv",index=False,float_format="%.17g");pd.DataFrame([nearfar2]).to_csv(output/"game2_nearfar_consistency.csv",index=False,float_format="%.17g");f1.rank_distance_diagnostics(z2).to_csv(output/"game2_rank_distances.csv",index=False,float_format="%.17g")
    f1.write_json(output/"game2_sample.json",{"eligible_anchors":len(a2),"unique_times":int(a2[["period","time_period_s"]].drop_duplicates().shape[0]),"complete_rows":len(z2),"period_counts":a2.groupby("period").size().to_dict(),"team_counts":a2.groupby("attacking_team").size().to_dict(),"simultaneous":b2.g1.summary(a2.groupby(["period","time_period_s"]).size()),"four_second_eligible":n42,"endpoint_counts":counts,"exclusion_counts":e2.groupby("reason").size().to_dict()})
    f1.make_qc(a2,z2,[rank2,place_rank2,reg2,place2,pair2,metric2,h2,tr2],nearfar2,False).to_csv(output/"game2_hard_qc.csv",index=False)
    game2_files=[p.name for p in sorted(output.glob("game2_*")) if p.name!="game2_closed_hashes.json"];f1.write_json(output/"game2_closed_hashes.json",{x:f1.sha256(output/x) for x in game2_files});game2_files.append("game2_closed_hashes.json")
    # Pooled only after Game 2 closure.
    a1["game"]="G1";a1["game2_indicator"]=0.;z1["game"]="G1";z1["game2_indicator"]=0.;a2["game"]="G2";a2["game2_indicator"]=1.;z2["game"]="G2";z2["game2_indicator"]=1.
    ap=pd.concat([a1,a2],ignore_index=True);zp=pd.concat([z1,z2],ignore_index=True);bpp,bzp,b1p,btp,b4p,bmp,bop,bo4p,n4p,labels,cpp=tables(ap,zp,5,True)
    # pooled rank bootstrap
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence(f1.MASTER_SEED).spawn(6)[5]));ordered=f1.ordered_linkage(ap,zp);w=np.arange(10);rank_samples=[];placebo_rank_samples=[]
    for _ in range(f1.BOOTSTRAPS):
        idx=sample_pooled(ap,rng);q=ordered.iloc[(idx[:,None]*10+w).ravel()].reset_index(drop=True);rank_samples.append(fit_rank(q,"response_2s_m","attacker_path_length_m",pooled=True)[0]);placebo_rank_samples.append(fit_rank(q,"earlier_relative_path_m","future_attacker_path_length_m",pooled=True)[0])
    rankp=f1.interval_rows([f"D{i}" for i in range(1,11)],bpp,np.array(rank_samples),.95);place_rankp=f1.interval_rows([f"D{i}" for i in range(1,11)],bzp,np.array(placebo_rank_samples),.95);regp=f1.interval_rows(list(f1.regional(bpp)),np.array(list(f1.regional(bpp).values())),bop["rp"],.975);placep=f1.interval_rows(list(f1.regional(bzp)),np.array(list(f1.regional(bzp).values())),bop["rz"],.975);metricp=f1.interval_rows(labels,bmp,bop["met"],.95);hp=pd.concat([f1.interval_rows(list(f1.regional(b1p)),np.array(list(f1.regional(b1p).values())),bop["r1"],.975).assign(horizon="1s"),regp.assign(horizon="2s"),f1.interval_rows(list(f1.regional(b4p)),np.array(list(f1.regional(b4p).values())),bo4p,.975).assign(horizon="4s")]);trp=f1.interval_rows(list(f1.regional(btp)),np.array(list(f1.regional(btp).values())),bop["rt"],.975)
    pairp=f1.interval_rows(["primary_minus_placebo_Delta_NM","primary_minus_placebo_Delta_MF"],np.array([f1.regional(bpp)["Delta_NM"]-f1.regional(bzp)["Delta_NM"],f1.regional(bpp)["Delta_MF"]-f1.regional(bzp)["Delta_MF"]]),bop["rp"][:,3:5]-bop["rz"][:,3:5],.975)
    excludedp=int((ap.attacker_path_length_m>f1.TRIM_THRESHOLD).sum());robp=[]
    for name in ["Delta_NM","Delta_MF"]:
        full=f1.regional(bpp)[name];trim=f1.regional(btp)[name];robp.append({"contrast":name,"threshold_m":f1.TRIM_THRESHOLD,"excluded":excludedp,"excluded_percent":100*excludedp/len(ap),"retained":len(ap)-excludedp,"full":full,"trimmed":trim,"trim_ci_low":float(trp[trp.estimand==name].ci_low.iloc[0]),"trim_ci_high":float(trp[trp.estimand==name].ci_high.iloc[0]),"sign_retained":np.sign(full)==np.sign(trim),"magnitude_ratio":abs(trim/full) if full else None,"passes":np.sign(full)==np.sign(trim) and abs(trim/full)>=.5})
    for n,t in [("pooled_rank_coefficients.csv",rankp),("pooled_placebo_rank.csv",place_rankp),("pooled_regional.csv",regp),("pooled_placebo.csv",placep),("pooled_primary_placebo_paired.csv",pairp),("pooled_metric.csv",metricp),("pooled_horizons.csv",hp),("pooled_trimmed.csv",trp),("pooled_robustness.csv",pd.DataFrame(robp))]:t.to_csv(output/n,index=False,float_format="%.17g")
    g1reg=pd.read_csv(G1OUT/"regional_contrasts.csv");qual=[]
    for name in ["Delta_NM","Delta_MF"]:
        def excl(t):r=t[t.estimand==name].iloc[0];return bool(r.ci_low>0 or r.ci_high<0),float(r.estimate)
        x1,s1=excl(g1reg);x2,s2=excl(reg2);xp,sp=excl(regp);trim=float(trp[trp.estimand==name].estimate.iloc[0]);h={r.horizon:float(r.estimate) for _,r in hp[hp.estimand==name].iterrows()};rob=np.sign(trim)==np.sign(sp) and abs(trim/sp)>=.5 and not(np.sign(h["1s"])==-np.sign(sp) and np.sign(h["4s"])==-np.sign(sp));same=np.sign(s1)==np.sign(s2)==np.sign(sp) and np.sign(sp)!=0
        qual.append({"contrast":name,"game1_excludes_zero":x1,"game2_excludes_zero":x2,"pooled_excludes_zero":xp,"same_strict_sign":same,"pooled_robustness":rob,"qualifies_final_A":x1 and x2 and xp and same and rob})
    q=pd.DataFrame(qual);q.to_csv(output/"final_classification_criteria.csv",index=False);status="FINAL FOOTPRINT A" if q.qualifies_final_A.any() else "FINAL FOOTPRINT B"
    f1.make_qc(ap,zp,[rankp,place_rankp,regp,placep,pairp,metricp,hp,trp],nearfar2,False).to_csv(output/"pooled_hard_qc.csv",index=False)
    qc={"frozen_hashes":True,"game2_complete_vectors":bool((z2.groupby("observation_id").size()==10).all()),"all_bootstraps_valid":all(int(t.valid.min())>=f1.MIN_VALID for t in [rank2,place_rank2,reg2,place2,pair2,metric2,h2,tr2,rankp,place_rankp,regp,placep,pairp,metricp,hp,trp]),"game3_accessed":False,"game2_standalone_classification":False}
    f1.write_json(output/"hard_qc.json",qc);f1.write_json(output/"final_results.json",{"classification":status,"criteria":qual,"game2_descriptively_unclassified":True,"game2_sample":len(a2),"pooled_sample":len(ap),"game3_accessed":False})
    manifest={"source":str(Path(__file__).relative_to(ROOT)),"source_sha256":f1.sha256(Path(__file__)),"protocol_sha256":f1.sha256(f1.PROTOCOL),"config_sha256":f1.sha256(f1.CONFIG),"clarification_sha256":f1.sha256(CLAR),"game1_result_sha256":f1.sha256(G1OUT/"final_results.json"),"game2_closed_files":game2_files,"python":platform.python_version()};f1.write_json(output/"manifest.json",manifest)
    governed=[p.name for p in sorted(output.iterdir()) if p.is_file() and p.name not in {"final_hashes.json","governed_hashes.json","reproduction.json"}];f1.write_json(output/"governed_hashes.json",{x:f1.sha256(output/x) for x in governed})
    # governed figures
    fig,ax=plt.subplots(figsize=(9,5));ax.plot(range(1,11),bp2,"o-",label="Game 2");ax.plot(range(1,11),bpp,"o-",label="Pooled");ax.axhline(0,color="black",lw=.8);ax.set(xlabel="Defender proximity rank",ylabel="Association (m/m)",title="Held-out and pooled spatial footprint");ax.legend();fig.tight_layout();fig.savefig(figdir/"rank_footprint.png",dpi=180);plt.close(fig)

def verify(primary,rerun):
    ledger=json.loads((primary/"governed_hashes.json").read_text());comp=[]
    for n in ledger:comp.append({"file":n,"byte_identical":(primary/n).read_bytes()==(rerun/n).read_bytes()})
    passed=all(x["byte_identical"] for x in comp);f1.write_json(primary/"reproduction.json",{"all_byte_identical":passed,"files_compared":len(comp),"comparisons":comp})
    for name in ["game2_hard_qc.csv","pooled_hard_qc.csv"]:
        q=pd.read_csv(primary/name);q.loc[q.check=="deterministic_reproduction","pass"]=passed;q.loc[q.check=="deterministic_reproduction","detail"]=f"{len(comp)} files compared";q.to_csv(primary/name,index=False)
    files=list(ledger)+["governed_hashes.json","reproduction.json","game2_hard_qc.csv","pooled_hard_qc.csv"];f1.write_json(primary/"final_hashes.json",{x:f1.sha256(primary/x) for x in dict.fromkeys(files)})

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--output",type=Path,default=OUT);p.add_argument("--figures",type=Path,default=FIG);p.add_argument("--verify-against",type=Path);a=p.parse_args();execute(a.output,a.figures) if a.verify_against is None else verify(a.output,a.verify_against)
