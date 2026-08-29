"""
Strategy scoring and recommendation engine
"""
import logging
from typing import List
from datetime import datetime

from core.models import (
    OptionChain, StrategyScore, StrategyType, StrategyLeg
)
from core.strategy.strategies import IronCondor, BullCallSpread, LongStraddle

logger = logging.getLogger(__name__)


class StrategyScorer:
    """Score and rank strategies based on multiple criteria"""

    def __init__(self):
        """Initialize strategy scorer"""
        self.strategies = {
            StrategyType.IRON_CONDOR: IronCondor(),
            StrategyType.BULL_CALL_SPREAD: BullCallSpread(),
            StrategyType.LONG_STRADDLE: LongStraddle(),
        }

    def score_strategies(
        self,
        option_chain: OptionChain,
        strategy_types: List[StrategyType] = None,
    ) -> List[StrategyScore]:
        """
        Score all applicable strategies for an option chain
        
        Args:
            option_chain: Option chain to analyze
            strategy_types: Specific strategies to score (default: all)
            
        Returns:
            List of strategy scores sorted by score (highest first)
        """
        if strategy_types is None:
            strategy_types = list(StrategyType)

        scores = []
        
        for strategy_type in strategy_types:
            if strategy_type not in self.strategies:
                continue
                
            try:
                score = self._score_single_strategy(
                    option_chain,
                    strategy_type,
                    self.strategies[strategy_type]
                )
                if score and score.max_loss != 0:  # Valid strategy
                    scores.append(score)
            except Exception as e:
                logger.warning(f"Error scoring {strategy_type}: {e}")
                continue

        # Sort by score (highest first)
        return sorted(scores, key=lambda x: x.score, reverse=True)

    def _score_single_strategy(
        self,
        option_chain: OptionChain,
        strategy_type: StrategyType,
        strategy,
    ) -> StrategyScore:
        """
        Score a single strategy
        
        Args:
            option_chain: Option chain
            strategy_type: Type of strategy
            strategy: Strategy object
            
        Returns:
            StrategyScore or None if invalid
        """
        # Identify legs
        legs = strategy.identify_legs(option_chain)
        if not legs:
            return None

        # Calculate PnL
        max_profit, max_loss = strategy.calculate_pnl(legs, option_chain.underlying_price)
        if max_loss <= 0:
            return None

        # Calculate probability of profit
        pop = strategy.calculate_probability_of_profit(legs, option_chain.underlying_price)

        # Calculate return on risk
        ror = max_profit / abs(max_loss) if max_loss != 0 else 0.0

        # Calculate breakeven points
        breakevens = self._calculate_breakevens(legs, strategy_type)

        # Calculate composite score (0-100)
        score = self._calculate_composite_score(pop, ror, legs, strategy_type)

        # Calculate Greeks summary
        greeks_summary = self._calculate_greeks_summary(legs)

        return StrategyScore(
            strategy_type=strategy_type,
            symbol=option_chain.symbol,
            score=score,
            probability_of_profit=pop,
            return_on_risk=ror,
            max_profit=max_profit,
            max_loss=max_loss,
            breakeven_points=breakevens,
            legs=legs,
            greeks_summary=greeks_summary,
            rationale=self._generate_rationale(strategy_type, pop, ror),
        )

    def _calculate_composite_score(self, pop: float, ror: float, legs: List[StrategyLeg], strategy_type: StrategyType) -> float:
        """
        Calculate composite score (0-100)
        
        Weighting:
        - 40% Probability of Profit
        - 30% Return on Risk
        - 20% Liquidity (volume + OI)
        - 10% Theta (time decay)
        """
        # Base score from POP (0-40)
        pop_score = pop * 40

        # RoR score (0-30, capped at RoR=1.0)
        ror_score = min(ror, 1.0) * 30

        # Liquidity score from volume and OI
        avg_volume = sum(leg.option.volume for leg in legs) / len(legs) if legs else 0
        avg_oi = sum(leg.option.open_interest for leg in legs) / len(legs) if legs else 0
        liquidity_score = min((avg_volume + avg_oi) / 500, 20)

        # Theta score (time decay benefit)
        avg_theta = sum(leg.option.greeks.theta if leg.option.greeks else 0 for leg in legs) / len(legs) if legs else 0
        theta_score = min(abs(avg_theta) * 100, 10)

        total_score = pop_score + ror_score + liquidity_score + theta_score
        return min(total_score, 100.0)

    def _calculate_breakevens(self, legs: List[StrategyLeg], strategy_type: StrategyType) -> List[float]:
        """
        Calculate breakeven points for strategy
        """
        if not legs:
            return []

        breakevens = []
        total_cost = sum(leg.total_cost for leg in legs)

        if strategy_type == StrategyType.IRON_CONDOR:
            if len(legs) >= 2:
                short_call_strike = legs[0].option.strike
                short_put_strike = legs[2].option.strike if len(legs) > 2 else legs[1].option.strike
                breakevens = [short_put_strike - (total_cost / 100), short_call_strike + (total_cost / 100)]

        elif strategy_type == StrategyType.BULL_CALL_SPREAD:
            if len(legs) >= 2:
                long_strike = legs[0].option.strike
                breakevens = [long_strike + (total_cost / 100)]

        elif strategy_type == StrategyType.LONG_STRADDLE:
            if len(legs) >= 2:
                strike = legs[0].option.strike
                premium = total_cost / 100
                breakevens = [strike - premium, strike + premium]

        return breakevens

    def _calculate_greeks_summary(self, legs: List[StrategyLeg]) -> dict:
        """
        Calculate Greeks summary for the entire strategy
        """
        if not legs or not any(leg.option.greeks for leg in legs):
            return {}

        total_delta = sum((leg.quantity * leg.option.greeks.delta if leg.option.greeks else 0) for leg in legs)
        total_gamma = sum((leg.quantity * leg.option.greeks.gamma if leg.option.greeks else 0) for leg in legs)
        total_theta = sum((leg.quantity * leg.option.greeks.theta if leg.option.greeks else 0) for leg in legs)
        total_vega = sum((leg.quantity * leg.option.greeks.vega if leg.option.greeks else 0) for leg in legs)

        return {
            "delta": total_delta,
            "gamma": total_gamma,
            "theta": total_theta,
            "vega": total_vega,
        }

    def _generate_rationale(self, strategy_type: StrategyType, pop: float, ror: float) -> str:
        """
        Generate human-readable rationale for the strategy
        """
        rationale = f"{strategy_type.value}: "
        
        if pop > 0.6:
            rationale += "High probability of profit. "
        elif pop > 0.5:
            rationale += "Moderate probability of profit. "
        else:
            rationale += "Lower probability of profit. "

        if ror > 0.5:
            rationale += "Good risk-reward ratio. "
        elif ror > 0.2:
            rationale += "Acceptable risk-reward ratio. "
        else:
            rationale += "Limited profit potential. "

        return rationale
