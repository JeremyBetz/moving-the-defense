"""External IDSSE execution of frozen Concurrent Defensive Coordination Form v1."""
from __future__ import annotations
import argparse, gc, json, math, platform
from pathlib import Path
import numpy as np
import pandas as pd
import polars as pl

import concurrent_defensive_coordination_form_game1_v1 as g1
import concurrent_attacker_defensive_geometry_idsse_v1 as ext
from concurrent_defensive_coordination_form_v1 import centered_rolling_mean, continuous_valid_blocks, coordination_form, window_has_physical_edge_support, zero_phase_butterworth
import local_defensive_deformation_v1 as deformation

ROOT=Path(__file__).resolve().parents[1]
CLAR=ROOT/'docs/protocols/concurrent_defensive_coordination_form_v1_idsse_replication.md'
LEDGER=ROOT/'config/concurrent_defensive_coordination_form_v1_idsse_replication_hashes.json'
OUT=ROOT/'outputs/concurrent_defensive_coordination_form_idsse_v1'
MATCHES=ext.MATCHES
FROZEN={g1.PROTOCOL:'3172592f0890ea5c8030f4691b24d5a66fc0614d72c4cd60a6f7475934381032',g1.CONFIG:'d3b8be7306ffb850aa246ffed2a2f69b71b5593e32a8578b28734a4a438bb3e3',CLAR:'1d14f5c3e2a6436307aaca2dd7cb9c51f728de04235162cd0da8c309919ba510'}
DT,TOL,EDGE=.04,1e-9,2.0

def verify():
    bad={str(p):[g1.sha(p),h] for p,h in FROZEN.items() if g1.sha(p)!=h}
    if json.loads(LEDGER.read_text())['clarification_sha256']!=FROZEN[CLAR]: bad[str(LEDGER)]=['ledger mismatch']
    if bad: raise RuntimeError(bad)

class Player:
    def __init__(self,team,pid,time,raw,valid):
        self.team,self.pid,self.blocks=team,pid,[]
        frames=np.arange(len(time)); runs=continuous_valid_blocks(frames,time,valid,DT,TOL)
        for s,e in runs:
            xy=raw[s:e+1]
            if len(xy)<=15: continue
            roll=np.full_like(xy,np.nan)
            if len(xy)>=7: roll[3:-3]=centered_rolling_mean(xy,7)
            self.blocks.append((time[s:e+1],{'primary':zero_phase_butterworth(xy,25,1.0),'sensitivity':zero_phase_butterworth(xy,25,1.5),'raw':xy.copy(),'rolling7':roll}))
    def segment(self,start,end,method):
        for time,m in self.blocks:
            if not window_has_physical_edge_support(float(time[0]),float(time[-1]),(start+end)/2,(end-start)/2,(end-start)/2,EDGE,TOL): continue
            i=int(np.searchsorted(time,start-TOL)); j=int(np.searchsorted(time,end-TOL))
            if i<len(time) and j<len(time) and abs(time[i]-start)<=TOL and abs(time[j]-end)<=TOL and j-i==round((end-start)/DT):
                z=m[method][i:j+1]
                return (z,time[i:j+1]) if np.isfinite(z).all() else None
        return None

