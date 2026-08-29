"""
Options screening engine for filtering and discovering opportunities
"""
import logging
from typing import List, Optional
from datetime import datetime
from core.models import (
    OptionData, OptionChain, OptionType, ScreeningCriteria,
    ScreeningResult
)

logger = logging.getLogger(__name__)


class OptionScreener:
    """Screen options based on multiple criteria"""

    def __init__(self):
        """Initialize screener"""
        pass

    def screen_options(
        self,
        option_chain: OptionChain,
        criteria: ScreeningCriteria,
    ) -> ScreeningResult:
        """
        Screen options based on criteria
        
        Args:
            option_chain: Option chain to screen
            criteria: Screening criteria
            
        Returns:
            ScreeningResult with filtered options
        """
        logger.info(f"Screening {option_chain.symbol} with criteria: {criteria}")
        
        # Start with all options
        all_options = option_chain.calls + option_chain.puts
        
        # Apply filters
        filtered = self._apply_filters(all_options, criteria, option_chain.underlying_price)
        
        logger.info(f"Filtered to {len(filtered)} options from {len(all_options)} total")
        
        # Sort results
        sorted_options = self._sort_options(filtered, criteria.sort_by, criteria.sort_order)
        
        return ScreeningResult(
            symbol=option_chain.symbol,
            option_chain=option_chain,
            matching_options=sorted_options,
            recommended_strategies=[],  # Will be populated by strategy scorer
        )

    def _apply_filters(
        self,
        options: List[OptionData],
        criteria: ScreeningCriteria,
        underlying_price: float,
    ) -> List[OptionData]:
        """
        Apply all screening filters
        
        Args:
            options: List of options to filter
            criteria: Filtering criteria
            underlying_price: Current underlying price
            
        Returns:
            Filtered list of options
        """
        filtered = options

        # Filter by option type
        if criteria.option_type:
            filtered = [o for o in filtered if o.option_type == criteria.option_type]

        # Filter by underlying price
        filtered = [
            o for o in filtered
            if criteria.min_price <= o.underlying_price <= criteria.max_price
        ]

        # Filter by volume
        filtered = [o for o in filtered if o.volume >= criteria.min_volume]

        # Filter by open interest
        filtered = [o for o in filtered if o.open_interest >= criteria.min_open_interest]

        # Filter by days to expiration
        filtered = [
            o for o in filtered
            if criteria.min_dte <= o.days_to_expiration <= criteria.max_dte
        ]

        # Filter by moneyness
        lower, upper = criteria.moneyness_range
        filtered = [
            o for o in filtered
            if lower <= o.moneyness <= upper
        ]

        return filtered

    def _sort_options(
        self,
        options: List[OptionData],
        sort_by: str,
        sort_order: str = "desc",
    ) -> List[OptionData]:
        """
        Sort options by criteria
        
        Args:
            options: List of options to sort
            sort_by: Sort key ("volume", "oi", "iv", "price")
            sort_order: "asc" or "desc"
            
        Returns:
            Sorted list of options
        """
        reverse = sort_order == "desc"

        if sort_by == "volume":
            return sorted(options, key=lambda o: o.volume, reverse=reverse)
        elif sort_by == "oi":
            return sorted(options, key=lambda o: o.open_interest, reverse=reverse)
        elif sort_by == "iv":
            return sorted(options, key=lambda o: o.implied_volatility, reverse=reverse)
        elif sort_by == "price":
            return sorted(options, key=lambda o: o.current_price, reverse=reverse)
        else:
            return sorted(options, key=lambda o: o.volume, reverse=reverse)
