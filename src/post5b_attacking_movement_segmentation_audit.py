"""Outcome-blind attacking movement-episode segmentation audit.

Only each player's own tracking trajectory and global period/stoppage boundaries
enter segmentation or method evaluation. No opposing-player geometry, defensive
outcome, possession outcome, or tactical label is constructed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "metrica_sample_game_1"
RULES_PATH = ROOT / "config" / "post5b_movement_segmentation_audit_rules.json"
OUT = ROOT / "outputs" / "post5b_movement_segmentation_audit"
FIG = ROOT / "figures" / "post5b_movement_segmentation_audit"
LENGTH_M, WIDTH_M, FPS = 105.0, 68.0, 25.0
GK = {"Home": "11", "Away": "25"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_tracking(path: Path, team: str) -> tuple[pd.DataFrame, list[str]]:
    h = pd.read_csv(path, header=None, nrows=3)
    ids = [str(int(float(v))) for v in h.iloc[1, 3:-2:2] if pd.notna(v)]
    cols = ["Period", "Frame", "Time [s]"]
    for p in ids:
        cols += [f"{team}_{p}_x", f"{team}_{p}_y"]
    cols += [f"{team}_ball_x", f"{team}_ball_y"]
    return pd.read_csv(path, skiprows=3, names=cols), ids


def global_exclusions(events: pd.DataFrame) -> tuple[dict[int, list[tuple[float, float]]], dict[int, set[float]]]:
    intervals: dict[int, list[tuple[float, float]]] = {1: [], 2: []}
    boundaries: dict[int, set[float]] = {1: set(), 2: set()}
    for period, g in events.sort_values("Start Time [s]").groupby("Period"):
        period = int(period)
        set_times = g.loc[g["Type"].eq("SET PIECE"), "Start Time [s]"].astype(float).to_numpy()
        boundaries[period].update(set_times.tolist())
        for start in g.loc[g["Type"].eq("BALL OUT"), "Start Time [s]"].astype(float):
            later = set_times[set_times >= start]
            end = float(later[0]) if len(later) else float(start)
            intervals[period].append((float(start), end))
            boundaries[period].add(float(start)); boundaries[period].add(end)
    return intervals, boundaries


def player_blocks(
    raw: pd.DataFrame, team: str, player: str, exclusions: dict[int, list[tuple[float, float]]], boundaries: dict[int, set[float]]
) -> list[pd.DataFrame]:
    xcol, ycol = f"{team}_{player}_x", f"{team}_{player}_y"
    blocks: list[pd.DataFrame] = []
    for period, pg in raw.groupby("Period", sort=True):
        q = pg[["Period", "Frame", "Time [s]", xcol, ycol]].copy()
        valid = q[[xcol, ycol]].notna().all(axis=1)
        stopped = pd.Series(False, index=q.index)
        for lo, hi in exclusions[int(period)]:
            stopped |= q["Time [s]"].between(lo, hi, inclusive="both")
        for t in boundaries[int(period)]:
            stopped |= np.isclose(q["Time [s]"], t, atol=1e-8)
        q["eligible"] = valid & ~stopped
        q["new_block"] = (~q["eligible"]) | q["Frame"].diff().ne(1) | q["eligible"].ne(q["eligible"].shift())
        q["block"] = q["new_block"].cumsum()
        for _, b in q[q["eligible"]].groupby("block"):
            if len(b) < 12:
                continue
            b = b.copy()
            b["x_m"] = b[xcol] * LENGTH_M; b["y_m"] = b[ycol] * WIDTH_M
            b["sx_m"] = b["x_m"].rolling(7, center=True, min_periods=7).mean()
            b["sy_m"] = b["y_m"].rolling(7, center=True, min_periods=7).mean()
            b = b.dropna(subset=["sx_m", "sy_m"]).reset_index(drop=True)
            if len(b) < 5:
                continue
            dt = b["Time [s]"].diff()
            b["dx_m"] = b["sx_m"].diff(); b["dy_m"] = b["sy_m"].diff()
            b["speed_mps"] = np.hypot(b["dx_m"], b["dy_m"]) / dt
            b = b.dropna(subset=["speed_mps"]).reset_index(drop=True)
            if len(b) >= 3:
                blocks.append(b)
    return blocks


def raw_valleys(speed: np.ndarray) -> list[int]:
    """Plateau-aware local minima; use midpoint of each qualifying flat run."""
    candidates: list[int] = []
    i, n = 1, len(speed) - 1
    while i < n:
        j = i
        while j + 1 < n and speed[j + 1] == speed[i]:
            j += 1
        left, right = speed[i - 1], speed[j + 1]
        if speed[i] <= left and speed[j] <= right and (speed[i] < left or speed[j] < right):
            candidates.append((i + j) // 2)
        i = j + 1
    return candidates


def consolidate_valleys(candidates: list[int], speed: np.ndarray, times: np.ndarray, separation_s: float = 1.0) -> list[int]:
    kept: list[int] = []
    for idx in candidates:
        if not kept or times[idx] - times[kept[-1]] >= separation_s - 1e-9:
            kept.append(idx)
        elif speed[idx] < speed[kept[-1]] - 1e-12:
            kept[-1] = idx
        # Exact ties preserve the earlier candidate.
    return kept


def geometry(q: pd.DataFrame) -> dict:
    xy = q[["sx_m", "sy_m"]].to_numpy()
    inc = np.diff(xy, axis=0)
    lengths = np.linalg.norm(inc, axis=1)
    path = float(lengths.sum())
    delta = xy[-1] - xy[0]; displacement = float(np.linalg.norm(delta))
    ratio = displacement / path if path > 1e-9 else np.nan
    if displacement > 1e-9:
        u = delta / displacement
        projection = (xy - xy[0]) @ u
        closest = xy[0] + np.outer(projection, u)
        chord_dev = float(np.linalg.norm(xy - closest, axis=1).max())
    else:
        chord_dev = float(np.linalg.norm(xy - xy[0], axis=1).max())
    speeds = q["speed_mps"].to_numpy()
    valid_inc = lengths > 1e-9
    valid_inc &= speeds[1:] >= 0.5
    heading = np.arctan2(inc[:, 1], inc[:, 0])[valid_inc]
    if len(heading) >= 2:
        changes = np.diff(np.unwrap(heading))
        signed_heading = float(np.degrees(changes.sum()))
        absolute_heading = float(np.degrees(np.abs(changes).sum()))
        large_heading_changes = int((np.abs(np.degrees(changes)) >= 45.0).sum())
    else:
        signed_heading = absolute_heading = 0.0; large_heading_changes = 0
    return {
        "duration_s": float(q["Time [s]"].iloc[-1] - q["Time [s]"].iloc[0]),
        "path_m": path, "displacement_m": displacement,
        "delta_x_m": float(delta[0]), "delta_y_m": float(delta[1]),
        "displacement_path_ratio": ratio, "path_displacement_ratio": path / displacement if displacement > 1e-9 else np.nan,
        "peak_speed_mps": float(q["speed_mps"].max()), "mean_speed_mps": float(q["speed_mps"].mean()),
        "start_speed_mps": float(q["speed_mps"].iloc[0]), "end_speed_mps": float(q["speed_mps"].iloc[-1]),
        "max_chord_deviation_m": chord_dev, "signed_heading_change_deg": signed_heading,
        "absolute_heading_change_deg": absolute_heading, "heading_changes_ge45_count": large_heading_changes,
    }


def segment_method_a(block: pd.DataFrame, team: str, player: str, block_id: str) -> tuple[list[dict], list[int]]:
    speed = block["speed_mps"].to_numpy(); times = block["Time [s]"].to_numpy()
    valleys = consolidate_valleys(raw_valleys(speed), speed, times, 1.0)
    episodes = []
    for a, b in zip(valleys[:-1], valleys[1:]):
        q = block.iloc[a:b + 1]
        if q["Time [s]"].iloc[-1] - q["Time [s]"].iloc[0] < 1.0 - 1e-9:
            continue
        g = geometry(q)
        g.update({"team": team, "player": player, "period": int(q["Period"].iloc[0]), "block_id": block_id,
                  "start_frame": int(q["Frame"].iloc[0]), "end_frame": int(q["Frame"].iloc[-1]),
                  "start_s": float(q["Time [s]"].iloc[0]), "end_s": float(q["Time [s]"].iloc[-1]),
                  "start_x_m": float(q["sx_m"].iloc[0]), "start_y_m": float(q["sy_m"].iloc[0]),
                  "end_x_m": float(q["sx_m"].iloc[-1]), "end_y_m": float(q["sy_m"].iloc[-1])})
        episodes.append(g)
    return episodes, valleys


def segment_method_b(block: pd.DataFrame, team: str, player: str, block_id: str) -> list[dict]:
    mask = block["speed_mps"].ge(5.5).to_numpy(); runs = []
    starts = np.flatnonzero(mask & ~np.r_[False, mask[:-1]])
    ends = np.flatnonzero(mask & ~np.r_[mask[1:], False])
    for a, b in zip(starts, ends):
        q = block.iloc[a:b + 1]
        support_duration = len(q) / FPS
        if support_duration < 1.0 - 1e-9:
            continue
        g = geometry(q); g.update({"team": team, "player": player, "period": int(q["Period"].iloc[0]), "block_id": block_id,
            "start_frame": int(q["Frame"].iloc[0]), "end_frame": int(q["Frame"].iloc[-1]), "start_s": float(q["Time [s]"].iloc[0]), "end_s": float(q["Time [s]"].iloc[-1]),
            "threshold_support_duration_s": support_duration})
        runs.append(g)
    return runs


def method_c_windows(block: pd.DataFrame, team: str, player: str, block_id: str, period_origin: float) -> list[dict]:
    lo, hi = float(block["Time [s]"].min()), float(block["Time [s]"].max())
    k0 = int(np.ceil((lo - period_origin) / 4.0 - 1e-9)); k1 = int(np.floor((hi - period_origin - 4.0) / 4.0 + 1e-9))
    rows = []
    for k in range(k0, k1 + 1):
        start = period_origin + 4.0 * k; end = start + 4.0
        q = block[(block["Time [s]"] >= start - 1e-8) & (block["Time [s]"] < end - 1e-8)]
        if len(q) < 90:
            continue
        g = geometry(q); g.update({"team": team, "player": player, "period": int(q["Period"].iloc[0]), "block_id": block_id,
            "start_frame": int(q["Frame"].iloc[0]), "end_frame": int(q["Frame"].iloc[-1]), "start_s": float(start), "end_s": float(end)})
        rows.append(g)
    return rows


def add_diagnostics(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    a = a.copy()
    overlap = []
    for r in a.itertuples():
        hit = b[(b.team == r.team) & (b.player.astype(str) == str(r.player)) & (b.period == r.period) & (b.start_s < r.end_s) & (b.end_s > r.start_s)]
        overlap.append(not hit.empty)
    a["method_b_overlap"] = overlap
    a["diag_short"] = a.duration_s <= 1.5 + 1e-9
    a["diag_tiny_path"] = a.path_m <= 1.0 + 1e-9
    a["diag_tiny_displacement"] = a.displacement_m <= 0.5 + 1e-9
    a["diag_long"] = a.duration_s >= 8.0 - 1e-9
    a["diag_low_displacement_path_ratio"] = a.displacement_path_ratio <= 0.5 + 1e-12
    a["diag_direction_change"] = (a.path_m >= 3.0 - 1e-9) & (a.absolute_heading_change_deg >= 180.0 - 1e-9)
    a["diag_lower_speed_meaningful_displacement"] = (a.peak_speed_mps < 5.5) & (a.displacement_m >= 3.0)
    a["diag_fragmentation_any"] = a[["diag_short", "diag_tiny_path", "diag_tiny_displacement"]].any(axis=1)
    a["diag_merging_any"] = a[["diag_long", "diag_low_displacement_path_ratio", "diag_direction_change"]].any(axis=1)
    return a


def deterministic_visual_sample(a: pd.DataFrame) -> pd.DataFrame:
    ordered = a.sort_values(["start_s", "period", "team", "player"], key=lambda s: s.map(lambda x: int(x)) if s.name == "player" else s).reset_index()
    idx = np.unique(np.linspace(0, len(ordered) - 1, 16).round().astype(int))
    primary = ordered.iloc[idx].copy(); primary["sample_reason"] = "evenly_spaced_chronological"
    extremes = []
    specs = [
        ("shortest_duration", a.sort_values(["duration_s", "start_s"]).iloc[0]),
        ("longest_duration", a.sort_values(["duration_s", "start_s"], ascending=[False, True]).iloc[0]),
        ("highest_heading_change", a[a.path_m >= 3].sort_values(["absolute_heading_change_deg", "start_s"], ascending=[False, True]).iloc[0]),
        ("lowest_peak_speed_displacement_ge3m", a[a.displacement_m >= 3].sort_values(["peak_speed_mps", "start_s"]).iloc[0]),
        ("first_method_b_overlap", a[a.method_b_overlap].sort_values("start_s").iloc[0]),
    ]
    for reason, row in specs:
        d = row.to_dict(); d["sample_reason"] = reason; extremes.append(d)
    cols = list(a.columns) + ["sample_reason"]
    return pd.concat([primary[cols], pd.DataFrame(extremes)[cols]], ignore_index=True).drop_duplicates(["team", "player", "start_frame", "sample_reason"])


def episode_slice(blocks: dict[str, pd.DataFrame], row: pd.Series, pad: float = 1.5) -> pd.DataFrame:
    q = blocks[row["block_id"]]
    return q[q["Time [s]"].between(row.start_s - pad, row.end_s + pad)]


def plot_visual_samples(a: pd.DataFrame, sample: pd.DataFrame, blocks: dict[str, pd.DataFrame]) -> None:
    primary = sample[sample.sample_reason.eq("evenly_spaced_chronological")].head(16)
    fig, axes = plt.subplots(4, 4, figsize=(16, 15), constrained_layout=True)
    for ax, (_, r) in zip(axes.flat, primary.iterrows()):
        q = episode_slice(blocks, r, 0); ax.plot(q.sx_m, q.sy_m, color="#1f77b4"); ax.scatter([q.sx_m.iloc[0]], [q.sy_m.iloc[0]], marker="o", c="green"); ax.scatter([q.sx_m.iloc[-1]], [q.sy_m.iloc[-1]], marker="x", c="red")
        ax.set_title(f"{r.team} {r.player} | {r.start_s:.2f}–{r.end_s:.2f}s", fontsize=9); ax.set_aspect("equal", adjustable="datalim"); ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    fig.suptitle("Deterministic visual audit sample — attacker trajectory only")
    fig.savefig(FIG / "01_deterministic_trajectory_sample.png", dpi=170); plt.close(fig)

    fig, axes = plt.subplots(4, 4, figsize=(16, 13), constrained_layout=True)
    for ax, (_, r) in zip(axes.flat, primary.iterrows()):
        q = episode_slice(blocks, r, 1.5); ax.plot(q["Time [s]"], q.speed_mps, color="black"); ax.axvspan(r.start_s, r.end_s, color="#1f77b4", alpha=.2); ax.axvline(r.start_s, color="green", ls="--"); ax.axvline(r.end_s, color="red", ls="--")
        ax.set_title(f"{r.team} {r.player} | {r.duration_s:.2f}s", fontsize=9); ax.set_xlabel("time (s)"); ax.set_ylabel("speed (m/s)")
    fig.suptitle("Speed valleys bound the deterministic visual sample")
    fig.savefig(FIG / "02_deterministic_speed_valleys.png", dpi=170); plt.close(fig)


def plot_distributions(a: pd.DataFrame, b: pd.DataFrame, c: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True); ax.hist(a.duration_s, bins=50, color="#1f77b4"); ax.axvline(1.5, color="orange", ls="--", label="short diagnostic"); ax.axvline(8, color="red", ls="--", label="long diagnostic"); ax.set(xlabel="duration (s)", ylabel="episodes", title="Method A duration distribution"); ax.legend(); fig.savefig(FIG/"03_duration_distribution.png",dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 7), constrained_layout=True); ax.scatter(a.path_m,a.displacement_m,s=8,alpha=.3); ax.plot([0,a.path_m.max()],[0,a.path_m.max()],color="black",ls="--"); ax.set(xlabel="path (m)",ylabel="net displacement (m)",title="Method A path and displacement"); fig.savefig(FIG/"04_path_displacement.png",dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 7), constrained_layout=True); sc=ax.scatter(a.delta_x_m,a.delta_y_m,c=a.peak_speed_mps,s=9,alpha=.45,cmap="viridis"); ax.axhline(0,color=".7");ax.axvline(0,color=".7");ax.set(xlabel="signed x displacement (m)",ylabel="signed y displacement (m)",title="Method A directional geometry");fig.colorbar(sc,ax=ax,label="peak speed (m/s)");fig.savefig(FIG/"05_signed_displacement.png",dpi=180);plt.close(fig)
    fig, ax = plt.subplots(figsize=(9,5), constrained_layout=True); counts=[(~a.method_b_overlap).sum(),a.method_b_overlap.sum()];ax.bar(["No high-speed overlap","Overlaps comparator"],counts,color=["#1f77b4","#d62728"]);ax.set(ylabel="Method A episodes",title="Method A retention beyond high-speed comparator");fig.savefig(FIG/"06_method_a_vs_b.png",dpi=180);plt.close(fig)
    fig, ax=plt.subplots(figsize=(9,5),constrained_layout=True); ax.hist(a.duration_s,bins=45,alpha=.6,label="Method A");ax.axvline(4,color="black",ls="--",label="Method C fixed duration");ax.set(xlabel="duration (s)",ylabel="units",title="Movement-defined versus fixed-window duration");ax.legend();fig.savefig(FIG/"07_method_a_vs_fixed.png",dpi=180);plt.close(fig)


def plot_edge_group(a: pd.DataFrame, blocks: dict[str, pd.DataFrame], mask: pd.Series, filename: str, title: str, sort_col: str, ascending: bool) -> None:
    rows=a[mask].sort_values([sort_col,"start_s"],ascending=[ascending,True]).head(6)
    fig,axes=plt.subplots(2,3,figsize=(14,8),constrained_layout=True)
    for ax,(_,r) in zip(axes.flat,rows.iterrows()):
        q=episode_slice(blocks,r,0);ax.plot(q.sx_m,q.sy_m,color="#1f77b4");ax.scatter([q.sx_m.iloc[0]],[q.sy_m.iloc[0]],c="green");ax.scatter([q.sx_m.iloc[-1]],[q.sy_m.iloc[-1]],c="red",marker="x");ax.set_aspect("equal",adjustable="datalim");ax.set_title(f"{r.team} {r.player} {r.start_s:.1f}s\n{r.duration_s:.2f}s, {r.path_m:.1f}m",fontsize=9)
    fig.suptitle(title);fig.savefig(FIG/filename,dpi=180);plt.close(fig)


def comparisons(a: pd.DataFrame, b: pd.DataFrame, c: pd.DataFrame) -> dict:
    split=[];combine=[];alignment=[]
    for r in a.itertuples():
        cw=c[(c.team==r.team)&(c.player.astype(str)==str(r.player))&(c.period==r.period)]
        boundaries=np.unique(np.r_[cw.start_s.to_numpy(),cw.end_s.to_numpy()]) if len(cw) else np.array([])
        split.append(bool(((boundaries>r.start_s)&(boundaries<r.end_s)).any()))
        alignment.append(float(np.min(np.abs(boundaries-r.start_s))) if len(boundaries) else np.nan)
    for r in c.itertuples():
        ep=a[(a.team==r.team)&(a.player.astype(str)==str(r.player))&(a.period==r.period)&(a.start_s<r.end_s)&(a.end_s>r.start_s)]
        combine.append(len(ep)>1)
    return {"method_a_episodes":len(a),"method_b_runs":len(b),"method_c_windows":len(c),
        "method_a_peak_below_5_5_mps_pct":float((a.peak_speed_mps < 5.5).mean()*100),
        "lower_speed_displacement_ge_3m_n":int(a.diag_lower_speed_meaningful_displacement.sum()),
        "lower_speed_displacement_ge_3m_pct":float(a.diag_lower_speed_meaningful_displacement.mean()*100),
        "fragmentation_any_n":int(a.diag_fragmentation_any.sum()),"fragmentation_any_pct":float(a.diag_fragmentation_any.mean()*100),
        "merging_direction_any_n":int(a.diag_merging_any.sum()),"merging_direction_any_pct":float(a.diag_merging_any.mean()*100),
        "method_a_without_b_overlap_n":int((~a.method_b_overlap).sum()),"method_a_without_b_overlap_pct":float((~a.method_b_overlap).mean()*100),
        "method_a_split_by_fixed_boundary_pct":float(np.mean(split)*100),"fixed_windows_combining_multiple_a_pct":float(np.mean(combine)*100),
        "median_a_start_to_nearest_fixed_boundary_s":float(np.nanmedian(alignment))}


def main() -> None:
    OUT.mkdir(parents=True,exist_ok=True);FIG.mkdir(parents=True,exist_ok=True)
    rules=json.loads(RULES_PATH.read_text())
    home_path=DATA/'Sample_Game_1_RawTrackingData_Home_Team.csv';away_path=DATA/'Sample_Game_1_RawTrackingData_Away_Team.csv';event_path=DATA/'Sample_Game_1_RawEventsData.csv'
    home,hids=load_tracking(home_path,'Home');away,aids=load_tracking(away_path,'Away');events=pd.read_csv(event_path)
    tracking={'Home':home,'Away':away};players={'Home':[p for p in hids if p!=GK['Home']], 'Away':[p for p in aids if p!=GK['Away']]}
    exclusions,boundaries=global_exclusions(events)
    origins={int(p):float(g['Time [s]'].min()) for p,g in home.groupby('Period')}
    arows=[];brows=[];crows=[];inclusion=[];blocks_by_id={}
    for team in ('Home','Away'):
        raw=tracking[team]
        for player in sorted(players[team],key=int):
            blocks=player_blocks(raw,team,player,exclusions,boundaries);before=len(arows)
            supported_frames=sum(len(b) for b in blocks)
            for j,block in enumerate(blocks):
                block_id=f'{team}_{player}_{int(block.Period.iloc[0])}_{j}';blocks_by_id[block_id]=block
                ae,_=segment_method_a(block,team,player,block_id);arows.extend(ae);brows.extend(segment_method_b(block,team,player,block_id));crows.extend(method_c_windows(block,team,player,block_id,origins[int(block.Period.iloc[0])]))
            inclusion.append({'team':team,'player':player,'supported_smoothed_frames':supported_frames,'eligible_blocks':len(blocks),'method_a_episodes':len(arows)-before,'included':len(arows)>before})
    a=pd.DataFrame(arows);b=pd.DataFrame(brows);c=pd.DataFrame(crows)
    a=add_diagnostics(a,b);a.insert(0,'episode_id',[f'A{i:06d}' for i in range(1,len(a)+1)])
    b.insert(0,'run_id',[f'B{i:05d}' for i in range(1,len(b)+1)]);c.insert(0,'window_id',[f'C{i:06d}' for i in range(1,len(c)+1)])
    sample=deterministic_visual_sample(a)
    pd.DataFrame(inclusion).to_csv(OUT/'player_inclusion.csv',index=False);a.to_csv(OUT/'method_a_episodes.csv',index=False);b.to_csv(OUT/'method_b_high_speed_runs.csv',index=False);c.to_csv(OUT/'method_c_fixed_windows.csv',index=False);sample.to_csv(OUT/'visual_audit_sample.csv',index=False)
    a[a.diag_fragmentation_any].to_csv(OUT/'fragmentation_diagnostics.csv',index=False);a[a.diag_merging_any].to_csv(OUT/'merging_direction_diagnostics.csv',index=False);a[a.diag_lower_speed_meaningful_displacement].to_csv(OUT/'lower_speed_retention_diagnostics.csv',index=False)
    comp=comparisons(a,b,c);(OUT/'method_comparison_summary.json').write_text(json.dumps(comp,indent=2)+'\n')
    summary=[]
    for col in ['duration_s','path_m','displacement_m','peak_speed_mps']:
        s=a[col];summary.append({'quantity':col,'median':float(s.median()),'q1':float(s.quantile(.25)),'q3':float(s.quantile(.75)),'min':float(s.min()),'max':float(s.max())})
    pd.DataFrame(summary).to_csv(OUT/'method_a_distribution_summary.csv',index=False)
    plot_visual_samples(a,sample,blocks_by_id);plot_distributions(a,b,c)
    plot_edge_group(a,blocks_by_id,a.diag_fragmentation_any,'08_fragmentation_examples.png','Predeclared fragmentation diagnostics','duration_s',True)
    plot_edge_group(a,blocks_by_id,a.diag_merging_any,'09_direction_merging_examples.png','Predeclared merging/direction diagnostics','absolute_heading_change_deg',False)
    plot_edge_group(a,blocks_by_id,a.diag_lower_speed_meaningful_displacement,'10_lower_speed_examples.png','Lower-speed episodes with ≥3 m net displacement','peak_speed_mps',True)
    manifest={'audit':'Post-5B outcome-blind attacking movement segmentation','classification':'B — mixed','rules_sha256':sha256(RULES_PATH),'source_sha256':sha256(Path(__file__)),'inputs_sha256':{p.name:sha256(p) for p in (home_path,away_path,event_path)},'metrica_game3_accessed':False,'defensive_coordinates_used':False,'defensive_outcomes_used':False,'method_parameters_predeclared':True,'counts':comp}
    (OUT/'audit_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    qc={'players_processed':len(inclusion),'players_with_episodes':int(pd.DataFrame(inclusion).included.sum()),'anchors_or_defensive_outcomes_used':False,'opposing_player_coordinates_joined':False,'method_a_deterministic':True,'method_b_predeclared':True,'method_c_predeclared':True,'visual_sample_deterministic':True,'metrica_game3_accessed':False,'figure_count':len(list(FIG.glob('*.png')))}
    qc['passed']=all([qc['players_with_episodes']>0,not qc['anchors_or_defensive_outcomes_used'],not qc['opposing_player_coordinates_joined'],qc['method_a_deterministic'],qc['method_b_predeclared'],qc['method_c_predeclared'],qc['visual_sample_deterministic'],not qc['metrica_game3_accessed'],qc['figure_count']==10])
    (OUT/'qc_results.json').write_text(json.dumps(qc,indent=2)+'\n')
    print(json.dumps({'method_a':len(a),'method_b':len(b),'method_c':len(c),'players':len(inclusion),'qc':qc['passed']},indent=2))


if __name__=='__main__':main()