def build(match,metadata,events,native):
    rows=[]; excluded=[]; teams={metadata['home_team_id'],metadata['away_team_id']}
    for period_number,period in enumerate(ext.idsse.PERIODS,1):
        pdata=native[period]; t=(pdata['time_ns']-pdata['time_ns'][0])/1e9
        entities={(e['team_id'],e['person_id']):e for e in pdata['entities']}
        players={}
        for p in metadata['players'].values():
            key=(p.team_id,p.player_id)
            if p.goalkeeper or key not in entities: continue
            e=entities[key]; raw=np.column_stack([e['x'],e['y']]).astype(float)
            players[key]=Player(*key,t,raw,np.asarray(e['valid'],bool)&np.isfinite(raw).all(axis=1))
        origin=float(t[0]); last=float(t[-1]); k=0
        while origin+2+4*k+2<=last+TOL:
            a=origin+2+4*k; ans=int(pdata['time_ns'][0]+round(a*1e9)); start_ns=ans-2_000_000_000; end_ns=ans+2_000_000_000
            attack,open_ok=ext.context_at_anchor(events,start_ns,ans,end_ns)
            if attack not in teams or not open_ok:
                excluded.append({'match_id':match,'period':period_number,'time_period_s':a,'attacker_key':None,'reason':'possession_or_open_play'}); k+=1; continue
            defend=next(iter(teams-{attack})); defenders=sorted([p for (team,p) in players if team==defend]); attackers=sorted([p for (team,p) in players if team==attack])
            for attacker in attackers:
                ap=players[(attack,attacker)]; asp={m:ap.segment(a-2,a+2,m) for m in ('primary','sensitivity','raw','rolling7')}
                if asp['primary'] is None:
                    excluded.append({'match_id':match,'period':period_number,'time_period_s':a,'attacker_key':attacker,'reason':'attacker_continuous_edge_support'}); continue
                ds=[]
                for d in defenders:
                    dp=players[(defend,d)]; z={m:dp.segment(a-2,a+2,m) for m in ('primary','sensitivity','raw','rolling7')}
                    if all(v is not None for v in z.values()): ds.append((d,z))
                if len(ds)!=10:
                    excluded.append({'match_id':match,'period':period_number,'time_period_s':a,'attacker_key':attacker,'reason':'complete_ten_defender_continuous_edge_support'}); continue
                pm={}
                for method in ('primary','sensitivity','raw','rolling7'):
                    aa,time=asp[method]; stack=np.stack([z[method][0] for _,z in ds],axis=1)
                    if method=='rolling7':
                        mask=np.isfinite(aa).all(1)&np.isfinite(stack).all((1,2)); aa,stack,time=aa[mask],stack[mask],time[mask]
                    c=int(np.flatnonzero(np.abs(time-a)<=TOL)[0]); pm[method]=(aa[:c+1],aa[c:],stack[:c+1],stack[c:],time[:c+1],time[c:])
                if g1.path(pm['primary'][1])<=g1.EPSILON_M or g1.path(pm['sensitivity'][1])<=g1.EPSILON_M:
                    excluded.append({'match_id':match,'period':period_number,'time_period_s':a,'attacker_key':attacker,'reason':'numerical_zero_attacker_path'}); continue
                p=pm['primary']; order=sorted((float(np.linalg.norm(p[3][0,j]-p[1][0])),d,j) for j,(d,_) in enumerate(ds))
                obs=f'CDFI|{match}|P{period_number}|T{a:.2f}|{attacker}'
                for rank,(distance,d,j) in enumerate(order,1):
                    row={'observation_id':obs,'match_id':match,'period':period_number,'time_period_s':a,'attacker_key':attacker,'attacking_team':attack,'is_home_attacking':attack==metadata['home_team_id'],'block_id':int(math.floor(a/60)),'defender_key':d,'distance_rank':rank,'primary_distance_m':distance}
                    for method in ('primary','sensitivity','raw','rolling7'):
                        apre,acon,dpre,dcon,tpre,tcon=pm[method]; pre=g1.measures(apre,dpre,tpre); cf=coordination_form(acon,dcon[:,j],np.delete(dcon,j,axis=1),tcon)
                        row.update({f'{method}_attacker_path_m':g1.path(acon),f'{method}_prior_attacker_path_m':pre['attacker_path'],f'{method}_prior_focal_relative_path_m':pre['relative_path'][j],f'{method}_prior_centroid_path_m':pre['centroid_path'],f'{method}_prior_other_nine_mean_absolute_path_m':float((pre['defender_abs'].sum()-pre['defender_abs'][j])/9),f'{method}_aard_vel_mps':cf.relative_aligned_mps,f'{method}_cross_vel_mps':cf.relative_cross_mps,f'{method}_absolute_aligned_mps':cf.absolute_aligned_mps})
                    row['primary_deformation_m']=deformation.focal_endpoint_rms(p[3])[j]; rows.append(row)
            k+=1
    return pd.DataFrame(rows).sort_values(['period','time_period_s','attacker_key','distance_rank'],kind='mergesort').reset_index(drop=True),pd.DataFrame(excluded)

