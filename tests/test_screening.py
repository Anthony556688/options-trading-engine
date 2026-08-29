"""
Test suite for options screening module
"""
import pytest
from core.data.provider import MockDataProvider
from core.screening.screener import OptionScreener
from core.models import ScreeningCriteria, OptionType


@pytest.fixture
def data_provider():
    """Fixture for data provider"""
    return MockDataProvider()


@pytest.fixture
def screener():
    """Fixture for screener"""
    return OptionScreener()


def test_get_option_chain(data_provider):
    """Test getting option chain"""
    chain = data_provider.get_option_chain("AAPL")
    assert chain.symbol == "AAPL"
    assert len(chain.calls) > 0
    assert len(chain.puts) > 0
    assert chain.underlying_price > 0


def test_screening_basic(screener, data_provider):
    """Test basic screening"""
    chain = data_provider.get_option_chain("AAPL")
    criteria = ScreeningCriteria(
        min_volume=0,
        min_open_interest=0,
    )
    result = screener.screen_options(chain, criteria)
    assert result.symbol == "AAPL"
    assert len(result.matching_options) > 0


def test_screening_by_option_type(screener, data_provider):
    """Test screening by option type"""
    chain = data_provider.get_option_chain("AAPL")
    criteria = ScreeningCriteria(option_type=OptionType.CALL)
    result = screener.screen_options(chain, criteria)
    assert all(opt.option_type == OptionType.CALL for opt in result.matching_options)


def test_screening_by_dte(screener, data_provider):
    """Test screening by days to expiration"""
    chain = data_provider.get_option_chain("AAPL")
    criteria = ScreeningCriteria(min_dte=20, max_dte=40)
    result = screener.screen_options(chain, criteria)
    assert all(20 <= opt.days_to_expiration <= 40 for opt in result.matching_options)
