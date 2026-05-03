"""Sklearn realtime inference handlers (Lab 6)."""

from __future__ import annotations

import json
import os

import joblib
import numpy as np


def model_fn(model_dir: str):
    return joblib.load(os.path.join(model_dir, "model.joblib"))


def input_fn(request_body, request_content_type):
    raw = (
        request_body.decode("utf-8")
        if isinstance(request_body, bytes)
        else str(request_body)
    )
    ct = request_content_type or ""
    if "application/json" in ct:
        payload = json.loads(raw)
        arr = np.asarray(payload["features"], dtype=np.float64)
        return np.atleast_2d(arr.flatten())
    if "text/csv" in ct or ct == "":
        values = np.array([float(x) for x in raw.strip().split(",")], dtype=np.float64)
        return np.atleast_2d(values)
    raise ValueError(f"Unsupported content type: {request_content_type}")


def predict_fn(input_data, model):
    pred = int(model.predict(input_data)[0])
    if hasattr(model, "predict_proba") and getattr(model, "classes_", []).size >= 2:
        prob = float(model.predict_proba(input_data)[0][1])
    else:
        prob = float(pred)
    return {"prediction": pred, "probability_positive": prob}


def output_fn(prediction, accept):
    return json.dumps(prediction), accept or "application/json"