def design(data,method):
    x=np.zeros((len(data),72)); rank=data.distance_rank.to_numpy(int)-1
    terms=np.column_stack([np.ones(len(data)),data[f'{method}_attacker_path_m'],data[f'{method}_prior_focal_relative_path_m'],data[f'{method}_prior_centroid_path_m'],data[f'{method}_prior_other_nine_mean_absolute_path_m'],data[f'{method}_prior_attacker_path_m'],data.primary_distance_m]).astype(float)
    for i in range(7): x[np.arange(len(data)),rank*7+i]=terms[:,i]
    x[:,70]=(data.period.to_numpy(int)==2); x[:,71]=data.is_home_attacking.to_numpy(float); return x

def bootstrap(data):
    stores={}
    for method in ('primary','sensitivity'):
        x=design(data,method); stores[method]=g1.sufficient(data,x,data[f'{method}_aard_vel_mps'].to_numpy(float))
    keys=sorted(stores['primary']); periods={p:[k for k in keys if k[0]==p] for p in sorted({k[0] for k in keys})}; rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence(g1.SEED).spawn(2)[1])); aa=[];bb=[]
    for _ in range(g1.BOOT):
        chosen=[]
        for blocks in periods.values(): chosen.extend(blocks[int(i)] for i in rng.integers(0,len(blocks),size=len(blocks)))
        try:
            vals=[]
            for method in ('primary','sensitivity'):
                xx=sum((stores[method][k][0] for k in chosen),np.zeros((72,72))); xy=sum((stores[method][k][1] for k in chosen),np.zeros(72)); vals.append(g1.summary(g1.fit_sufficient(xx,xy)))
            aa.append([*vals[0]['D1_D10'],vals[0]['primary_D2_D3_minus_D4_D7'],vals[0]['D1_minus_D4_D7']]); bb.append([*vals[1]['D1_D10'],vals[1]['primary_D2_D3_minus_D4_D7'],vals[1]['D1_minus_D4_D7']])
        except (np.linalg.LinAlgError,RuntimeError): pass
    return np.asarray(aa),np.asarray(bb)

def fit_match(data):
    point={}; support={}
    for method in ('primary','sensitivity'):
        point[method]=g1.summary(g1.fit(design(data,method),data[f'{method}_aard_vel_mps'].to_numpy(float)))
    for method in ('raw','rolling7'):
        x=design(data,method); y=data[f'{method}_aard_vel_mps'].to_numpy(float); m=np.isfinite(x).all(1)&np.isfinite(y); point[method]=g1.summary(g1.fit(x[m],y[m])); support[method]={'rows':int(m.sum()),'excluded':int((~m).sum())}
    secondary={n:g1.summary(g1.fit(design(data,'primary'),data[c].to_numpy(float))) for n,c in [('absolute','primary_absolute_aligned_mps'),('cross','primary_cross_vel_mps'),('deformation','primary_deformation_m')]}
    bp,bs=bootstrap(data); ci=lambda x:[float(v) for v in np.quantile(x,[.025,.975])]; valid=len(bp); est=point['primary']['primary_D2_D3_minus_D4_D7']; sens=point['sensitivity']['primary_D2_D3_minus_D4_D7']
    status='INVALID' if valid<1900 else 'NOT SUPPORTED' if est<=0 else 'SUPPORTED' if ci(bp[:,-2])[0]>0 and sens>0 else 'MIXED'
    anchors=data.drop_duplicates('observation_id')
    return {'status':status,'sample':{'eligible_observations':len(anchors),'unique_anchors':anchors[['period','time_period_s']].drop_duplicates().shape[0],'rows':len(data)},'primary':point['primary'],'primary_ci95':ci(bp[:,-2]),'sensitivity':point['sensitivity'],'sensitivity_ci95':ci(bs[:,-2]),'D1_benchmark_ci95':ci(bp[:,-1]),'paired_valid_bootstraps':valid,'secondary':secondary,'comparators':{'raw':point['raw'],'rolling7':point['rolling7'],'support':support}}

