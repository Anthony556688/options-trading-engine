"""
Greeks calculation (Delta, Gamma, Theta, Vega, Rho)
"""
import math
from scipy.stats import norm
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Greeks:
    """Data class for option Greeks"""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


class GreeksCalculator:
    """Calculate the Greeks for option pricing"""

    @staticmethod
    def _calculate_d1_d2(S: float, K: float, T: float, r: float, sigma: float):
        """Calculate d1 and d2 for Black-Scholes"""
        if T <= 0:
            return None, None
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        return d1, d2

    @staticmethod
    def calculate_delta(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = "call",
    ) -> float:
        """
        Calculate delta (rate of change of option price w.r.t. stock price)
        
        Delta range:
        - Call: 0 to 1
        - Put: -1 to 0
        """
        if T <= 0:
            if option_type == "call":
                return 1.0 if S > K else 0.0
            else:
                return -1.0 if S < K else 0.0
        
        d1, _ = GreeksCalculator._calculate_d1_d2(S, K, T, r, sigma)
        
        if option_type == "call":
            return norm.cdf(d1)
        else:
            return norm.cdf(d1) - 1

    @staticmethod
    def calculate_gamma(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
    ) -> float:
        """
        Calculate gamma (rate of change of delta w.r.t. stock price)
        
        Gamma is always positive for both calls and puts
        """
        if T <= 0:
            return 0.0
        
        d1, _ = GreeksCalculator._calculate_d1_d2(S, K, T, r, sigma)
        return norm.pdf(d1) / (S * sigma * math.sqrt(T))

    @staticmethod
    def calculate_theta(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = "call",
    ) -> float:
        """
        Calculate theta (time decay per day)
        
        Returns:
            Theta per day (divide by 365)
        """
        if T <= 0:
            return 0.0
        
        d1, d2 = GreeksCalculator._calculate_d1_d2(S, K, T, r, sigma)
        
        first_term = -(S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
        
        if option_type == "call":
            second_term = -r * K * math.exp(-r * T) * norm.cdf(d2)
        else:
            second_term = r * K * math.exp(-r * T) * norm.cdf(-d2)
        
        # Return theta per day
        return (first_term + second_term) / 365

    @staticmethod
    def calculate_vega(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
    ) -> float:
        """
        Calculate vega (sensitivity to volatility change)
        
        Returns:
            Vega per 1% change in volatility
        """
        if T <= 0:
            return 0.0
        
        d1, _ = GreeksCalculator._calculate_d1_d2(S, K, T, r, sigma)
        return S * norm.pdf(d1) * math.sqrt(T) / 100

    @staticmethod
    def calculate_rho(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = "call",
    ) -> float:
        """
        Calculate rho (sensitivity to interest rate change)
        
        Returns:
            Rho per 1% change in interest rate
        """
        if T <= 0:
            return 0.0
        
        _, d2 = GreeksCalculator._calculate_d1_d2(S, K, T, r, sigma)
        
        if option_type == "call":
            return K * T * math.exp(-r * T) * norm.cdf(d2) / 100
        else:
            return -K * T * math.exp(-r * T) * norm.cdf(-d2) / 100

    @staticmethod
    def calculate_all_greeks(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = "call",
    ) -> Greeks:
        """
        Calculate all Greeks at once
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Volatility
            option_type: "call" or "put"
            
        Returns:
            Greeks object containing all values
        """
        return Greeks(
            delta=GreeksCalculator.calculate_delta(S, K, T, r, sigma, option_type),
            gamma=GreeksCalculator.calculate_gamma(S, K, T, r, sigma),
            theta=GreeksCalculator.calculate_theta(S, K, T, r, sigma, option_type),
            vega=GreeksCalculator.calculate_vega(S, K, T, r, sigma),
            rho=GreeksCalculator.calculate_rho(S, K, T, r, sigma, option_type),
        )
