"""Geometry-only mechanics for frozen Local Defensive Deformation v1."""
from __future__ import annotations

import numpy as np


def focal_distance_vectors(xy: np.ndarray) -> np.ndarray:
    """Return [time, focal, other-nine] distance vectors for ten defenders."""
    values=np.asarray(xy,dtype=np.float64)
    if values.ndim!=3 or values.shape[1:]!=(10,2) or not np.isfinite(values).all():
        raise ValueError("Expected finite [time,10,2] defender positions")
    delta=values[:,:,None,:]-values[:,None,:,:]
    distance=np.linalg.norm(delta,axis=3)
    return np.stack([np.delete(distance[:,i,:],i,axis=1) for i in range(10)],axis=1)


def focal_endpoint_rms(xy: np.ndarray) -> np.ndarray:
    distance=focal_distance_vectors(xy); change=distance[-1]-distance[0]
    return np.sqrt(np.mean(change*change,axis=1))


def focal_relational_path(xy: np.ndarray) -> np.ndarray:
    distance=focal_distance_vectors(xy); step=np.diff(distance,axis=0)
    return np.sqrt(np.mean(step*step,axis=2)).sum(axis=0)


def focal_signed_mean_change(xy: np.ndarray) -> np.ndarray:
    distance=focal_distance_vectors(xy)
    return np.mean(distance[-1]-distance[0],axis=1)


def global_endpoint_rms(xy: np.ndarray) -> float:
    values=np.asarray(xy,dtype=np.float64)
    if values.ndim!=3 or values.shape[1:]!=(10,2) or not np.isfinite(values).all():
        raise ValueError("Expected finite [time,10,2] defender positions")
    pairs=np.triu_indices(10,1)
    start=np.linalg.norm(values[0,pairs[0]]-values[0,pairs[1]],axis=1)
    end=np.linalg.norm(values[-1,pairs[0]]-values[-1,pairs[1]],axis=1)
    return float(np.sqrt(np.mean((end-start)**2)))
