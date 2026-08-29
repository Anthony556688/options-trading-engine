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
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            sigma: Volatility (annualized)
            
        Returns:
            Put option price
        """
        if T <= 0:
            return max(K - S, 0)
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        put_price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        return max(put_price, 0)

    @staticmethod
    def calculate_both_prices(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
    ) -> Tuple[float, float]:
        """
        Calculate both call and put prices
        
        Returns:
            Tuple of (call_price, put_price)
        """
        call = BlackScholesCalculator.calculate_call_price(S, K, T, r, sigma)
        put = BlackScholesCalculator.calculate_put_price(S, K, T, r, sigma)
        return call, put

    @staticmethod
    def implied_volatility(
        option_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: str = "call",
        initial_guess: float = 0.3,
        tolerance: float = 1e-6,
        max_iterations: int = 100,
    ) -> float:
        """
        Calculate implied volatility using Newton-Raphson method
        
        Args:
            option_price: Current option market price
            S: Current stock price
            K: Strike price
            T: Time to expiration
            r: Risk-free rate
            option_type: "call" or "put"
            initial_guess: Starting volatility estimate
            tolerance: Convergence tolerance
            max_iterations: Maximum iterations
            
        Returns:
            Implied volatility
        """
        sigma = initial_guess
        
        for i in range(max_iterations):
            if option_type == "call":
                price = BlackScholesCalculator.calculate_call_price(S, K, T, r, sigma)
            else:
                price = BlackScholesCalculator.calculate_put_price(S, K, T, r, sigma)
            
            diff = price - option_price
            
            if abs(diff) < tolerance:
                return sigma
            
            # Calculate vega for Newton-Raphson
            from .greeks import GreeksCalculator
            vega = GreeksCalculator.calculate_vega(S, K, T, r, sigma)
            
            if abs(vega) < 1e-10:
                break
            
            sigma = sigma - diff / vega
            
            # Keep sigma positive
            if sigma <= 0:
                sigma = initial_guess / 2
        
        logger.warning(f"IV calculation did not converge after {max_iterations} iterations")
        return sigma
