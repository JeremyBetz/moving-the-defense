"""Generate documentation figures from Metrica Sample Game 1 and frozen results.

No Sample Game 2 focal-relative quantity is loaded or calculated.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "metrica_sample_game_1"
OUT = ROOT / "figures"
L, W = 105.0, 68.0


def load_tracking(path, team):
    header = pd.read_csv(path, header=None, nrows=3)
    ids = [str(int(float(v))) for v in header.iloc[1, 3:-2:2] if pd.notna(v)]
    columns = ["Period", "Frame", "Time [s]"]
    for player in ids:
        columns += [f"{team}_{player}_x", f"{team}_{player}_y"]
    columns += [f"{team}_ball_x", f"{team}_ball_y"]
    return pd.read_csv(path, skiprows=3, names=columns), ids


home, home_ids = load_tracking(DATA / "Sample_Game_1_RawTrackingData_Home_Team.csv", "Home")
away, away_ids = load_tracking(DATA / "Sample_Game_1_RawTrackingData_Away_Team.csv", "Away")
tracking = home.merge(away.drop(columns=["Period", "Time [s]"]), on="Frame", validate="one_to_one")
players = {"Home": home_ids, "Away": away_ids}
goalkeeper = {"Home": "11", "Away": "25"}


def window(period, start, end):
    return tracking[(tracking.Period == period) & tracking["Time [s]"].between(start, end)].copy()


def pos(frame, team, player):
    return np.c_[frame[f"{team}_{player}_x"] * L, frame[f"{team}_{player}_y"] * W]


def outfield(team):
    return [p for p in players[team] if p != goalkeeper[team]]


def loo_centroid(frame, team, focal):
    arrays = [pos(frame, team, p) for p in outfield(team) if p != focal and pos(frame, team, p).shape[0]]
    valid = [a for a in arrays if np.isfinite(a).all()]
    return np.mean(np.stack(valid), axis=0)


def pitch(ax, title=None):
    ax.add_patch(Rectangle((0, 0), L, W, fill=False, lw=1.2, color="#374151"))
    ax.axvline(L / 2, color="#9ca3af", lw=.8)
    ax.set(xlim=(0, L), ylim=(0, W), aspect="equal", xlabel="pitch length [m]", ylabel="pitch width [m]")
    if title:
        ax.set_title(title)


def save(fig, rel):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# A — raw motion versus collective-relative motion.
w = window(1, 1888, 1896)
focal = pos(w, "Home", "4")
centroid = loo_centroid(w, "Home", "4")
relative = focal - centroid
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
pitch(axes[0], "Raw pitch motion: coordinated passage")
axes[0].plot(focal[:, 0], focal[:, 1], color="#dc2626", lw=2, label="Home4 focal")
axes[0].plot(centroid[:, 0], centroid[:, 1], color="#2563eb", lw=2, label="leave-one-out centroid")
axes[0].scatter(*focal[0], color="#dc2626", marker="o"); axes[0].scatter(*focal[-1], color="#dc2626", marker="x")
axes[0].legend()
axes[1].plot(relative[:, 0], relative[:, 1], color="#7c3aed", lw=2)
axes[1].scatter(*relative[0], color="#7c3aed", marker="o", label="start")
axes[1].scatter(*relative[-1], color="#7c3aed", marker="x", label="end")
axes[1].set(title="Same focal trajectory relative to collective motion", xlabel="relative x [m]", ylabel="relative y [m]", aspect="equal")
axes[1].grid(alpha=.25); axes[1].legend()
fig.suptitle("Illustrative Game 1 geometry — large raw translation can shrink in a collective-relative frame")
fig.tight_layout(); save(fig, "concepts/raw_vs_collective_relative.png")


# B — scale comparison.
cases = [
    ("Coordinated translation", 1888, 1896, "Home", "4"),
    ("Focal departure", 590, 598, "Home", "2"),
    ("Centroid-stable local change", 1228.12, 1232.12, "Away", "19"),
]
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
for j, (name, start, end, team, focal_id) in enumerate(cases):
    q = window(1, start, end); f = pos(q, team, focal_id); c = loo_centroid(q, team, focal_id); r = f - c
    pitch(axes[0, j], name)
    for p in outfield(team):
        a = pos(q, team, p)
        if np.isfinite(a).all(): axes[0, j].plot(a[:, 0], a[:, 1], color="#9ca3af", lw=.7, alpha=.65)
    axes[0, j].plot(c[:, 0], c[:, 1], color="#2563eb", lw=2, label="LOO centroid")
    axes[0, j].plot(f[:, 0], f[:, 1], color="#dc2626", lw=2.4, label=f"{team}{focal_id}")
    axes[0, j].legend(fontsize=8)
    axes[1, j].plot(r[:, 0], r[:, 1], color="#7c3aed", lw=2)
    axes[1, j].scatter(*r[0], marker="o", color="#7c3aed"); axes[1, j].scatter(*r[-1], marker="x", color="#7c3aed")
    axes[1, j].set(xlabel="relative x [m]", ylabel="relative y [m]", aspect="equal", title="Focal minus leave-one-out centroid")
    axes[1, j].grid(alpha=.25)
fig.suptitle("Illustrative Game 1 contrasts — geometric scales, not validation labels")
fig.tight_layout(); save(fig, "concepts/collective_translation_vs_focal_departure.png")


# C — stable centroid versus local reorganization.
q = window(1, 1228.12, 1232.12); trio = ["19", "20", "21"]
fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
indices = [0, len(q)//2, len(q)-1]
for ax, idx, label in zip(axes, indices, ["before", "during", "after"]):
    pitch(ax, label)
    for team, color in [("Home", "#111827"), ("Away", "#9ca3af")]:
        for p in outfield(team):
            a = pos(q.iloc[[idx]], team, p)
            if np.isfinite(a).all(): ax.scatter(a[0, 0], a[0, 1], s=22, color=color, alpha=.8)
    pts = np.array([pos(q.iloc[[idx]], "Away", p)[0] for p in trio])
    ax.fill(pts[:, 0], pts[:, 1], color="#f59e0b", alpha=.25, label="illustrated 19/20/21 set")
    ax.plot(np.r_[pts[:, 0], pts[0, 0]], np.r_[pts[:, 1], pts[0, 1]], color="#d97706", lw=2)
    all_away = np.array([pos(q.iloc[[idx]], "Away", p)[0] for p in outfield("Away") if np.isfinite(pos(q.iloc[[idx]], "Away", p)).all()])
    cen = all_away.mean(axis=0); ax.scatter(*cen, marker="P", s=90, color="#2563eb", label="defensive centroid")
    ball = np.array([q.iloc[idx].Home_ball_x * L, q.iloc[idx].Home_ball_y * W]); ax.scatter(*ball, marker="*", s=100, color="#ef4444", label="ball")
    if idx == 0: ax.legend(fontsize=7, loc="lower left")
fig.suptitle("Illustrative Game 1 counterexample — small centroid movement can coexist with local relational change")
fig.tight_layout(); save(fig, "concepts/centroid_stability_local_reorganization.png")


# D — local membership/reference sensitivity.
sets = {"visual trio\n19/20/21": ["19", "20", "21"], "start-nearest trio\n19/22/17": ["19", "22", "17"], "anchor trio\n19/22/23": ["19", "22", "23"]}
fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
for ax, (label, members) in zip(axes, sets.items()):
    pitch(ax, label)
    for p in outfield("Away"):
        a = pos(q, "Away", p)
        if np.isfinite(a).all(): ax.plot(a[:, 0], a[:, 1], color="#d1d5db", lw=.7)
    for p, color in zip(members, ["#dc2626", "#2563eb", "#059669"]):
        a = pos(q, "Away", p); ax.plot(a[:, 0], a[:, 1], lw=2.2, color=color, label=f"Away{p}")
    ax.legend(fontsize=8)
fig.suptitle("Illustrative reference sensitivity — reasonable fixed local memberships produce different deformation stories")
fig.tight_layout(); save(fig, "concepts/local_membership_sensitivity.png")


# E — closure versus residual engagement schematic.
fig, ax = plt.subplots(figsize=(9, 5.5)); pitch(ax, "Conceptual vector decomposition — schematic, not an empirical event")
d0=np.array([45.,30.]); a0=np.array([60.,36.]); vd=np.array([4.,1.]); va=np.array([-1.,0.]); vc=np.array([2.5,.5]); residual=vd-vc
ax.scatter(*d0,s=90,color="#2563eb",label="defender start"); ax.scatter(*a0,s=90,color="#dc2626",label="attacker start")
for origin,vec,color,label in [(d0,vd,"#2563eb","defender absolute movement"),(a0,va,"#dc2626","attacker movement"),(d0,vc,"#059669","collective movement"),(d0+vc,residual,"#7c3aed","defender residual")]:
    ax.add_patch(FancyArrowPatch(origin,origin+vec*2.2,arrowstyle="->",mutation_scale=14,lw=2,color=color,label=label))
ax.plot([d0[0],a0[0]],[d0[1],a0[1]],ls="--",color="#6b7280",label="pairwise distance")
ax.legend(loc="lower right",fontsize=8)
fig.tight_layout(); save(fig, "concepts/closure_vs_engagement_vectors.png")


# F — Phase 3 failure, using frozen reported median paired differences.
labels=["collective path","focal-relative path","nearest-opponent distance","generic activity"]
primary=np.array([3.92,5.01,2.81,33.96]); shifted=np.array([5.33,6.54,1.75,59.19])
fig, ax=plt.subplots(figsize=(10,5)); x=np.arange(len(labels)); width=.36
ax.bar(x-width/2,primary,width,label="reception vs matched ordinary",color="#2563eb")
ax.bar(x+width/2,shifted,width,label="reception vs shifted same-possession anchor",color="#f59e0b")
ax.axhline(0,color="#111827",lw=.8); ax.set_xticks(x,labels); ax.set_ylabel("median paired difference [m]")
ax.set_title("Phase 3B: apparent movement differences were not relationally specific")
ax.legend(); ax.text(.01,-.23,"Frozen result C; primary support 46/315 (14.6%). Bars are separate descriptors, not a combined score.",transform=ax.transAxes,fontsize=9)
fig.tight_layout(); save(fig, "phase3/phase3_validation_failure.png")


# G — Phase 4 design schematic.
fig, ax=plt.subplots(figsize=(11,5.5)); ax.axis("off")
boxes=[(.05,.55,.25,.25,"Game 1\ndevelopment/history\nfreeze activity strata"),(.38,.55,.25,.25,"Frozen Phase 4A\nfocal-departure protocol\nno event-positive labels"),(.71,.55,.25,.25,"Game 2\nuntouched held-out test\nexecute once")]
for x,y,wid,hei,text in boxes:
    ax.add_patch(Rectangle((x,y),wid,hei,fc="#eff6ff",ec="#2563eb",lw=1.5)); ax.text(x+wid/2,y+hei/2,text,ha="center",va="center",fontsize=10)
for x1,x2 in [(.30,.38),(.63,.71)]: ax.add_patch(FancyArrowPatch((x1,.675),(x2,.675),arrowstyle="->",mutation_scale=16,lw=1.8))
ax.text(.5,.35,r"$\mathbf{r}_d(t)=\mathbf{x}_d(t)-\mathbf{c}_{-d}(t)$",ha="center",fontsize=17)
ax.text(.5,.20,"Test: reproducible focal-relative structure beyond focal, collective, team, and ball activity",ha="center",fontsize=11)
ax.text(.5,.08,"Not tested here: tactical meaning, opponent attribution, reconfiguration, gravity, or value",ha="center",fontsize=9,color="#7f1d1d")
ax.set_title("Phase 4 design — development/test separation before focal outcomes",fontsize=14)
fig.tight_layout(); save(fig, "phase4/phase4_heldout_design.png")


# H — research evolution.
fig, ax=plt.subplots(figsize=(12,4.8)); ax.axis("off")
stages=[("Historical\ndiscrete states",.06),("Continuous typed\nrelationships",.27),("Multi-scale\ngeometry",.48),("Umbrella validation\nfailed",.69),("Narrow primitive\nvalidation",.90)]
for i,(text,x) in enumerate(stages):
    ax.add_patch(Rectangle((x-.085,.47),.17,.22,fc="#fff7ed" if i==3 else "#eff6ff",ec="#dc2626" if i==3 else "#2563eb",lw=1.4))
    ax.text(x,.58,text,ha="center",va="center",fontsize=10)
    if i<len(stages)-1: ax.add_patch(FancyArrowPatch((x+.09,.58),(stages[i+1][1]-.09,.58),arrowstyle="->",mutation_scale=15,lw=1.5))
ax.text(.5,.28,"Scientific narrowing: failures constrain the next claim; they do not guarantee progress toward gravity.",ha="center",fontsize=11)
ax.text(.5,.13,"Current position: frozen held-out validation design for focal departure",ha="center",fontsize=11,fontweight="bold")
ax.set_title("Research evolution",fontsize=14)
fig.tight_layout(); save(fig, "concepts/research_evolution.png")

print("Generated 8 documentation figures under figures/.")