def execute(output):
    verify(); output.mkdir(parents=True,exist_ok=True); results={}; allrows=[]; allex=[]; gates=[]
    for match in MATCHES:
        meta,events,native=ext.load_native(match); eq=ext.tracking_equivalence(match,meta,native); gates.append(eq)
        if not eq['passed']: raise RuntimeError(f'equivalence failed {match}')
        data,ex=build(match,meta,events,native); results[match]=fit_match(data); allrows.append(data); allex.append(ex); gc.collect()
    statuses=[v['status'] for v in results.values()]; nonpos=sum(v['primary']['primary_D2_D3_minus_D4_D7']<=0 for v in results.values())
    overall='IDSSE COORDINATION FORM EXTERNAL REPLICATION INVALID' if 'INVALID' in statuses else 'IDSSE COORDINATION FORM EXTERNAL REPLICATION SUPPORTED' if all(s=='SUPPORTED' for s in statuses) else 'IDSSE COORDINATION FORM EXTERNAL REPLICATION NOT SUPPORTED' if nonpos>=4 else 'IDSSE COORDINATION FORM EXTERNAL REPLICATION MIXED'
    combined=pd.concat(allrows,ignore_index=True); exclusions=pd.concat(allex,ignore_index=True)
    final={'status':overall,'match_results':results,'provider_equivalence':gates,'hard_qc':{'all_provider_equivalence':all(g['passed'] for g in gates),'all_complete_rank_vectors':bool(combined.groupby('observation_id').distance_rank.apply(lambda x:sorted(x)==list(range(1,11))).all()),'all_ten_unique_defenders':bool(combined.groupby('observation_id').defender_key.nunique().eq(10).all()),'all_bootstraps_at_least_1900':all(v['paired_valid_bootstraps']>=1900 for v in results.values()),'no_interpolation':True,'game3_untouched':True,'no_pooled_estimator':True,'scientific_rules_unchanged':True},'frozen_hashes':{str(p.relative_to(ROOT)):h for p,h in FROZEN.items()},'environment':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'polars':pl.__version__}}
    g1.write_json(output/'final_results.json',final); pd.DataFrame(gates).to_csv(output/'provider_equivalence.csv',index=False); exclusions.to_csv(output/'exclusions.csv',index=False); pl.from_pandas(combined).write_parquet(output/'observation_rows.parquet',compression='zstd')
    rows=[]
    for m,v in results.items():
        for method in ('primary','sensitivity'): rows += [{'match_id':m,'method':method,'rank':i+1,'estimate':x} for i,x in enumerate(v[method]['D1_D10'])]
    pd.DataFrame(rows).to_csv(output/'rank_coefficients.csv',index=False)
    g1.write_json(output/'manifest.json',{'starting_commit':'c22a9c2e6a8117dc3528e45207cddba5073ad1ef','source':str(Path(__file__).relative_to(ROOT)),'source_sha256':g1.sha(Path(__file__)),'protected':{'idsse':'authorized_executed','game3':False}})
    governed=['final_results.json','provider_equivalence.csv','exclusions.csv','observation_rows.parquet','rank_coefficients.csv','manifest.json']; g1.write_json(output/'governed_hashes.json',{n:g1.sha(output/n) for n in governed}); return final

def compare(primary,rerun):
    ledger=json.loads((primary/'governed_hashes.json').read_text()); c={n:(primary/n).read_bytes()==(rerun/n).read_bytes() for n in ledger}; return {'files_compared':len(c),'all_governed_outputs_byte_identical':all(c.values()),'comparisons':c}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,default=OUT); p.add_argument('--verify-against',type=Path); a=p.parse_args(); value=compare(a.output,a.verify_against) if a.verify_against else execute(a.output); print(json.dumps(g1.clean(value),indent=2,sort_keys=True))
