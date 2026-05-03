"""Minimal sklearn inference script for realtime endpoint."""

import os

import joblib
import numpy as np


def model_fn(model_dir):
    return joblib.load(os.path.join(model_dir, "model.joblib"))


def predict_fn(input_data, model):
    arr = np.asarray(input_data, dtype=float)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    return model.predict(arr)
