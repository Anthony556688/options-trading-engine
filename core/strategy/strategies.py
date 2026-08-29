"""
Options strategy module with three core strategies
"""
from abc import ABC, abstractmethod
from typing import List, Tuple
from dataclasses import dataclass
from core.models import (
    OptionData, OptionType, StrategyLeg, StrategyScore, StrategyType
)
from core.pricing.greeks import GreeksCalculator, Greeks


class BaseStrategy(ABC):
    """Base class for all option strategies"""

    @abstractmethod
    def identify_legs(self, option_chain) -> List[StrategyLeg]:
        """Identify legs for this strategy"""
        pass

    @abstractmethod
    def calculate_pnl(
        self,
        legs: List[StrategyLeg],
        underlying_price: float,
    ) -> Tuple[float, float]:
        """Calculate max profit and max loss"""
        pass

    @abstractmethod
    def calculate_probability_of_profit(
        self,
        legs: List[StrategyLeg],
        underlying_price: float,
    ) -> float:
        """Calculate probability of profit"""
        pass


class IronCondor(BaseStrategy):
    """
    Iron Condor Strategy:
    - Sell OTM Call Spread (1 short call + 1 long call)
    - Sell OTM Put Spread (1 short put + 1 long put)
    - Neutral outlook, benefits from time decay
    - Max profit = credit received
    - Max loss = width of spreads - credit
    """

    def identify_legs(self, option_chain) -> List[StrategyLeg]:
        """
        Identify Iron Condor legs from option chain
        
        Structure:
        1. Short OTM Call (first call above ATM)
        2. Long Call (further OTM)
        3. Short OTM Put (first put below ATM)
        4. Long Put (further OTM)
        """
        underlying = option_chain.underlying_price
        calls = sorted([c for c in option_chain.calls], key=lambda x: x.strike)
        puts = sorted([p for p in option_chain.puts], key=lambda x: x.strike, reverse=True)

        legs = []

        # Short call spread (sell higher premium, buy lower premium)
        if len(calls) >= 2:
            short_call = next((c for c in calls if c.strike > underlying), None)
            if short_call:
                idx = calls.index(short_call)
                if idx + 1 < len(calls):
                    long_call = calls[idx + 1]
                    legs.append(StrategyLeg(short_call, -1, short_call.current_price))
                    legs.append(StrategyLeg(long_call, 1, long_call.current_price))

        # Short put spread
        if len(puts) >= 2:
            short_put = next((p for p in puts if p.strike < underlying), None)
            if short_put:
                idx = puts.index(short_put)
                if idx + 1 < len(puts):
                    long_put = puts[idx + 1]
                    legs.append(StrategyLeg(short_put, -1, short_put.current_price))
                    legs.append(StrategyLeg(long_put, 1, long_put.current_price))

        return legs

    def calculate_pnl(self, legs: List[StrategyLeg], underlying_price: float) -> Tuple[float, float]:
        """
        Calculate max profit and max loss for Iron Condor
        
        Returns:
            (max_profit, max_loss) tuple in dollars
        """
        if len(legs) != 4:
            return 0.0, 0.0

        call_short = legs[0]
        call_long = legs[1]
        put_short = legs[2]
        put_long = legs[3]

        # Net credit received
        net_credit = (
            abs(call_short.total_cost) + abs(put_short.total_cost)
            - abs(call_long.total_cost) - abs(put_long.total_cost)
        )

        # Max profit = net credit
        max_profit = net_credit

        # Max loss = width of spread - credit
        call_width = abs(call_short.option.strike - call_long.option.strike) * 100
        put_width = abs(put_short.option.strike - put_long.option.strike) * 100

        max_loss = call_width - net_credit

        return max_profit, max_loss

    def calculate_probability_of_profit(self, legs: List[StrategyLeg], underlying_price: float) -> float:
        """
        Calculate POP for Iron Condor
        
        For Iron Condor, POP ≈ Delta of short call + Delta of short put + adjustments
        """
        if len(legs) != 4:
            return 0.5

        # Sum of deltas for short positions (which represent profitable range)
        short_call_delta = abs(legs[0].option.greeks.delta) if legs[0].option.greeks else 0.2
        short_put_delta = abs(legs[2].option.greeks.delta) if legs[2].option.greeks else 0.2

        pop = 1 - (short_call_delta + short_put_delta) * 0.5
        return min(max(pop, 0.0), 1.0)


