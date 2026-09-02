"""Deterministic synthetic sampling-frequency audit; no match data are loaded."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.concurrent_defensive_coordination_form_v1 import (
    centered_rolling_mean,
    coordination_form,
    displacement_audit_form,
    zero_phase_butterworth,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "concurrent_defensive_coordination_measurement_audit"
RATES = (10, 25, 100)
ABSOLUTE_TOLERANCE_MPS = 0.005
RELATIVE_TOLERANCE = 0.01


def trajectories(case: str, t: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if case == "constant_aligned":
        a = np.column_stack((1.2 * t, np.zeros_like(t))); r = 0.4 * a
    elif case == "constant_opposite":
        a = np.column_stack((1.2 * t, np.zeros_like(t))); r = -0.3 * a
    elif case == "perpendicular":
        a = np.column_stack((1.2 * t, np.zeros_like(t))); r = np.column_stack((np.zeros_like(t), 0.25 * 1.2 * t))
    elif case == "smooth_speed":
        a = np.column_stack((t + 0.18 * np.sin(0.8 * t), 0.1 * np.sin(0.4 * t)))
        r = np.column_stack((0.35 * t + 0.05 * np.sin(0.8 * t), 0.035 * np.sin(0.4 * t)))
    elif case == "curved_aligned":
        a = np.column_stack((4 * np.sin(0.45 * t), 4 * (1 - np.cos(0.45 * t)))); r = 0.45 * a
    elif case == "stop":
        moving_time = np.where(t < 3, t, np.where(t < 5, 3, t - 2))
        a = np.column_stack((moving_time, np.zeros_like(t)))
        r = 0.3 * a + np.column_stack((np.zeros_like(t), 0.02 * t))
    elif case == "collective_plus_local":
        a = np.column_stack((t, 0.4 * np.sin(0.5 * t))); r = 0.35 * a
    else:
        raise ValueError(case)
    c = np.column_stack((0.6 * t, -0.15 * t)) if case == "collective_plus_local" else np.zeros_like(a)
    focal = c + r
    others = np.repeat(c[:, None, :], 9, axis=1)
    return a, focal, others


def preprocess(values: np.ndarray, time: np.ndarray, method: str, hz: int) -> tuple[np.ndarray, np.ndarray]:
    if method == "raw": return values, time
    if method == "rolling7": return centered_rolling_mean(values, 7), time[3:-3]
    cutoff = 1.0 if method == "butter1" else 1.5
    return zero_phase_butterworth(values, hz, cutoff), time


def execute() -> dict:
    rows = []
    cases = ("constant_aligned", "constant_opposite", "perpendicular", "smooth_speed", "curved_aligned", "stop", "collective_plus_local")
    methods = ("raw", "rolling7", "butter1", "butter1_5")
    for case in cases:
        for hz in RATES:
            t = np.arange(0, 8 + 0.5 / hz, 1 / hz)
            a, d, o = trajectories(case, t)
            disp = displacement_audit_form(a, d, o)
            for method in methods:
                aa, tt = preprocess(a, t, method, hz)
                dd, _ = preprocess(d, t, method, hz)
                oo = np.stack([preprocess(o[:, j], t, method, hz)[0] for j in range(9)], axis=1)
                result = coordination_form(aa, dd, oo, tt)
                rows.append({"case":case,"sample_hz":hz,"method":method,"aard_disp_m":disp.relative_aligned_m,
                    "aard_vel_mps":result.relative_aligned_mps,"cross_vel_mps":result.relative_cross_mps})
    comparisons=[]
    for case in cases:
        for method in methods:
            x=[r for r in rows if r["case"]==case and r["method"]==method]
            a=next(r for r in x if r["sample_hz"]==10); b=next(r for r in x if r["sample_hz"]==25)
            for metric in ("aard_vel_mps","cross_vel_mps"):
                absolute=abs(a[metric]-b[metric]); scale=max(abs(a[metric]),abs(b[metric]),1e-12)
                comparisons.append({"case":case,"method":method,"metric":metric,"absolute_difference":absolute,
                    "relative_difference":absolute/scale,"pass":absolute<=ABSOLUTE_TOLERANCE_MPS or absolute/scale<=RELATIVE_TOLERANCE})
    method_summary={method:{"maximum_absolute_difference_mps":max(x["absolute_difference"] for x in comparisons if x["method"]==method),
        "failed_comparisons":sum(not x["pass"] for x in comparisons if x["method"]==method)} for method in methods}
    result={"synthetic_only":True,"rates_hz":list(RATES),"absolute_tolerance_mps":ABSOLUTE_TOLERANCE_MPS,
        "relative_tolerance":RELATIVE_TOLERANCE,"rows":rows,"comparisons_10_vs_25":comparisons,
        "method_summary":method_summary,
        "physical_time_filters_pass_all":all(x["pass"] for x in comparisons if x["method"] in ("butter1","butter1_5")),
        "historical_rolling7_passes_all":all(x["pass"] for x in comparisons if x["method"]=="rolling7"),"game3_accessed":False,
        "protected_scientific_outcomes_computed":False}
    OUTPUT.mkdir(parents=True,exist_ok=True)
    (OUTPUT/"audit_results.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(execute(),indent=2,sort_keys=True))
