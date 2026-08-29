"""
Data models for options trading engine
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class OptionType(str, Enum):
    """Option type enumeration"""
    CALL = "call"
    PUT = "put"


class StrategyType(str, Enum):
    """Strategy type enumeration"""
    IRON_CONDOR = "iron_condor"
    BULL_CALL_SPREAD = "bull_call_spread"
    LONG_STRADDLE = "long_straddle"
    BULL_PUT_SPREAD = "bull_put_spread"
    BEAR_CALL_SPREAD = "bear_call_spread"
    BEAR_PUT_SPREAD = "bear_put_spread"


@dataclass
class Greeks:
    """Option Greeks"""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


@dataclass
class OptionData:
    """Single option contract data"""
    symbol: str
    strike: float
    expiration_date: datetime
    option_type: OptionType
    current_price: float
    bid: float
    ask: float
    volume: int
    open_interest: int
    implied_volatility: float
    underlying_price: float
    last_updated: datetime = field(default_factory=datetime.now)
    greeks: Optional[Greeks] = None

    @property
    def days_to_expiration(self) -> float:
        """Calculate days to expiration"""
        delta = self.expiration_date - datetime.now()
        return delta.days + delta.seconds / 86400

    @property
    def mid_price(self) -> float:
        """Calculate mid price"""
        return (self.bid + self.ask) / 2

    @property
    def moneyness(self) -> float:
        """Calculate moneyness (strike / underlying price)"""
        if self.underlying_price <= 0:
            return 0.0
        return self.strike / self.underlying_price


@dataclass
class OptionChain:
    """Option chain for a given underlying"""
    symbol: str
    underlying_price: float
    calls: List[OptionData]
    puts: List[OptionData]
    last_updated: datetime = field(default_factory=datetime.now)

    def get_expiration_dates(self) -> set:
        """Get all unique expiration dates"""
        dates = set()
        for option in self.calls + self.puts:
            dates.add(option.expiration_date.date())
        return dates

    def get_strikes(self, expiration_date: datetime = None) -> set:
        """Get all strikes for a given expiration"""
        options = self.calls + self.puts
        if expiration_date:
            options = [o for o in options if o.expiration_date.date() == expiration_date.date()]
        return set(o.strike for o in options)


@dataclass
class StrategyLeg:
    """Single leg of an options strategy"""
    option: OptionData
    quantity: int  # Positive for long, negative for short
    entry_price: float

    @property
    def total_cost(self) -> float:
        """Total cost/credit for this leg"""
        return self.entry_price * self.quantity * 100  # Multiply by 100 for contract multiplier


@dataclass
class StrategyScore:
    """Strategy scoring results"""
    strategy_type: StrategyType
    symbol: str
    score: float  # 0-100
    probability_of_profit: float
    return_on_risk: float
    max_profit: float
    max_loss: float
    breakeven_points: List[float]
    legs: List[StrategyLeg]
    greeks_summary: Optional[dict] = None
    rationale: str = ""
    last_calculated: datetime = field(default_factory=datetime.now)

    def __lt__(self, other):
        """Allow sorting by score"""
        return self.score < other.score


@dataclass
class ScreeningCriteria:
    """Screening filter criteria"""
    symbols: Optional[List[str]] = None
    min_price: float = 1.0
    max_price: float = 1000.0
    min_volume: int = 100
    min_open_interest: int = 50
    min_iv_percentile: float = 0.0
    max_iv_percentile: float = 100.0
    min_dte: int = 1
    max_dte: int = 365
    option_type: Optional[OptionType] = None
    moneyness_range: tuple = (0.8, 1.2)  # (lower, upper)
    sort_by: str = "score"  # "score", "ror", "pop", "theta"
    sort_order: str = "desc"  # "asc" or "desc"


@dataclass
class ScreeningResult:
    """Screening results"""
    symbol: str
    option_chain: OptionChain
    matching_options: List[OptionData]
    recommended_strategies: List[StrategyScore]
    scan_timestamp: datetime = field(default_factory=datetime.now)
