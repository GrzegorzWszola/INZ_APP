import math
import pytest
from backend.src.routers.predictions import (
    assign_labels,
    decide_label,
    euclidean_distance,
)

def test_euclidean_distance_known_values():
    assert euclidean_distance((0, 0), (3, 4)) == 5.0
    assert euclidean_distance((1, 1), (1, 1)) == 0.0
    assert math.isclose(euclidean_distance((-1, -1), (2, 3)), 5.0)

def test_assign_labels_empty():
    labels, label_count = assign_labels({}, {"joy": [1.0, 1.0]}, [0.0, 0.0], 0.2)
    assert labels == {}
    assert label_count == {}

def test_assign_labels_neutral_radius():
    centroids = {"joy": [1.0, 1.0], "sadness": [-1.0, -1.0]}
    center = [0.0, 0.0]
    r_neutral = 0.3

    # (0.1, 0.1) distance to center is sqrt(0.02) ~ 0.1414 < 0.3 -> neutral
    values = {"1": [0.1, 0.1]}
    labels, counts = assign_labels(values, centroids, center, r_neutral)

    assert labels["1"] == "neutral"
    assert counts["neutral"] == 1.0

def test_assign_labels_closest_centroid():
    centroids = {
        "joy": [1.0, 1.0],
        "sadness": [-1.0, -1.0],
    }
    center = [0.0, 0.0]
    r_neutral = 0.2

    values = {
        "1": [0.9, 0.9],   # Close to joy
        "2": [-0.8, -0.9], # Close to sadness
        "3": [0.05, 0.05]  # Neutral
    }
    labels, counts = assign_labels(values, centroids, center, r_neutral)

    assert labels["1"] == "joy"
    assert labels["2"] == "sadness"
    assert labels["3"] == "neutral"
    assert math.isclose(counts["joy"], 1 / 3)
    assert math.isclose(counts["sadness"], 1 / 3)
    assert math.isclose(counts["neutral"], 1 / 3)

def test_decide_label_single():
    top, p1, margin = decide_label({"joy": 1.0})
    assert top == "joy"
    assert p1 == 1.0
    assert margin == 1.0

def test_decide_label_multiple_with_margin():
    top, p1, margin = decide_label({"joy": 0.7, "sadness": 0.3})
    assert top == "joy"
    assert p1 == 0.7
    assert margin == 0.4

def test_decide_label_tie():
    top, p1, margin = decide_label({"joy": 0.5, "calm": 0.5})
    assert top in ("joy", "calm")
    assert p1 == 0.5
    assert margin == 0.0
