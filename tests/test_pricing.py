"""
Test suite for option pricing
"""
import pytest
from core.pricing.black_scholes import BlackScholesCalculator
from core.pricing.greeks import GreeksCalculator


def test_call_option_pricing():
    """Test call option pricing"""
    price = BlackScholesCalculator.calculate_call_price(
        S=100, K=100, T=0.25, r=0.05, sigma=0.2
    )
    assert price > 0
    assert price < 100


def test_put_option_pricing():
    """Test put option pricing"""
    price = BlackScholesCalculator.calculate_put_price(
        S=100, K=100, T=0.25, r=0.05, sigma=0.2
    )
    assert price > 0
    assert price < 100


def test_call_put_parity():
    """Test put-call parity"""
    S, K, T, r, sigma = 100, 100, 0.25, 0.05, 0.2
    call_price = BlackScholesCalculator.calculate_call_price(S, K, T, r, sigma)
    put_price = BlackScholesCalculator.calculate_put_price(S, K, T, r, sigma)
    
    # Call - Put = S - K*e^(-rT)
    lhs = call_price - put_price
    rhs = S - K * (2.71828 ** (-r * T))
    
    assert abs(lhs - rhs) < 0.01


def test_calculate_delta():
    """Test delta calculation"""
    delta = GreeksCalculator.calculate_delta(
        S=100, K=100, T=0.25, r=0.05, sigma=0.2, option_type="call"
    )
    assert 0 <= delta <= 1


def test_calculate_gamma():
    """Test gamma calculation"""
    gamma = GreeksCalculator.calculate_gamma(
        S=100, K=100, T=0.25, r=0.05, sigma=0.2
    )
    assert gamma > 0


def test_calculate_theta():
    """Test theta calculation"""
    theta = GreeksCalculator.calculate_theta(
        S=100, K=100, T=0.25, r=0.05, sigma=0.2, option_type="call"
    )
    # Theta for long call is typically negative (time decay hurts long calls)
    assert theta < 0


def test_calculate_vega():
    """Test vega calculation"""
    vega = GreeksCalculator.calculate_vega(
        S=100, K=100, T=0.25, r=0.05, sigma=0.2
    )
    assert vega > 0


def test_calculate_all_greeks():
    """Test calculating all Greeks at once"""
    greeks = GreeksCalculator.calculate_all_greeks(
        S=100, K=100, T=0.25, r=0.05, sigma=0.2, option_type="call"
    )
    assert greeks.delta is not None
    assert greeks.gamma is not None
    assert greeks.theta is not None
    assert greeks.vega is not None
    assert greeks.rho is not None
