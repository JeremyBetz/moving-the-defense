from pathlib import Path
import sys
import pandas as pd
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from selected_window_demo import AUTHORIZED, LINK_CAP, assert_identity, assert_close, capped_links, bounded_csv


def test_exact_authorization_and_fail_closed():
    assert AUTHORIZED == {(2,5355.64),(1,336.76),(2,4443.16),(1,978.32),(1,1734.72)}
    for period,time in AUTHORIZED:
        assert_identity(pd.Series(dict(period=period,peak_time_s=time,team_key='metrica:Home',match_id='metrica_sample_game_2')))
    with pytest.raises(ValueError):
        assert_identity(pd.Series(dict(period=1,peak_time_s=100,team_key='metrica:Home',match_id='metrica_sample_game_2')))
    with pytest.raises(RuntimeError,match='closed-result mismatch'):
        assert_close('score',1,2)


def test_link_cap_preserves_all_links_and_is_deterministic():
    links=pd.DataFrame([dict(defender_contribution_m=i%3,attacker_path_m=i,attacker_key=f'a{i}',defender_key=f'd{i%3}') for i in range(12)])
    before=links.copy(deep=True)
    a=capped_links(links); b=capped_links(links.sample(frac=1,random_state=4))
    assert LINK_CAP==3 and len(a)==3 and len(links)==12
    assert a.attacker_key.tolist()==['a11','a8','a5']
    pd.testing.assert_frame_equal(a,b)
    pd.testing.assert_frame_equal(links,before)


def test_clock_only_filter_does_not_normalize_outside_coordinates(tmp_path):
    source=tmp_path/'fixture.csv'
    source.write_text('header\nheader\nPeriod,Time [s],Player1,y\n1,0,INVALID,INVALID\n1,1,0.5,0.5\n2,1,INVALID,INVALID\n')
    q=pd.read_csv(bounded_csv(source,1,1,1),skiprows=2)
    assert len(q)==1 and q.Player1.iloc[0]==.5


def test_demo_never_calls_candidate_ranking(tmp_path, monkeypatch):
    import match_reorganization_review as facade
    import run_match_reorganization_demo as demo
    def forbidden(*args, **kwargs):
        raise AssertionError('candidate ranking forbidden')
    monkeypatch.setattr(facade, '_rank', forbidden)
    monkeypatch.setattr(facade, 'analyze_match_reorganization', forbidden)
    monkeypatch.setattr(demo, '_records', forbidden)
    demo.run_demo(tmp_path/'out',data_root=tmp_path/'absent')
    q=pd.read_csv(tmp_path/'out'/'detailed_episode_table.csv')
    assert set(zip(q.period,q.peak_time_s))==AUTHORIZED


@pytest.mark.provider_data
def test_five_window_recovery_matches_closed_authority(monkeypatch):
    import selected_window_demo as bounded
    import run_match_reorganization_demo as demo
    import run_attacker_linked_reorganization_review as runner
    root=Path(__file__).resolve().parents[1]
    if not (root/'data/metrica_sample_game_2').is_dir():
        pytest.skip('public Game 2 tracking unavailable')
    def forbidden(*a,**k):
        raise AssertionError('full-population operation forbidden')
    for name in ('_load_population','_game_review'):
        if hasattr(runner,name):
            monkeypatch.setattr(runner,name,forbidden)
    ball=demo._load_manifest(demo.BALL_MANIFEST)
    review=demo.frozen_demo_review(ball,demo._load_manifest(demo.ATTACKER_MANIFEST))
    for _,row in review.rapid_episodes.iterrows():
        detail=bounded.recover(row,root/'data',ball)
        cache=detail['cache']
        assert cache['consistency']=='PASS'
        assert len(cache['top_three_contributions_m'])==3
        assert cache['score_window_s']==[row.peak_time_s-2,row.peak_time_s]
        assert cache['render_window_s']==[row.peak_time_s-5,row.peak_time_s+5]
        if row.peak_time_s==4443.16:
            assert len(detail['linkage'].strong_links)==12
            assert len(bounded.capped_links(detail['linkage'].strong_links))==3
        if row.peak_time_s==1734.72:
            assert detail['linkage'] is None
            assert cache['integrity_status']!='trajectory_integrity_clean'
            assert cache['impossible_native_speed_count']>0
        import json
        serialized=json.dumps(cache)
        assert all(key not in serialized for key in ('player_key','attacker_key','defender_key','x_m','y_m','frame_id'))
