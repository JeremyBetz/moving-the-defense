"""Execute frozen Phase 4B focal-departure validation.

`--precheck` performs only outcome-blind checksum, schema, interval, membership,
activity-cutpoint, negative-control-support, and implementation checks. Full mode
constructs the preregistered focal-relative outcomes and writes reproducible outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CFG_PATH = ROOT / "config" / "phase4a_focal_departure_validation_protocol.json"
OUT = ROOT / "outputs" / "phase4b"
FIG = ROOT / "figures" / "phase4b"
L, W = 105.0, 68.0
TOL = 1e-10


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_tracking(path: Path, team: str):
    header = pd.read_csv(path, header=None, nrows=3)
    ids = [str(int(float(v))) for v in header.iloc[1, 3:-2:2] if pd.notna(v)]
    cols = ["Period", "Frame", "Time [s]"]
    for player in ids:
        cols += [f"{team}_{player}_x", f"{team}_{player}_y"]
    cols += [f"{team}_ball_x", f"{team}_ball_y"]
    return pd.read_csv(path, skiprows=3, names=cols), ids


def load_match(game: int):
    data = ROOT / "data" / f"metrica_sample_game_{game}"
    prefix = f"Sample_Game_{game}"
    home, home_ids = load_tracking(data / f"{prefix}_RawTrackingData_Home_Team.csv", "Home")
    away, away_ids = load_tracking(data / f"{prefix}_RawTrackingData_Away_Team.csv", "Away")
    tracking = home.merge(away.drop(columns=["Period", "Time [s]"]), on="Frame", validate="one_to_one")
    events = pd.read_csv(data / f"{prefix}_RawEventsData.csv")
    return {
        "game": game,
        "data": data,
        "tracking": tracking.reset_index(drop=True),
        "events": events,
        "players": {"Home": home_ids, "Away": away_ids},
    }


def other(team: str) -> str:
    return "Away" if team == "Home" else "Home"


def outfield(match, team: str, cfg):
    return [p for p in match["players"][team] if p != cfg["identities"]["goalkeeper_ids"][team]]


def smooth_xy(a: np.ndarray, frames: int) -> np.ndarray:
    return pd.DataFrame(a).rolling(frames, center=True, min_periods=frames).mean().to_numpy()


def path_length(a: np.ndarray) -> float:
    valid = np.isfinite(a).all(axis=1)
    z = a[valid]
    return float(np.linalg.norm(np.diff(z, axis=0), axis=1).sum()) if len(z) > 1 else np.nan


def interval_frames(tracking: pd.DataFrame, period: int, start: float, seconds: float):
    n = int(round(seconds * 25))
    z = tracking[(tracking["Period"] == period) & (tracking["Time [s]"] >= start - 1e-9) &
                 (tracking["Time [s]"] < start + seconds - 1e-9)].copy()
    if len(z) != n:
        return None
    expected = start + np.arange(n) / 25
    if not np.allclose(z["Time [s]"].to_numpy(), expected, atol=1e-7):
        return None
    return z.reset_index(drop=True)


def make_grid(tracking: pd.DataFrame, seconds: float):
    rows = []
    for period in sorted(tracking["Period"].dropna().astype(int).unique()):
        z = tracking[tracking["Period"] == period]
        first = math.ceil((float(z["Time [s]"].min()) - 1e-9) / seconds) * seconds
        last_start = float(z["Time [s]"].max()) - seconds + 1 / 25
        for start in np.arange(first, last_start + 1e-8, seconds):
            rows.append((period, round(float(start), 8)))
    return rows


def build_intervals(match, cfg, seconds=5.0, smoothing=7):
    tracking, events = match["tracking"], match["events"]
    pb = {"PASS", "RECOVERY", "SET PIECE", "SHOT"}
    restart_types = set(cfg["sampling"]["restart_exclusion"]["types"])
    restart_subtypes = set(cfg["sampling"]["restart_exclusion"]["subtypes"])
    poss_events = events[events["Type"].isin(pb) & events["Team"].notna() & events["Start Time [s]"].notna()].copy()
    poss_events = poss_events.sort_values(["Period", "Start Time [s]", "Start Frame"])
    restart_events = events[(events["Type"].isin(restart_types) | events["Subtype"].isin(restart_subtypes)) &
                            events["Start Time [s]"].notna()]
    attrition = {"possession_change": 0, "ball_incomplete": 0, "restart": 0, "no_possession": 0,
                 "frame_or_membership": 0}
    eligible = []
    for interval_id, (period, start) in enumerate(make_grid(tracking, seconds)):
        w = interval_frames(tracking, period, start, seconds)
        if w is None:
            attrition["frame_or_membership"] += 1
            continue
        prior = poss_events[(poss_events["Period"] == period) & (poss_events["Start Time [s]"] <= start + 1e-9)]
        if prior.empty:
            attrition["no_possession"] += 1
            continue
        possession = str(prior.iloc[-1]["Team"])
        during = poss_events[(poss_events["Period"] == period) &
                             (poss_events["Start Time [s]"] >= start - 1e-9) &
                             (poss_events["Start Time [s]"] < start + seconds - 1e-9)]
        if (during["Team"] != possession).any():
            attrition["possession_change"] += 1
            continue
        rest = restart_events[(restart_events["Period"] == period) &
                              (restart_events["Start Time [s]"] >= start - 1e-9) &
                              (restart_events["Start Time [s]"] < start + seconds - 1e-9)]
        if not rest.empty:
            attrition["restart"] += 1
            continue
        ball_cols = ["Home_ball_x", "Home_ball_y"]
        if w[ball_cols].isna().any().any():
            attrition["ball_incomplete"] += 1
            continue
        defending = other(possession)
        complete = []
        for p in outfield(match, defending, cfg):
            cols = [f"{defending}_{p}_x", f"{defending}_{p}_y"]
            if cols[0] in w and w[cols].notna().all().all():
                complete.append(p)
        if len(complete) < cfg["identities"]["minimum_complete_outfield_defenders"]:
            attrition["frame_or_membership"] += 1
            continue
        # Conditioning quantities are outcome-blind and were authorized in Phase 4A.
        positions = {p: np.c_[w[f"{defending}_{p}_x"] * L, w[f"{defending}_{p}_y"] * W] for p in complete}
        smoothed = {p: smooth_xy(a, smoothing) for p, a in positions.items()}
        full_centroid = np.mean(np.stack([positions[p] for p in complete]), axis=0)
        full_centroid_s = smooth_xy(full_centroid, smoothing)
        ball = np.c_[w["Home_ball_x"] * L, w["Home_ball_y"] * W]
        ball_s = smooth_xy(ball, smoothing)
        focal_abs = {p: path_length(smoothed[p]) for p in complete}
        record = {
            "interval_id": f"G{match['game']}_P{period}_{start:.2f}_{seconds:g}s",
            "game": match["game"], "period": period, "start_s": start, "seconds": seconds,
            "possession_team": possession, "defending_team": defending, "players": complete,
            "positions": positions, "smoothed": smoothed,
            "full_centroid": full_centroid, "full_centroid_s": full_centroid_s,
            "ball": ball, "ball_s": ball_s,
            "focal_abs": focal_abs,
            "full_centroid_path_m": path_length(full_centroid_s),
            "sum_defending_paths_m": float(sum(focal_abs.values())),
            "ball_path_m": path_length(ball_s),
        }
        eligible.append(record)
    return make_grid(tracking, seconds), eligible, attrition


def bin3(value, cuts):
    return 0 if value < cuts[0] else (1 if value <= cuts[1] else 2)


def activity_rows(intervals, cfg):
    cuts = cfg["activity_conditioning"]["cuts_m"]
    rows = []
    for r in intervals:
        coll_bin = bin3(r["full_centroid_path_m"], cuts["full_defending_outfield_centroid_path_m"])
        team_bin = bin3(r["sum_defending_paths_m"], cuts["sum_defending_outfield_paths_m"])
        ball_bin = bin3(r["ball_path_m"], cuts["ball_path_m"])
        for p in r["players"]:
            rows.append({
                "interval_id": r["interval_id"], "game": r["game"], "period": r["period"],
                "start_s": r["start_s"], "seconds": r["seconds"], "possession_team": r["possession_team"],
                "defending_team": r["defending_team"], "focal_player": p,
                "focal_absolute_path_m": r["focal_abs"][p],
                "full_defending_outfield_centroid_path_m": r["full_centroid_path_m"],
                "sum_defending_outfield_paths_m": r["sum_defending_paths_m"], "ball_path_m": r["ball_path_m"],
                "focal_bin": bin3(r["focal_abs"][p], cuts["focal_absolute_path_m"]),
                "collective_bin": coll_bin, "team_activity_bin": team_bin, "ball_bin": ball_bin,
            })
    return pd.DataFrame(rows)


def collective_tercile(r, cfg):
    return bin3(r["full_centroid_path_m"], cfg["activity_conditioning"]["cuts_m"]["full_defending_outfield_centroid_path_m"])


def misaligned_pairs(intervals, cfg):
    pairs = {}
    for r in intervals:
        options = [q for q in intervals if q["period"] == r["period"] and q["defending_team"] == r["defending_team"]
                   and collective_tercile(q, cfg) == collective_tercile(r, cfg)
                   and 10 - 1e-9 <= abs(q["start_s"] - r["start_s"]) <= 120 + 1e-9]
        if options:
            q = min(options, key=lambda x: (abs(x["start_s"] - r["start_s"]), x["start_s"]))
            pairs[r["interval_id"]] = q
    return pairs


def precheck(cfg, matches):
    expected = cfg["data"]["sample_game_2_sha256"]
    game2 = matches[2]
    hashes = {p.name: sha256(p) for p in sorted(game2["data"].glob("*.csv"))}
    assert hashes == expected, (hashes, expected)
    assert list(game2["tracking"].shape) == cfg["data"]["sample_game_2_schema"]["tracking_joined_shape"]
    assert list(game2["events"].shape) == cfg["data"]["sample_game_2_schema"]["event_shape"]
    assert game2["players"]["Home"] == cfg["data"]["sample_game_2_schema"]["home_player_ids"]
    assert game2["players"]["Away"] == cfg["data"]["sample_game_2_schema"]["away_player_ids"]
    report = {"checksums": "pass", "schema": "pass", "matches": {}}
    built = {}
    for game, match in matches.items():
        grid, intervals, attrition = build_intervals(match, cfg, 5.0, 7)
        activity = activity_rows(intervals, cfg)
        pairs = misaligned_pairs(intervals, cfg)
        team_counts = pd.Series([r["defending_team"] for r in intervals]).value_counts().to_dict()
        cell_counts = activity.groupby(["focal_bin", "collective_bin"]).size()
        defender_counts = activity.groupby(["defending_team", "focal_player"])["interval_id"].nunique()
        result = {
            "grid_intervals": len(grid), "eligible_intervals": len(intervals),
            "defender_interval_observations": len(activity), "attrition": attrition,
            "eligible_by_defending_team": team_counts, "minimum_3x3_cell": int(cell_counts.min()),
            "defenders_ge_50": int((defender_counts >= 50).sum()),
            "misaligned_support_intervals": len(pairs),
        }
        frozen = cfg["support"]["readiness_counts"][f"Sample Game {game}"]
        assert result["grid_intervals"] == frozen["grid_intervals"], (game, result, frozen)
        assert result["eligible_intervals"] == frozen["eligible_intervals"], (game, result, frozen)
        assert result["defender_interval_observations"] == frozen["defender_interval_observations"]
        expected_attrition = dict(frozen["interval_attrition"])
        expected_attrition.setdefault("no_possession", 0)
        expected_attrition["frame_or_membership"] = 0
        assert result["attrition"] == expected_attrition, (game, result["attrition"], expected_attrition)
        assert result["eligible_by_defending_team"] == frozen["eligible_intervals_by_defending_team"]
        assert result["minimum_3x3_cell"] == frozen["minimum_primary_3x3_cell"]
        assert result["defenders_ge_50"] == frozen["defenders_with_at_least_50_intervals"]
        expected_misaligned = 378 if game == 1 else 366
        assert len(pairs) == expected_misaligned, (game, len(pairs), expected_misaligned)
        report["matches"][str(game)] = result
        built[game] = (intervals, activity, pairs)
    # Recompute only Game-1 conditioning cutpoints; never tune them.
    a1 = built[1][1]
    cuts = cfg["activity_conditioning"]["cuts_m"]
    recomputed = {
        "focal_absolute_path_m": a1["focal_absolute_path_m"].quantile([1/3, 2/3]).tolist(),
        # Interval-level cuts were frozen at the observed tercile values (nearest
        # order statistic); the focal-observation cuts use pandas' linear default.
        "full_defending_outfield_centroid_path_m": pd.Series([r["full_centroid_path_m"] for r in built[1][0]]).quantile([1/3,2/3], interpolation="nearest").tolist(),
        "sum_defending_outfield_paths_m": pd.Series([r["sum_defending_paths_m"] for r in built[1][0]]).quantile([1/3,2/3], interpolation="nearest").tolist(),
        "ball_path_m": pd.Series([r["ball_path_m"] for r in built[1][0]]).quantile([1/3,2/3], interpolation="nearest").tolist(),
    }
    for name, vals in recomputed.items():
        assert np.allclose(vals, cuts[name], atol=1e-10), (name, vals, cuts[name])
    report["game1_cutpoints_reproduced"] = recomputed
    report["implementation"] = {
        "primary": "centered rolling x/y; leave-one-out outfield centroid; accumulated Euclidean path",
        "negative_controls": "common translation plus frozen nearest misaligned interval",
        "sensitivities": "4/5/6 seconds and 5/7/9 frames",
        "replication": "7/9 cells within 0.5 pooled combined-sample cell IQR; direction and sensitivity checks",
        "quantile_resolution": "exact frozen cuts imply linear quantiles for focal observations and nearest observed order statistics for interval-level quantities",
        "ambiguity_resolution": "pooled within-cell IQR = IQR of combined Game-1 and Game-2 outcomes in that cell",
    }
    return report, built


def add_outcomes(intervals, activity, smoothing=7, misaligned=None):
    by_id = {r["interval_id"]: r for r in intervals}
    rows = []
    for rec in activity.to_dict("records"):
        r = by_id[rec["interval_id"]]
        p = rec["focal_player"]
        focal = smooth_xy(r["positions"][p], smoothing)
        others = [q for q in r["players"] if q != p]
        loo = smooth_xy(np.mean(np.stack([r["positions"][q] for q in others]), axis=0), smoothing)
        rel = focal - loo
        valid = np.isfinite(rel).all(axis=1)
        z = rel[valid]
        rec.update({
            "smoothing_frames": smoothing,
            "focal_relative_path_m": path_length(rel),
            "focal_relative_net_x_change_m": float(z[-1, 0] - z[0, 0]),
            "focal_relative_net_y_change_m": float(z[-1, 1] - z[0, 1]),
            "focal_relative_net_displacement_m": float(np.linalg.norm(z[-1] - z[0])),
            "leave_one_out_centroid_path_m": path_length(loo),
        })
        if misaligned is not None and r["interval_id"] in misaligned:
            q = misaligned[r["interval_id"]]
            q_others = [x for x in q["players"] if x != p]
            qloo = smooth_xy(np.mean(np.stack([q["positions"][x] for x in q_others]), axis=0), smoothing)
            rec["misaligned_relative_path_m"] = path_length(focal - qloo)
            rec["misaligned_interval_id"] = q["interval_id"]
        rows.append(rec)
    return pd.DataFrame(rows)


def spearman(x, y):
    a = pd.Series(x).rank(method="average").to_numpy(float)
    b = pd.Series(y).rank(method="average").to_numpy(float)
    return float(np.corrcoef(a, b)[0, 1])


def quantile_summary(df, label):
    q = df["focal_relative_path_m"].quantile([.1, .25, .5, .75, .9])
    return {"label": label, "n": len(df), "p10": q.loc[.1], "p25": q.loc[.25], "median": q.loc[.5],
            "p75": q.loc[.75], "p90": q.loc[.9], "iqr": q.loc[.75]-q.loc[.25]}


def cluster_boot_cell_difference(g1, g2, seed, n=10000):
    rng = np.random.default_rng(seed)
    ids1 = g1["interval_id"].unique(); ids2 = g2["interval_id"].unique()
    groups1 = {k: g1.loc[g1.interval_id == k, "focal_relative_path_m"].to_numpy() for k in ids1}
    groups2 = {k: g2.loc[g2.interval_id == k, "focal_relative_path_m"].to_numpy() for k in ids2}
    vals = np.empty(n)
    for i in range(n):
        a = np.concatenate([groups1[k] for k in rng.choice(ids1, len(ids1), replace=True)])
        b = np.concatenate([groups2[k] for k in rng.choice(ids2, len(ids2), replace=True)])
        vals[i] = np.median(b) - np.median(a)
    return np.quantile(vals, [.025, .975]).tolist()


def analyze_primary(outcomes, cfg):
    g1 = outcomes[outcomes.game == 1].copy(); g2 = outcomes[outcomes.game == 2].copy()
    summaries = pd.DataFrame([quantile_summary(g1, "Game 1"), quantile_summary(g2, "Game 2")])
    activity_vars = cfg["activity_conditioning"]["variables"][:4]
    corr_rows = []
    for game, z in [(1, g1), (2, g2)]:
        for v in activity_vars:
            corr_rows.append({"game": game, "variable": v, "spearman_rho": spearman(z["focal_relative_path_m"], z[v])})
    correlations = pd.DataFrame(corr_rows)
    cells = []
    for fb in range(3):
        for cb in range(3):
            a = g1[(g1.focal_bin == fb) & (g1.collective_bin == cb)]
            b = g2[(g2.focal_bin == fb) & (g2.collective_bin == cb)]
            med1 = a.focal_relative_path_m.median(); med2 = b.focal_relative_path_m.median()
            pooled = pd.concat([a.focal_relative_path_m, b.focal_relative_path_m])
            pooled_iqr = pooled.quantile(.75)-pooled.quantile(.25)
            diff = med2-med1
            ci = cluster_boot_cell_difference(a, b, cfg["random_seed"] + 100*fb + cb)
            cells.append({"focal_bin":fb,"collective_bin":cb,"n_game1":len(a),"n_game2":len(b),
                          "median_game1":med1,"median_game2":med2,"game2_minus_game1":diff,
                          "pooled_iqr":pooled_iqr,"half_pooled_iqr":.5*pooled_iqr,
                          "compatible":abs(diff)<=.5*pooled_iqr,"bootstrap_diff_low":ci[0],"bootstrap_diff_high":ci[1],
                          "iqr_game1":a.focal_relative_path_m.quantile(.75)-a.focal_relative_path_m.quantile(.25),
                          "iqr_game2":b.focal_relative_path_m.quantile(.75)-b.focal_relative_path_m.quantile(.25)})
    cells = pd.DataFrame(cells)
    within = outcomes.groupby(["game","interval_id","defending_team"])["focal_relative_path_m"].quantile([.25,.75]).unstack()
    within["within_interval_iqr"] = within[.75]-within[.25]
    within_summary = within.groupby("game")["within_interval_iqr"].agg(["count","median",lambda x:x.quantile(.25),lambda x:x.quantile(.75)]).reset_index()
    within_summary.columns=["game","n_intervals","median","p25","p75"]
    context = outcomes.groupby(["game","period","possession_team","defending_team"])["focal_relative_path_m"].agg(["count","median",lambda x:x.quantile(.75)-x.quantile(.25)]).reset_index()
    context.columns=["game","period","possession_team","defending_team","n","median","iqr"]
    marginal=[]
    for col in ["team_activity_bin","ball_bin"]:
        z=outcomes.groupby(["game",col])["focal_relative_path_m"].agg(["count","median",lambda x:x.quantile(.75)-x.quantile(.25)]).reset_index()
        z.columns=["game","bin","n","median","iqr"];z["stratum"]=col;marginal.append(z)
    return summaries, correlations, cells, within_summary, context, pd.concat(marginal,ignore_index=True)


def common_translation_check(cfg, observed_translation):
    translation=np.asarray(observed_translation, dtype=float)
    fixed=np.array([[5.,8.],[10.,4.],[2.,3.],[7.,12.],[15.,2.],[3.,14.],[12.,11.],[18.,5.],[1.,9.],[9.,1.]])
    players=np.stack([translation+p for p in fixed])
    vals=[]
    for i in range(len(fixed)):
        focal=smooth_xy(players[i],cfg["smoothing"]["primary_frames"])
        loo=smooth_xy(players[np.arange(len(fixed))!=i].mean(axis=0),cfg["smoothing"]["primary_frames"])
        vals.append(path_length(focal-loo))
    return max(vals)


def defender_summary(outcomes, cfg):
    counts=outcomes.groupby(["game","defending_team","focal_player"])["interval_id"].nunique()
    eligible=counts[counts>=cfg["support"]["criteria"]["within_defender_diagnostic_intervals_min"]].index
    keyed=outcomes.set_index(["game","defending_team","focal_player"])
    z=keyed[keyed.index.isin(eligible)].reset_index()
    out=z.groupby(["game","defending_team","focal_player"])["focal_relative_path_m"].agg(["count","median",lambda x:x.quantile(.75)-x.quantile(.25)]).reset_index()
    out.columns=["game","defending_team","focal_player","n","median","iqr"]
    return out


def sensitivity_analysis(cfg, matches):
    rows=[]
    for seconds in [4.,5.,6.]:
        for smoothing in [5,7,9]:
            all_out=[]
            for game in [1,2]:
                _,ints,_=build_intervals(matches[game],cfg,seconds,smoothing)
                act=activity_rows(ints,cfg)
                all_out.append(add_outcomes(ints,act,smoothing))
            z=pd.concat(all_out,ignore_index=True);g1=z[z.game==1];g2=z[z.game==2]
            rho1=spearman(g1.focal_relative_path_m,g1.focal_absolute_path_m)
            rho2=spearman(g2.focal_relative_path_m,g2.focal_absolute_path_m)
            rows.append({"seconds":seconds,"smoothing_frames":smoothing,"n_intervals_game1":g1.interval_id.nunique(),
                         "n_intervals_game2":g2.interval_id.nunique(),"n_obs_game1":len(g1),"n_obs_game2":len(g2),
                         "median_game1":g1.focal_relative_path_m.median(),"median_game2":g2.focal_relative_path_m.median(),
                         "rho_focal_abs_game1":rho1,"rho_focal_abs_game2":rho2})
    return pd.DataFrame(rows)


def plots(outcomes,cells,correlations,sensitivities):
    FIG.mkdir(parents=True,exist_ok=True)
    fig,axs=plt.subplots(1,2,figsize=(12,4.5))
    for game,color in [(1,"#2563eb"),(2,"#dc2626")]:
        z=outcomes[outcomes.game==game].focal_relative_path_m
        axs[0].hist(z,bins=40,density=True,histtype="step",lw=2,color=color,label=f"Game {game}")
        axs[1].plot(np.linspace(.01,.99,99),z.quantile(np.linspace(.01,.99,99)),lw=2,color=color,label=f"Game {game}")
    axs[0].set(xlabel="7-frame focal-relative path [m]",ylabel="density",title="Frozen five-second distribution")
    axs[1].set(xlabel="quantile",ylabel="focal-relative path [m]",title="Quantile comparison")
    for ax in axs: ax.legend();ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(FIG/"phase4b_distribution_replication.png",dpi=180,bbox_inches="tight");plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(12,4.6))
    bin_colors=["#0f766e","#d97706","#7c3aed"]
    for cb,color in enumerate(bin_colors):
        q=cells[cells.collective_bin==cb]
        for game,marker,style in [(1,"o","-"),(2,"s","--")]:
            axs[0].plot(q.focal_bin,q[f"median_game{game}"],marker=marker,linestyle=style,
                        color=color,label=f"G{game}, collective bin {cb}")
    axs[0].set(xticks=[0,1,2],xlabel="focal absolute-path bin",ylabel="cell median focal-relative path [m]",title="Frozen 3×3 activity cells")
    x=np.arange(4);vars=list(correlations.variable.unique())
    for game,off,color in [(1,-.17,"#2563eb"),(2,.17,"#dc2626")]:
        q=correlations[correlations.game==game].set_index("variable").loc[vars]
        axs[1].bar(x+off,q.spearman_rho,.34,color=color,label=f"Game {game}")
    axs[1].set(xticks=x,xticklabels=["focal","centroid","team sum","ball"],ylabel="Spearman rho",title="Separate activity relationships",ylim=(-1,1))
    for ax in axs:ax.grid(alpha=.2);ax.legend()
    fig.tight_layout();fig.savefig(FIG/"phase4b_activity_context.png",dpi=180,bbox_inches="tight");plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.8))
    for smooth,marker in [(5,"o"),(7,"s"),(9,"^")]:
        z=sensitivities[sensitivities.smoothing_frames==smooth]
        ax.plot(z.seconds,z.median_game2-z.median_game1,marker=marker,label=f"{smooth}-frame")
    ax.axhline(0,color="black",lw=.8);ax.set(xlabel="interval length [s]",ylabel="Game 2 - Game 1 median [m]",title="Frozen window/smoothing sensitivity")
    ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(FIG/"phase4b_sensitivity.png",dpi=180,bbox_inches="tight");plt.close(fig)


def full_run(cfg,matches,pre,built):
    OUT.mkdir(parents=True,exist_ok=True);FIG.mkdir(parents=True,exist_ok=True)
    all_out=[]
    for game in [1,2]:
        intervals,activity,pairs=built[game]
        all_out.append(add_outcomes(intervals,activity,7,pairs))
    outcomes=pd.concat(all_out,ignore_index=True)
    summaries,correlations,cells,within,context,marginal=analyze_primary(outcomes,cfg)
    defenders=defender_summary(outcomes,cfg)
    sensitivities=sensitivity_analysis(cfg,matches)
    # Use one eligible observed defending-centroid trajectory, as frozen, while
    # keeping synthetic fixed relative player positions for the invariance check.
    common_max=common_translation_check(cfg,built[1][0][0]["full_centroid"])
    neg=[]
    for game,z in outcomes.dropna(subset=["misaligned_relative_path_m"]).groupby("game"):
        neg.append({"game":int(game),"n_observations":len(z),"n_intervals":z.interval_id.nunique(),
                    "contemporaneous_median":z.focal_relative_path_m.median(),"misaligned_median":z.misaligned_relative_path_m.median(),
                    "median_paired_difference_misaligned_minus_contemporaneous":(z.misaligned_relative_path_m-z.focal_relative_path_m).median(),
                    "fraction_misaligned_greater":float((z.misaligned_relative_path_m>z.focal_relative_path_m).mean())})
    negative=pd.DataFrame(neg)
    compatible=int(cells.compatible.sum())
    rho_focal=correlations[correlations.variable=="focal_absolute_path_m"].set_index("game").spearman_rho.to_dict()
    almost_determined=all(abs(rho_focal[g])>=.95 for g in [1,2])
    rel_checks=[]
    for v in correlations.variable.unique():
        x=correlations[correlations.variable==v].set_index("game").spearman_rho
        rel_checks.append({"variable":v,"game1_rho":x[1],"game2_rho":x[2],
                           "sign_reversal":bool(np.sign(x[1])!=np.sign(x[2])),
                           "absolute_rho_change":abs(x[2]-x[1])})
    rel_checks=pd.DataFrame(rel_checks)
    primary_sens=sensitivities[(sensitivities.seconds==5)&(sensitivities.smoothing_frames==7)].iloc[0]
    sensitivity_stable=bool(((sensitivities.median_game2-sensitivities.median_game1)*
                             (primary_sens.median_game2-primary_sens.median_game1)>=0).all())
    result={
        "protocol_version":cfg["phase4a_protocol_version"],"seed":cfg["random_seed"],
        "support_pass":True,"compatible_primary_cells":compatible,"required_compatible_cells":7,
        "cell_replication_pass":compatible>=7,
        "activity_relationship_sign_reversal_present":bool(rel_checks.sign_reversal.any()),
        "focal_absolute_rho_game1":rho_focal[1],"focal_absolute_rho_game2":rho_focal[2],
        "almost_completely_determined_falsifier":almost_determined,
        "sensitivity_direction_stable":sensitivity_stable,
        "common_translation_max_path_m":common_max,
        "common_translation_pass":common_max<TOL,
        "negative_control":negative.to_dict("records"),
        "replication_requirements":{
            "support":True,"shapes_reported":True,"seven_of_nine_cells":compatible>=7,
            "effect_size_and_bootstrap_reported":True,"sensitivity_preserved":sensitivity_stable,
        },
    }
    # Frozen interpretation: geometry replication and generic-activity distinction are separate.
    result["geometric_replication"] = bool(all(result["replication_requirements"].values()))
    result["activity_relationship_materiality_requires_scientific_review"] = True
    result["distinguishable_from_generic_activity_requires_scientific_review"] = True
    for name,df in [("focal_outcomes",outcomes),("distribution_summary",summaries),("activity_correlations",correlations),
                    ("activity_cells",cells),("within_interval_iqr",within),("context_summary",context),
                    ("marginal_activity",marginal),("defender_summary",defenders),("negative_control",negative),
                    ("sensitivities",sensitivities),("activity_relationship_checks",rel_checks)]:
        df.to_csv(OUT/f"{name}.csv",index=False)
    (OUT/"precheck.json").write_text(json.dumps(pre,indent=2,default=float)+"\n")
    (OUT/"phase4b_result.json").write_text(json.dumps(result,indent=2,default=float)+"\n")
    plots(outcomes,cells,correlations,sensitivities)
    return result, {"summaries":summaries,"correlations":correlations,"cells":cells,"negative":negative,
                    "sensitivities":sensitivities,"defenders":defenders,"context":context,"marginal":marginal}


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--precheck",action="store_true");args=parser.parse_args()
    cfg=json.loads(CFG_PATH.read_text())
    assert cfg["phase4a_protocol_version"]=="1.0" and cfg["random_seed"]==20260829
    matches={1:load_match(1),2:load_match(2)}
    pre,built=precheck(cfg,matches)
    print(json.dumps(pre,indent=2,default=float))
    if args.precheck:
        print("PRECHECK PASSED: no focal-relative outcomes constructed.")
        return
    result,tables=full_run(cfg,matches,pre,built)
    print("\nPHASE 4B FROZEN RESULT")
    print(json.dumps(result,indent=2,default=float))
    for name in ["summaries","correlations","cells","negative","sensitivities"]:
        print(f"\n{name.upper()}\n",tables[name].to_string(index=False))


if __name__=="__main__":
    main()
