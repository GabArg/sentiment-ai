from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.evaluation import load_benchmark
from src.hybrid import evaluate_hybrid_benchmark, evaluate_hybrid_text
from src.review_router import ReviewRouterConfig
from src.hybrid_config import HybridRoutingConfig
from src.review_router import route_prediction
from src.sentiment_review import ReviewResult


@dataclass
class MockProvider:
    result: ReviewResult
    received_text: str | None = None

    def review_sentiment(self, text: str) -> ReviewResult:
        self.received_text = text
        return self.result


def result(sentiment: str | None, *, success: bool, error_code: str | None = None):
    return ReviewResult(sentiment, 0.9 if success else None, None, "mock", "mock-v1", success, error_code)


def test_no_key_equivalent_falls_back_to_local(predictor):
    hybrid = evaluate_hybrid_text(
        "El pedido llegó el martes por la tarde.", predictor, provider=None
    )
    assert hybrid.review_requested
    assert hybrid.provider_status == "unavailable"
    assert hybrid.state == "fallback_local"
    assert hybrid.hybrid_prediction == hybrid.local_prediction
    assert hybrid.second_check_prediction is None


def test_provider_failure_falls_back_without_claiming_review(predictor):
    provider = MockProvider(result(None, success=False, error_code="timeout"))
    hybrid = evaluate_hybrid_text("El pedido llegó el martes.", predictor, provider=provider)
    assert hybrid.provider_status == "timeout"
    assert hybrid.state == "fallback_local"
    assert hybrid.hybrid_prediction == hybrid.local_prediction


def test_provider_can_return_same_class(predictor):
    text = "El pedido llegó el martes por la tarde."
    local = predictor.predict_one(text).label
    provider = MockProvider(result(local, success=True))
    hybrid = evaluate_hybrid_text(text, predictor, provider=provider)
    assert hybrid.state == "reviewed"
    assert hybrid.hybrid_prediction == local


def test_provider_can_contradict_local_class(predictor):
    provider = MockProvider(result("Neutro", success=True))
    hybrid = evaluate_hybrid_text("El pedido llegó el martes.", predictor, provider=provider)
    assert hybrid.second_check_prediction == "Neutro"
    assert hybrid.hybrid_prediction == "Neutro"
    assert hybrid.state == "disagreement"


def test_no_review_keeps_local_and_does_not_call_provider(predictor):
    provider = MockProvider(result("Neutro", success=True))
    hybrid = evaluate_hybrid_text(
        "Excelente atención, volvería a comprar.",
        predictor,
        config=ReviewRouterConfig(confidence_threshold=None, margin_threshold=None),
        provider=provider,
    )
    assert hybrid.state == "local_only"
    assert provider.received_text is None


def test_mock_neutral_can_improve_known_factual_case(predictor):
    provider = MockProvider(result("Neutro", success=True))
    hybrid = evaluate_hybrid_text("El pedido llegó el martes por la tarde.", predictor, provider=provider)
    assert hybrid.hybrid_prediction == "Neutro"


def test_hybrid_benchmark_records_local_fallback_without_key(predictor):
    comparison = evaluate_hybrid_benchmark(load_benchmark(), predictor, provider=None)
    assert len(comparison) == 60
    assert comparison["review_requested"].sum() == 50
    assert (comparison["hybrid_prediction"] == comparison["local_prediction"]).all()
    assert (comparison["hybrid_correct"] == comparison["local_correct"]).all()
    assert set(comparison.loc[comparison.review_requested, "provider_status"]) == {"unavailable"}
    assert {
        "expected",
        "local_prediction",
        "local_confidence",
        "local_margin",
        "review_reasons",
        "second_check_prediction",
        "hybrid_prediction",
        "local_correct",
        "hybrid_correct",
        "provider_status",
    }.issubset(comparison.columns)


def test_controlled_thresholds_reproduce_exploratory_router_benchmark(predictor):
    benchmark = load_benchmark()
    config = HybridRoutingConfig().router_config()
    reviewed = captured = errors = 0
    for row in benchmark.itertuples(index=False):
        observation = predictor.observe_one(row.text)
        decision = route_prediction(observation, config)
        local_error = observation.local_prediction != row.expected_sentiment
        reviewed += decision.should_review
        errors += local_error
        captured += decision.should_review and local_error
    assert reviewed == 43
    assert errors == 29
    assert captured == 26
    # Evaluation-only upper bound using the previously observed perfect reviews.
    assert (len(benchmark) - (errors - captured)) / len(benchmark) == pytest.approx(0.95)
