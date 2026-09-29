"""Authorized five-window presentation recovery; never discovers candidates."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd

from defensive_reorganization_replay import DefenderRelativePathSpec, score_trailing_defender_relative_path
from ball_alignment_reorganization_review import audit_native_trajectory_integrity, compute_ball_alignment_at_time, classify_ballward
from attacker_linked_reorganization_review import AttackerLinkedReviewSpec, LinkReferenceThresholds, classify_episode_links
from run_attacker_linked_reorganization_review import _episode_inputs
from run_metrica_game2_application import load_normalized_team, load_ball, GOALKEEPERS

ROOT = Path(__file__).resolve().parents[1]
AUTHORIZED = frozenset({(2, 5355.64), (1, 336.76), (2, 4443.16), (1, 978.32), (1, 1734.72)})
LINK_CAP = 3
CONTEXT_SECONDS = 5.0


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def assert_identity(row):
    if (int(row.period), float(row.peak_time_s)) not in AUTHORIZED or row.team_key != 'metrica:Home' or row.match_id != 'metrica_sample_game_2':
        raise ValueError('outside the five authorized demo windows')


def bounded_csv(path, period, start, end):
    """Parse only clocks outside the selected slice; retain no other coordinates."""
    output = io.StringIO()
    writer = csv.writer(output)
    with Path(path).open(newline='') as handle:
        reader = csv.reader(handle)
        for _ in range(2):
            writer.writerow(next(reader))
        header = next(reader); writer.writerow(header)
        pi, ti = header.index('Period'), header.index('Time [s]')
        for row in reader:
            if int(row[pi]) == period and start - 1e-7 <= float(row[ti]) <= end + 1e-7:
                writer.writerow(row)
    output.seek(0)
    return output


def assert_close(name, actual, expected):
    if isinstance(expected, str):
        okay = actual == expected
    else:
        okay = np.allclose(actual, expected, atol=1e-8, rtol=1e-9, equal_nan=False)
    if not okay:
        raise RuntimeError(f'closed-result mismatch: {name}: recovered={actual!r}, closed={expected!r}')


def capped_links(links):
    return links.sort_values(['defender_contribution_m', 'attacker_path_m', 'attacker_key', 'defender_key'],
                             ascending=[False, False, True, True], kind='mergesort').head(LINK_CAP).copy()


def recover(row, data_root, ball_manifest):
    assert_identity(row)
    peak, period = float(row.peak_time_s), int(row.period)
    start, end = peak - CONTEXT_SECONDS - 2.12, peak + CONTEXT_SECONDS + .12
    config = json.loads((ROOT / 'config/ball_alignment_reorganization_review_v1.json').read_text())
    assert_close('production scorer hash',sha(ROOT/'src/defensive_reorganization_replay.py'),config['measurement']['production_scorer_sha256'])
    tracking, source_hashes = {}, {}
    for team in ('Home', 'Away'):
        name = f'Sample_Game_2_RawTrackingData_{team}_Team.csv'
        path = Path(data_root) / 'metrica_sample_game_2' / name
        key = f'data/metrica_sample_game_2/{name}'
        actual = sha(path)
        assert_close('source hash', actual, config['source']['tracking_sha256'][key])
        source_hashes[name] = actual
        sliced = bounded_csv(path, period, start, end)
        team_key = f'metrica:{team}'
        q = load_normalized_team(sliced, team_key)
        # Omit absent roster slots, preserving precisely ten complete outfield identities.
        q = q.loc[~q.player_key.eq(GOALKEEPERS[team_key])]
        valid_keys = q.groupby('player_key').coordinate_valid.all()
        q = q.loc[q.player_key.isin(valid_keys[valid_keys].index)].copy()
        if q.player_key.nunique() != 10:
            raise RuntimeError('selected context lacks ten stable outfield players')
        tracking[team_key] = q
        if team == 'Home':
            sliced.seek(0); ball = load_ball(sliced)
    scores = score_trailing_defender_relative_path(tracking[row.team_key], DefenderRelativePathSpec(row.team_key,25.0))
    def level(time):
        values = scores.team_scores.loc[np.isclose(scores.team_scores.time_match_s,time,atol=1e-7,rtol=0),'mean_trailing_relative_path_m']
        if len(values) != 1 or not np.isfinite(values.iloc[0]):
            raise RuntimeError('missing selected score endpoint')
        return float(values.iloc[0])
    assert_close('team_score_m',level(peak),row.team_score_m)
    assert_close('one_second_change_m',level(peak)-level(peak-1),row.one_second_change_m)
    kwargs = dict(match_id=row.match_id, period=period, team_key=row.team_key)
    audit = audit_native_trajectory_integrity(tracking[row.team_key],scores,peak_time_s=peak,**kwargs)
    assert_close('integrity',audit.status,row.trajectory_integrity_status)
    alignment = compute_ball_alignment_at_time(tracking[row.team_key],ball,scores,time_s=peak,**kwargs)
    assert_close('ballward share',alignment.team_ballward_projection_share,row.team_ballward_projection_share)
    assert_close('signed alignment',alignment.team_signed_alignment,row.team_signed_ball_alignment)
    thresholds = ball_manifest['reference_summary']['ballward_share']
    assert_close('stratum',classify_ballward(alignment.team_ballward_projection_share,p25=thresholds['p25'],p75=thresholds['p75']),row.ballward_stratum)
    contributors = sorted(alignment.player_alignment.raw_path_m.tolist(),reverse=True)[:3]
    prior = row.get('top_three_player_raw_paths_m')
    if isinstance(prior,(tuple,list)):
        assert_close('top three contributions',contributors,prior)
    inputs, linkage = None, None
    if audit.clean and row.attacker_link_status == 'supported':
        spec = AttackerLinkedReviewSpec()
        inputs = _episode_inputs(2,row,tracking,ball,{row.team_key:scores},spec)
        gate = json.loads((ROOT / 'figures/presentation/attacker_linked_reorganization_review/reference_thresholds.json').read_text())
        threshold = LinkReferenceThresholds(**{k:gate[k] for k in ('attacker_path_p75_m','relative_vector_path_p75_m','attacker_count','pair_count')})
        linkage = classify_episode_links(inputs['attackers'],inputs['pairs'],threshold,spec=spec)
        assert_close('linkage category',linkage.category,row.linkage_category)
        assert_close('strong links',len(linkage.strong_links),row.strong_link_count)
        assert_close('attacker path',linkage.metadata['maximum_eligible_attacker_path_m'],row.maximum_off_ball_attacker_path_m)
    # Canonical identities stay in memory. Cache labels are episode-local.
    player = scores.player_scores.loc[np.isclose(scores.player_scores.time_match_s,peak,atol=1e-7,rtol=0)].sort_values(['trailing_relative_path_m','player_key'],ascending=[False,True])
    dlabels = {key:f'D{i+1}' for i,key in enumerate(player.player_key)}
    alabels, links = {}, []
    if linkage is not None:
        attackers = linkage.attacker_summary.sort_values(['attacker_path_m','attacker_key'],ascending=[False,True])
        alabels = {key:f'A{i+1}' for i,key in enumerate(attackers.attacker_key)}
        for link in linkage.strong_links.itertuples():
            links.append(dict(attacker=alabels[link.attacker_key],defender=dlabels[link.defender_key],
                              attacker_path_m=float(link.attacker_path_m),defender_contribution_m=float(link.defender_contribution_m)))
    cache = dict(kind='application/demo derivative; not scientific result; not selection input',
                 identity=dict(period=period,time_s=peak,team='Home'),source_sha256=source_hashes,
                 raw_support_s=[start,end],score_window_s=[peak-2,peak],render_window_s=[peak-5,peak+5],
                 top_three_contributions_m=contributors,strong_links=links,visual_link_cap=LINK_CAP,
                 impossible_native_speed_count=audit.impossible_speed_count,integrity_status=audit.status,
                 consistency='PASS',inherited_metadata={key:row[key] for key in ['reference_percentile','possession_state','rapid_context','continuous_out_of_possession_s']},
                 inherited_metadata_policy='Copied exactly from closed package; no reference or possession rescan',
                 dependency_sha256={name:sha(ROOT/'src'/name) for name in ['defensive_reorganization_replay.py','ball_alignment_reorganization_review.py','attacker_linked_reorganization_review.py','selected_window_demo.py']})
    cache['config_sha256'] = {name:sha(ROOT/'config'/name) for name in ['ball_alignment_reorganization_review_v1.json','attacker_linked_off_ball_reorganization_review_v1.json']}
    cache['reference_threshold_sha256'] = sha(ROOT/'figures/presentation/attacker_linked_reorganization_review/reference_thresholds.json')
    return dict(cache=cache,tracking=tracking,ball=ball,scores=scores,inputs=inputs,linkage=linkage,dlabels=dlabels,alabels=alabels)


def render_detail(row, detail, destination):
    """Ten-second contextual replay; frozen link overlays only on [t-2,t]."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    from mplsoccer import Pitch
    destination = Path(destination); destination.mkdir(parents=True,exist_ok=True)
    peak = float(row.peak_time_s)
    stem = f'home_p{int(row.period)}_{peak:.2f}'
    times = peak + np.arange(-125,126)*.04
    # 251 native positions; display every other native frame at 12.5 fps.
    times = times[::2]
    players = detail['scores'].player_scores
    tracks = {}
    for team, frame in detail['tracking'].items():
        for key, q in frame.groupby('player_key'):
            tracks[key] = q.sort_values('time_match_s')
    ball = detail['ball'].sort_values('time_match_s')
    selected = capped_links(detail['linkage'].strong_links) if detail['linkage'] is not None else pd.DataFrame()
    rejected = detail['cache']['integrity_status'] != 'trajectory_integrity_clean'
    jumps = []
    if rejected:
        for key, q in detail['tracking'][row.team_key].groupby('player_key'):
            q = q.loc[q.time_match_s.between(peak-3.12-1e-7,peak+.12+1e-7)].sort_values('time_match_s')
            xy = q[['x_m','y_m']].to_numpy(float)
            for index in np.flatnonzero(np.linalg.norm(np.diff(xy,axis=0),axis=1)*25 > 15):
                jumps.append((xy[index],xy[index+1]))
    def point(q,t):
        result=q.loc[np.isclose(q.time_match_s,t,atol=1e-7,rtol=0)]
        if len(result)!=1 or not result.coordinate_valid.all():
            raise RuntimeError('incomplete visual context')
        return result[['x_m','y_m']].iloc[0].to_numpy(float)+[52.5,34]
    # Fail before export if any display frame is unsupported.
    for t in times:
        for q in [*tracks.values(),ball]: point(q,t)
    fig,ax=plt.subplots(figsize=(10,7))
    pitch=Pitch(pitch_type='custom',pitch_length=105,pitch_width=68,pitch_color='#315d3a',line_color='white')
    norm=plt.Normalize(0,6.25); cmap=plt.get_cmap('YlOrRd')
    from matplotlib.cm import ScalarMappable
    color_ax=fig.add_axes([.25,.17,.5,.018])
    bar=fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),cax=color_ax,orientation='horizontal',extend='max')
    bar.set_label('Defenders: trailing 2 s relative path (m) · attackers blue · ball white',fontsize=8)
    bar.ax.tick_params(labelsize=7)
    title = ('REJECTED — impossible native-frame movement' if rejected else
             'Goalkeeper-distribution diagnostic' if row.linkage_category=='distributed' else
             'High-ballward contrast' if row.ballward_stratum=='high_ballward' else
             'No-link diagnostic' if row.linkage_category=='none' else 'Localized off-ball association')
    def draw(t):
        ax.clear(); pitch.draw(ax=ax)
        current=players.loc[np.isclose(players.time_match_s,t,atol=1e-7,rtol=0)].set_index('player_key')
        for key,q in tracks.items():
            xy=point(q,t); defending=key in detail['dlabels']
            value=float(current.loc[key,'trailing_relative_path_m']) if defending else 0
            color=cmap(norm(value)) if defending and np.isfinite(value) else '#2468b4' if not defending else 'none'
            trail=q.loc[q.time_match_s.between(t-.4-1e-7,t+1e-7)]
            ax.plot(trail.x_m+52.5,trail.y_m+34,color='#b9bfc4' if defending else '#2468b4',lw=1,alpha=.75)
            ax.scatter(*xy,c=[color],edgecolors='#202124' if defending else 'white',s=55,zorder=5)
            if defending and detail['dlabels'][key] in {'D1','D2','D3'}:
                ax.text(xy[0]+.7,xy[1]+.7,detail['dlabels'][key],color='white',fontsize=8,zorder=8)
            if not defending and not selected.empty and key in set(selected.attacker_key):
                ax.text(xy[0]+.7,xy[1]+.7,detail['alabels'][key],color='white',fontsize=8,zorder=8)
        bxy=point(ball,t); trail=ball.loc[ball.time_match_s.between(t-.4-1e-7,t+1e-7)]
        ax.plot(trail.x_m+52.5,trail.y_m+34,color='white',lw=1.5)
        ax.scatter(*bxy,c='white',edgecolors='black',s=45,zorder=9)
        if peak-2-1e-7 <= t <= peak+1e-7:
            for link in selected.itertuples():
                a,d=point(tracks[link.attacker_key],t),point(tracks[link.defender_key],t)
                ax.plot([a[0],d[0]],[a[1],d[1]],color='white',lw=1.4,zorder=3)
        if rejected:
            for a,b in jumps:
                ax.plot([a[0]+52.5,b[0]+52.5],[a[1]+34,b[1]+34],color='#ff4df0',lw=3,ls='--',zorder=10)
            ax.text(52.5,64,'QC ONLY · magenta segments mark impossible native movement',ha='center',color='white',fontsize=9,bbox=dict(facecolor='#850b24',alpha=.95))
        ax.set_title(f'{title}\nHome · P{int(row.period)} · selected {peak:.2f} s · context {t-peak:+.2f} s',fontsize=11)
        return []
    total=len(detail['cache']['strong_links'])
    contributions=' · '.join(f'#{i+1} {v:.2f} m' for i,v in enumerate(detail['cache']['top_three_contributions_m']))
    fig.text(.5,.09,f'Selected rise +{float(row.one_second_change_m):.2f} m · level {float(row.team_score_m):.2f} m · reference {float(row.reference_percentile)*100:.1f}%',ha='center',fontsize=9)
    link_note=f'links shown {min(total,LINK_CAP)}/{total} during [t−2,t]' if detail['linkage'] is not None else 'attacker linkage: not evaluated'
    alignment_note='Integrity failed: no valid downstream interpretation' if rejected else f'Ballward {row.ballward_stratum.upper()}: {float(row.team_ballward_projection_share):.3f}'
    fig.text(.5,.065,f'{alignment_note} · {link_note}',ha='center',fontsize=9)
    fig.text(.5,.04,f'Selected defender contributions: {contributions}',ha='center',fontsize=9)
    fig.text(.5,.015,'Retrospective geometry · extra frames are visual context · no causal, marking or tactical interpretation',ha='center',fontsize=8)
    fig.subplots_adjust(bottom=.26,top=.88)
    draw(peak)
    png=destination/f'{stem}.png'; gif=destination/f'{stem}.gif'
    fig.savefig(png,dpi=110,metadata={'Date':None})
    animation=FuncAnimation(fig,lambda index:draw(float(times[index])),frames=len(times),interval=80,blit=False)
    animation.save(gif,writer=PillowWriter(fps=12.5)); plt.close(fig)
    return png,gif
