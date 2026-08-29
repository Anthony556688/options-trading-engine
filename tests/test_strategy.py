"""
Test suite for strategy scoring
"""
import pytest
from core.data.provider import MockDataProvider
from core.strategy.scorer import StrategyScorer
from core.models import StrategyType


@pytest.fixture
def data_provider():
    """Fixture for data provider"""
    return MockDataProvider()


@pytest.fixture
def scorer():
    """Fixture for strategy scorer"""
    return StrategyScorer()


def test_score_strategies(scorer, data_provider):
    """Test strategy scoring"""
    chain = data_provider.get_option_chain("AAPL")
    scores = scorer.score_strategies(chain)
    assert len(scores) > 0
    # Verify scores are sorted by score (highest first)
    assert scores[0].score >= scores[-1].score if len(scores) > 1 else True


def test_iron_condor_scoring(scorer, data_provider):
    """Test Iron Condor strategy scoring"""
    chain = data_provider.get_option_chain("AAPL")
    scores = scorer.score_strategies(chain, [StrategyType.IRON_CONDOR])
    assert len(scores) > 0
    assert scores[0].strategy_type == StrategyType.IRON_CONDOR
    assert 0 <= scores[0].probability_of_profit <= 1
    assert scores[0].return_on_risk >= 0


def test_bull_call_spread_scoring(scorer, data_provider):
    """Test Bull Call Spread strategy scoring"""
    chain = data_provider.get_option_chain("AAPL")
    scores = scorer.score_strategies(chain, [StrategyType.BULL_CALL_SPREAD])
    assert len(scores) > 0
    assert scores[0].strategy_type == StrategyType.BULL_CALL_SPREAD
    assert scores[0].max_profit > 0


def test_long_straddle_scoring(scorer, data_provider):
    """Test Long Straddle strategy scoring"""
    chain = data_provider.get_option_chain("AAPL")
    scores = scorer.score_strategies(chain, [StrategyType.LONG_STRADDLE])
    assert len(scores) > 0
    assert scores[0].strategy_type == StrategyType.LONG_STRADDLE
    assert len(scores[0].legs) == 2
