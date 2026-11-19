import numpy as np
import pytest
from src.app.nlp.vad_predictor import VADPredictor, lexicon

def test_fit_model_space_median():
    predictor = VADPredictor()
    pred = np.array([
        [0.2, 0.4, 0.6],
        [0.4, 0.6, 0.8],
        [0.6, 0.8, 1.0],
    ])
    lex_ref = np.array(list(lexicon.values()))

    center, k = predictor.fit_model_space(pred, lex_ref)

    # Median of [0.2, 0.4, 0.6] is 0.4, etc.
    np.testing.assert_allclose(center, [0.4, 0.6, 0.8])
    assert len(k) == 3

def test_fit_centroids():
    predictor = VADPredictor()
    cents_lex = {
        "joy": [1.0, 1.0, 1.0],
        "sadness": [-1.0, -1.0, -1.0]
    }
    center = np.array([0.5, 0.5, 0.5])
    k = np.array([0.2, 0.2, 0.2])

    result = predictor.fit_centroids(cents_lex, center, k)

    # joy = [0.5, 0.5, 0.5] + [1, 1, 1] * 0.2 = [0.7, 0.7, 0.7]
    np.testing.assert_allclose(result["joy"], [0.7, 0.7, 0.7])
    # sadness = [0.5, 0.5, 0.5] + [-1, -1, -1] * 0.2 = [0.3, 0.3, 0.3]
    np.testing.assert_allclose(result["sadness"], [0.3, 0.3, 0.3])

def test_fit_neutral_radius():
    predictor = VADPredictor()
    pred = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [3.0, 0.0, 0.0],
    ])
    center = np.array([0.0, 0.0, 0.0])

    r = predictor.fit_neutral_radius(pred, center, pct=50, axis_w=(1, 1, 0))
    # Norms: 0, 1, 2, 3 -> 50th percentile is 1.5
    assert r == 1.5

def test_process_data_formatting(sample_book_data, monkeypatch):
    predictor = VADPredictor()
    predictor.model_name = "test_vad_model"

    # Mock predict_vad to return deterministic 3D predictions for the 3 sentences
    fake_preds = [
        [0.75, 0.55, 0.45],
        [-0.60, 0.70, 0.10],
        [0.65, -0.80, -0.30]
    ]
    monkeypatch.setattr(predictor, "predict_vad", lambda texts: fake_preds)

    output = predictor.process_data(sample_book_data)

    assert "meta" in output
    assert output["meta"]["model_name"] == "test_vad_model"
    assert output["meta"]["columns"] == ["valence", "arousal", "dominance"]

    config = output["meta"]["config"]
    assert "centroids" in config
    assert "joy" in config["centroids"]
    assert "sadness" in config["centroids"]
    assert "r_neutral" in config
    assert "center" in config

    # Check VAD mapping for sentence IDs 1, 2, 3
    assert "vad" in output
    assert 1 in output["vad"]
    assert 2 in output["vad"]
    assert 3 in output["vad"]
    assert output["vad"][1] == [0.75, 0.55, 0.45]
