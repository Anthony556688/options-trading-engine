"""
Data provider for fetching option data
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from core.models import OptionData, OptionChain, OptionType

logger = logging.getLogger(__name__)


class DataProvider(ABC):
    """Abstract base class for data providers"""

    @abstractmethod
    def get_option_chain(self, symbol: str, expiration_date: Optional[datetime] = None) -> OptionChain:
        """Fetch option chain for a symbol"""
        pass

    @abstractmethod
    def get_historical_data(self, symbol: str, start_date: datetime, end_date: datetime):
        """Fetch historical data"""
        pass


class MockDataProvider(DataProvider):
    """Mock data provider for testing and development"""

    def __init__(self):
        """Initialize mock provider"""
        pass

    def get_option_chain(self, symbol: str, expiration_date: Optional[datetime] = None) -> OptionChain:
        """
        Generate mock option chain
        """
        from core.pricing.greeks import GreeksCalculator
        
        underlying_price = 100.0
        strikes = [95, 97.5, 100, 102.5, 105]
        dte = 30
        T = dte / 365
        r = 0.05
        sigma = 0.25

        calls = []
        puts = []

        for strike in strikes:
            from core.pricing.black_scholes import BlackScholesCalculator
            call_price = BlackScholesCalculator.calculate_call_price(underlying_price, strike, T, r, sigma)
            put_price = BlackScholesCalculator.calculate_put_price(underlying_price, strike, T, r, sigma)

            greeks_call = GreeksCalculator.calculate_all_greeks(underlying_price, strike, T, r, sigma, "call")
            greeks_put = GreeksCalculator.calculate_all_greeks(underlying_price, strike, T, r, sigma, "put")

            exp_date = datetime.now().replace(day=datetime.now().day + dte)
            
            calls.append(OptionData(
                symbol=symbol,
                strike=strike,
                expiration_date=exp_date,
                option_type=OptionType.CALL,
                current_price=call_price,
                bid=call_price * 0.98,
                ask=call_price * 1.02,
                volume=100,
                open_interest=500,
                implied_volatility=sigma,
                underlying_price=underlying_price,
                greeks=greeks_call,
            ))

            puts.append(OptionData(
                symbol=symbol,
                strike=strike,
                expiration_date=exp_date,
                option_type=OptionType.PUT,
                current_price=put_price,
                bid=put_price * 0.98,
                ask=put_price * 1.02,
                volume=100,
                open_interest=500,
                implied_volatility=sigma,
                underlying_price=underlying_price,
                greeks=greeks_put,
            ))

        return OptionChain(
            symbol=symbol,
            underlying_price=underlying_price,
            calls=calls,
            puts=puts,
        )

    def get_historical_data(self, symbol: str, start_date: datetime, end_date: datetime):
        """Mock historical data"""
        return {}
