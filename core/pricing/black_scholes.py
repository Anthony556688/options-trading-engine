"""
Black-Scholes option pricing model implementation
"""
import math
from scipy.stats import norm
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class BlackScholesCalculator:
    """Calculate option prices using Black-Scholes model"""

    @staticmethod
    def calculate_call_price(
        S: float,  # Current stock price
        K: float,  # Strike price
        T: float,  # Time to expiration (in years)
        r: float,  # Risk-free rate
        sigma: float,  # Volatility (standard deviation)
    ) -> float:
        """
        Calculate European call option price using Black-Scholes formula
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            sigma: Volatility (annualized)
            
        Returns:
            Call option price
        """
        if T <= 0:
            return max(S - K, 0)
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        call_price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
        return max(call_price, 0)

    @staticmethod
    def calculate_put_price(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
    ) -> float:
        """
        Calculate European put option price using Black-Scholes formula
        """
        if T <= 0:
            return max(K - S, 0)
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        put_price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        return max(put_price, 0)
