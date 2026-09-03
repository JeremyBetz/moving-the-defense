import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import defensive_response_expectation_v1 as m


def fixture():
    rows=[]; rng=np.random.default_rng(4)
    for mi,match in enumerate(m.MATCHES):
        teams=[f'{match}_A',f'{match}_B']
        for period in (1,2):
            for block in range(15):
                for side in teams:
                    for _ in range(5):
                        row={'match_id':match,'period':period,'block_id':block,'defending_team':side,'attacking_team':teams[1-teams.index(side)],'outcome_mps':0.0}
                        for j,c in enumerate(m.CONTINUOUS): row[c]=mi+period+block/10+j/100+rng.normal(scale=.2)
                        rows.append(row)
    d=pd.DataFrame(rows); d['fold']=0
    return d


def test_nested_matrices_are_full_rank_and_grow():
    d=fixture(); train=d.loc[d.block_id.ne(14)].copy(); test=d.loc[d.block_id.eq(14)].copy()
    widths=[]
    for model in ('E0','E1','E2a','E2b'):
        x,z,_=m.matrices(train,test,model); widths.append(x.shape[1]); assert x.shape[1]==z.shape[1]; assert np.linalg.matrix_rank(x)==x.shape[1]
    assert widths==sorted(widths) and len(set(widths))==4


def test_classification_tree_is_exact():
    primary={'absolute_improvement_mps':.01,'relative_improvement_percent':3.1,'matches_improved':6}
    boot={'absolute_improvement_mps':{'ci_low':.001,'ci_high':.02},'valid_replicates':2000}
    assert m.classify(primary,boot,3.0)[0]=='SUPPORTED'
    primary['relative_improvement_percent']=2.0
    assert m.classify(primary,boot,3.0)[0]=='MIXED'
    primary['absolute_improvement_mps']=-.01
    assert m.classify(primary,boot,3.0)[0]=='NOT SUPPORTED'


def test_fold_embargo_removes_adjacent_training_blocks():
    d=fixture(); d=m.assign_folds(d); train,test,log=m.fold_masks(d,2)
    assert train.any() and test.any()
    for tm,tp,tb in set(zip(d.loc[test,'match_id'],d.loc[test,'period'],d.loc[test,'block_id'])):
        assert not any((d.match_id==tm)&(d.period==tp)&(abs(d.block_id-tb)==1)&train)
    assert log['embargoed_training_rows']>0