class BullCallSpread(BaseStrategy):
    """
    Bull Call Spread Strategy:
    - Long ATM/ITM Call
    - Short OTM Call (further out)
    - Bullish outlook
    - Limited max profit and max loss
    - Lower cost than long call alone
    """

    def identify_legs(self, option_chain) -> List[StrategyLeg]:
        """
        Identify Bull Call Spread legs
        
        Structure:
        1. Long Call (ATM or slightly OTM)
        2. Short Call (further OTM)
        """
        underlying = option_chain.underlying_price
        calls = sorted([c for c in option_chain.calls], key=lambda x: x.strike)

        legs = []

        # Find ATM call
        atm_call = min((c for c in calls), key=lambda x: abs(x.strike - underlying), default=None)
        if atm_call:
            idx = calls.index(atm_call)
            # Find OTM call (next strike up)
            if idx + 1 < len(calls):
                otm_call = calls[idx + 1]
                legs.append(StrategyLeg(atm_call, 1, atm_call.current_price))
                legs.append(StrategyLeg(otm_call, -1, otm_call.current_price))

        return legs

    def calculate_pnl(self, legs: List[StrategyLeg], underlying_price: float) -> Tuple[float, float]:
        """
        Calculate max profit and max loss for Bull Call Spread
        
        Returns:
            (max_profit, max_loss) tuple in dollars
        """
        if len(legs) != 2:
            return 0.0, 0.0

        long_call = legs[0]
        short_call = legs[1]

        # Net debit paid
        net_debit = abs(long_call.total_cost) - abs(short_call.total_cost)

        # Max loss = debit paid
        max_loss = net_debit

        # Max profit = width of spread - debit
        spread_width = (short_call.option.strike - long_call.option.strike) * 100
        max_profit = spread_width - net_debit

        return max_profit, max_loss

    def calculate_probability_of_profit(self, legs: List[StrategyLeg], underlying_price: float) -> float:
        """
        Calculate POP for Bull Call Spread
        
        POP ≈ probability that underlying closes above short strike at expiration
        """
        if len(legs) != 2:
            return 0.5

        short_call = legs[1]
        # Approximate using delta (delta ≈ probability ITM)
        short_delta = abs(short_call.option.greeks.delta) if short_call.option.greeks else 0.3
        pop = short_delta
        return min(max(pop, 0.0), 1.0)


class LongStraddle(BaseStrategy):
    """
    Long Straddle Strategy:
    - Long ATM Call
    - Long ATM Put
    - Bullish on volatility (expects large move)
    - Benefits from IV expansion
    - Max loss = premium paid
    - Max profit = unlimited (theoretically)
    """

    def identify_legs(self, option_chain) -> List[StrategyLeg]:
        """
        Identify Long Straddle legs
        
        Structure:
        1. Long Call (ATM)
        2. Long Put (ATM, same strike)
        """
        underlying = option_chain.underlying_price

        # Find ATM call
        atm_call = min(
            (c for c in option_chain.calls),
            key=lambda x: abs(x.strike - underlying),
            default=None
        )

        # Find matching ATM put
        atm_put = None
        if atm_call:
            atm_put = next(
                (p for p in option_chain.puts if abs(p.strike - atm_call.strike) < 0.01),
                None
            )

        legs = []
        if atm_call and atm_put:
            legs.append(StrategyLeg(atm_call, 1, atm_call.current_price))
            legs.append(StrategyLeg(atm_put, 1, atm_put.current_price))

        return legs

    def calculate_pnl(self, legs: List[StrategyLeg], underlying_price: float) -> Tuple[float, float]:
        """
        Calculate max profit and max loss for Long Straddle
        
        Returns:
            (max_profit, max_loss) tuple in dollars
        """
        if len(legs) != 2:
            return 0.0, 0.0

        call = legs[0]
        put = legs[1]

        # Total premium paid
        total_premium = abs(call.total_cost) + abs(put.total_cost)

        # Max loss = total premium
        max_loss = total_premium

        # Max profit = unlimited (in theory)
        # For practical purposes, estimate based on strike and volatility
        strike = call.option.strike
        max_profit = max_loss * 0.5  # Conservative estimate

        return max_profit, max_loss

    def calculate_probability_of_profit(self, legs: List[StrategyLeg], underlying_price: float) -> float:
        """
        Calculate POP for Long Straddle
        
        POP increases with expected move vs break-even points
        """
        if len(legs) != 2:
            return 0.5

        call = legs[0]
        put = legs[1]
        strike = call.option.strike

        total_premium = abs(call.total_cost) + abs(put.total_cost)
        breakeven_up = strike + (total_premium / 100)
        breakeven_down = strike - (total_premium / 100)

        # Straddle POP depends on expected volatility vs implied volatility
        # Using IV as proxy: higher IV = higher POP for straddle buyer
        iv = call.option.implied_volatility
        pop = min(0.3 + (iv * 0.5), 0.7)
        return pop
