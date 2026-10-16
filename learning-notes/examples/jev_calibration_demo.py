"""Run a synthetic calibration exercise; no model, API, or third-party package.

The multiclass Brier score sums over classes (range 0..2), without dividing by
the number of classes. ECE measures top-label calibration. These are distinct
from the binary Brier score for the event "yes" or "the selected answer is right".
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections.abc import Sequence


def softmax(logits: Sequence[float], temperature: float = 1.0) -> list[float]:
    if not logits or not all(math.isfinite(x) for x in logits):
        raise ValueError("logits must be a nonempty finite sequence")
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("temperature must be finite and positive")
    # Subtract before division to avoid overflow for large positive logits.
    maximum = max(logits)
    values = [math.exp((x - maximum) / temperature) for x in logits]
    total = sum(values)
    return [value / total for value in values]


def validate(probabilities: Sequence[Sequence[float]], labels: Sequence[int]) -> None:
    if not probabilities or len(probabilities) != len(labels):
        raise ValueError("a nonempty prediction and one label per row are required")
    for row, label in zip(probabilities, labels):
        if len(row) < 2 or not 0 <= label < len(row):
            raise ValueError("each label must index a distribution with >=2 classes")
        if any(not math.isfinite(p) or not 0 <= p <= 1 for p in row):
            raise ValueError("probabilities must be finite and in [0, 1]")
        if not math.isclose(sum(row), 1.0, abs_tol=1e-9):
            raise ValueError("each probability distribution must sum to one")


def argmax(row: Sequence[float]) -> int:
    return max(range(len(row)), key=row.__getitem__)


def nll(probabilities: Sequence[Sequence[float]], labels: Sequence[int]) -> float:
    validate(probabilities, labels)
    # Clipping is a numerical convention here. A zero true-class probability
    # has infinite mathematical log loss; the demo reports a finite floor.
    return -sum(math.log(max(row[y], 1e-15)) for row, y in zip(probabilities, labels)) / len(labels)


def multiclass_brier(probabilities: Sequence[Sequence[float]], labels: Sequence[int]) -> float:
    validate(probabilities, labels)
    return sum(
        sum((p - int(k == y)) ** 2 for k, p in enumerate(row))
        for row, y in zip(probabilities, labels)
    ) / len(labels)


def ece(probabilities: Sequence[Sequence[float]], labels: Sequence[int], bins: int = 10) -> float:
    validate(probabilities, labels)
    if bins < 1:
        raise ValueError("bins must be positive")
    buckets: list[list[tuple[float, int]]] = [[] for _ in range(bins)]
    for row, y in zip(probabilities, labels):
        prediction = argmax(row)
        confidence = row[prediction]
        # Include confidence=1 in the final bucket, not an out-of-range bucket.
        bucket = min(int(confidence * bins), bins - 1)
        buckets[bucket].append((confidence, int(prediction == y)))
    error = 0.0
    for bucket in buckets:
        if bucket:
            mean_confidence = sum(q for q, _ in bucket) / len(bucket)
            accuracy = sum(c for _, c in bucket) / len(bucket)
            error += len(bucket) / len(labels) * abs(accuracy - mean_confidence)
    return error


def coverage_risk(
    probabilities: Sequence[Sequence[float]], labels: Sequence[int], threshold: float
) -> dict[str, float | int | None]:
    validate(probabilities, labels)
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("threshold must be in [0, 1]")
    accepted = [
        int(argmax(row) != y)
        for row, y in zip(probabilities, labels)
        if max(row) >= threshold
    ]
    return {
        "threshold": threshold,
        "accepted": len(accepted),
        "coverage": len(accepted) / len(labels),
        "risk": sum(accepted) / len(accepted) if accepted else None,
    }


def fit_temperature(logits: list[list[float]], labels: list[int]) -> float:
    """Illustrative grid search on calibration data only, not a production solver."""
    temperatures = [math.exp(math.log(0.25) + i / 200 * math.log(32)) for i in range(201)]
    return min(temperatures, key=lambda t: nll([softmax(row, t) for row in logits], labels))


def synthetic_data(seed: int, count: int) -> tuple[list[list[float]], list[int]]:
    rng = random.Random(seed)
    logits, labels = [], []
    for _ in range(count):
        margin = rng.uniform(-6, 6)
        row = [0.0, margin]
        # Ground truth deliberately follows temperature 3; these aren't model outputs.
        probability_of_one = softmax(row, temperature=3.0)[1]
        logits.append(row)
        labels.append(int(rng.random() < probability_of_one))
    return logits, labels


def report(probabilities: list[list[float]], labels: list[int]) -> dict[str, object]:
    return {
        "accuracy": sum(argmax(row) == y for row, y in zip(probabilities, labels)) / len(labels),
        "nll": nll(probabilities, labels),
        "multiclass_brier_sum_over_classes": multiclass_brier(probabilities, labels),
        "top_label_ece_10_bins": ece(probabilities, labels),
        "gates": [coverage_risk(probabilities, labels, t) for t in (0.5, 0.7, 0.9, 1.0)],
    }


def self_test() -> None:
    perfect = [[1.0, 0.0], [0.0, 1.0]]
    assert multiclass_brier(perfect, [0, 1]) == 0.0
    assert ece(perfect, [0, 1]) == 0.0
    assert nll(perfect, [0, 1]) == 0.0
    assert math.isclose(multiclass_brier([[0.8, 0.2]], [0]), 0.08)
    assert math.isclose(0.08, 2 * (0.2 - 0) ** 2)
    assert math.isclose(multiclass_brier([[1.0, 0.0]], [1]), 2.0)
    assert math.isclose(ece([[0.8, 0.2]] * 4, [0, 0, 0, 1]), 0.05)
    assert coverage_risk([[0.6, 0.4]], [0], 0.9)["risk"] is None
    assert coverage_risk([[0.9, 0.1]], [1], 0.9)["risk"] == 1.0
    assert argmax(softmax([10.0, 9.0, -1.0], 4)) == 0
    assert math.isclose(sum(softmax([1000.0, 1001.0])), 1.0)
    for operation in (
        lambda: softmax([1.0], 0),
        lambda: softmax([math.nan]),
        lambda: nll([[0.2, 0.2]], [0]),
        lambda: ece(perfect, [0]),
        lambda: coverage_risk(perfect, [0, 1], -1),
    ):
        try:
            operation()
        except ValueError:
            pass
        else:
            raise AssertionError("invalid input was accepted")
    print("PASS: calibration formulas, boundary handling, gates and invalid inputs")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if arguments.self_test:
        self_test()
        return
    calibration_logits, calibration_labels = synthetic_data(20261015, 500)
    test_logits, test_labels = synthetic_data(20261016, 1000)
    temperature = fit_temperature(calibration_logits, calibration_labels)
    raw = [softmax(row) for row in test_logits]
    calibrated = [softmax(row, temperature) for row in test_logits]
    assert [argmax(row) for row in raw] == [argmax(row) for row in calibrated]
    print(json.dumps({
        "data": "synthetic only; not a Jev or other model benchmark",
        "calibration_seed": 20261015,
        "test_seed": 20261016,
        "calibration_examples": len(calibration_labels),
        "test_examples": len(test_labels),
        "temperature_fitted_on_calibration_only": temperature,
        "test_raw": report(raw, test_labels),
        "test_calibrated": report(calibrated, test_labels),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
