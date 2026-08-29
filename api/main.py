"""
REST API for options trading engine using FastAPI
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from core.data.provider import MockDataProvider
from core.screening.screener import OptionScreener
from core.strategy.scorer import StrategyScorer
from core.models import ScreeningCriteria, StrategyType, OptionType

# Initialize FastAPI app
app = FastAPI(
    title="Options Trading Engine API",
    description="High-performance options screening and strategy recommendation engine",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
data_provider = MockDataProvider()
screener = OptionScreener()
strategy_scorer = StrategyScorer()


# Request/Response Models
class ScreeningRequest(BaseModel):
    """Screening request model"""
    symbol: str
    min_volume: int = 100
    min_open_interest: int = 50
    min_dte: int = 7
    max_dte: int = 60
    option_type: Optional[str] = None
    sort_by: str = "volume"


class StrategyRecommendationRequest(BaseModel):
    """Strategy recommendation request"""
    symbol: str
    strategies: Optional[List[str]] = None  # iron_condor, bull_call_spread, long_straddle


class GreeksResponse(BaseModel):
    """Greeks response model"""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


class OptionResponse(BaseModel):
    """Option data response model"""
    symbol: str
    strike: float
    expiration_date: datetime
    option_type: str
    current_price: float
    bid: float
    ask: float
    volume: int
    open_interest: int
    implied_volatility: float
    underlying_price: float
    days_to_expiration: float
    moneyness: float
    greeks: Optional[GreeksResponse] = None


class StrategyLegResponse(BaseModel):
    """Strategy leg response"""
    option: OptionResponse
    quantity: int
    entry_price: float
    total_cost: float


class StrategyScoreResponse(BaseModel):
    """Strategy score response model"""
    strategy_type: str
    symbol: str
    score: float
    probability_of_profit: float
    return_on_risk: float
    max_profit: float
    max_loss: float
    breakeven_points: List[float]
    legs: List[StrategyLegResponse]
    rationale: str


class ScreeningResponse(BaseModel):
    """Screening response model"""
    symbol: str
    matching_options_count: int
    matching_options: List[OptionResponse]
    recommended_strategies: List[StrategyScoreResponse]
    scan_timestamp: datetime


# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Options Trading Engine API",
        "version": "1.0.0",
        "endpoints": {
            "screening": "/api/v1/screening",
            "strategies": "/api/v1/strategies",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/api/v1/screening", response_model=ScreeningResponse)
async def screen_options(request: ScreeningRequest):
    """
    Screen options based on criteria
    
    Query parameters:
    - symbol: Stock symbol (required)
    - min_volume: Minimum trading volume (default: 100)
    - min_open_interest: Minimum open interest (default: 50)
    - min_dte: Minimum days to expiration (default: 7)
    - max_dte: Maximum days to expiration (default: 60)
    - option_type: "call" or "put" (optional)
    - sort_by: "volume", "oi", "iv", or "price" (default: volume)
    """
    try:
        # Fetch option chain
        option_chain = data_provider.get_option_chain(request.symbol)
        
        # Build screening criteria
        criteria = ScreeningCriteria(
            min_volume=request.min_volume,
            min_open_interest=request.min_open_interest,
            min_dte=request.min_dte,
            max_dte=request.max_dte,
            option_type=OptionType(request.option_type) if request.option_type else None,
            sort_by=request.sort_by,
        )
        
        # Screen options
        result = screener.screen_options(option_chain, criteria)
        
        # Score strategies
        strategies = strategy_scorer.score_strategies(option_chain)
        result.recommended_strategies = strategies
        
        # Convert to response
        matching_options = []
        for opt in result.matching_options[:50]:  # Limit to top 50
            greeks_resp = None
            if opt.greeks:
                greeks_resp = GreeksResponse(
                    delta=opt.greeks.delta,
                    gamma=opt.greeks.gamma,
                    theta=opt.greeks.theta,
                    vega=opt.greeks.vega,
                    rho=opt.greeks.rho,
                )
            
            matching_options.append(OptionResponse(
                symbol=opt.symbol,
                strike=opt.strike,
                expiration_date=opt.expiration_date,
                option_type=opt.option_type.value,
                current_price=opt.current_price,
                bid=opt.bid,
                ask=opt.ask,
                volume=opt.volume,
                open_interest=opt.open_interest,
                implied_volatility=opt.implied_volatility,
                underlying_price=opt.underlying_price,
                days_to_expiration=opt.days_to_expiration,
                moneyness=opt.moneyness,
                greeks=greeks_resp,
            ))
        
        # Convert strategies
        recommended_strategies = []
        for strat in result.recommended_strategies:
            legs = []
            for leg in strat.legs:
                greeks_resp = None
                if leg.option.greeks:
                    greeks_resp = GreeksResponse(
                        delta=leg.option.greeks.delta,
                        gamma=leg.option.greeks.gamma,
                        theta=leg.option.greeks.theta,
                        vega=leg.option.greeks.vega,
                        rho=leg.option.greeks.rho,
                    )
                
                legs.append(StrategyLegResponse(
                    option=OptionResponse(
                        symbol=leg.option.symbol,
                        strike=leg.option.strike,
                        expiration_date=leg.option.expiration_date,
                        option_type=leg.option.option_type.value,
                        current_price=leg.option.current_price,
                        bid=leg.option.bid,
                        ask=leg.option.ask,
                        volume=leg.option.volume,
                        open_interest=leg.option.open_interest,
                        implied_volatility=leg.option.implied_volatility,
                        underlying_price=leg.option.underlying_price,
                        days_to_expiration=leg.option.days_to_expiration,
                        moneyness=leg.option.moneyness,
                        greeks=greeks_resp,
                    ),
                    quantity=leg.quantity,
                    entry_price=leg.entry_price,
                    total_cost=leg.total_cost,
                ))
            
            recommended_strategies.append(StrategyScoreResponse(
                strategy_type=strat.strategy_type.value,
                symbol=strat.symbol,
                score=strat.score,
                probability_of_profit=strat.probability_of_profit,
                return_on_risk=strat.return_on_risk,
                max_profit=strat.max_profit,
                max_loss=strat.max_loss,
                breakeven_points=strat.breakeven_points,
                legs=legs,
                rationale=strat.rationale,
            ))
        
        return ScreeningResponse(
            symbol=request.symbol,
            matching_options_count=len(matching_options),
            matching_options=matching_options,
            recommended_strategies=recommended_strategies,
            scan_timestamp=datetime.now(),
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/strategies", response_model=List[StrategyScoreResponse])
async def recommend_strategies(request: StrategyRecommendationRequest):
    """
    Get strategy recommendations for a symbol
    """
    try:
        # Fetch option chain
        option_chain = data_provider.get_option_chain(request.symbol)
        
        # Parse requested strategies
        strategy_types = []
        if request.strategies:
            strategy_map = {
                "iron_condor": StrategyType.IRON_CONDOR,
                "bull_call_spread": StrategyType.BULL_CALL_SPREAD,
                "long_straddle": StrategyType.LONG_STRADDLE,
            }
            strategy_types = [strategy_map[s] for s in request.strategies if s in strategy_map]
        
        # Score strategies
        strategies = strategy_scorer.score_strategies(option_chain, strategy_types if strategy_types else None)
        
        # Convert to response
        recommended_strategies = []
        for strat in strategies:
            legs = []
            for leg in strat.legs:
                greeks_resp = None
                if leg.option.greeks:
                    greeks_resp = GreeksResponse(
                        delta=leg.option.greeks.delta,
                        gamma=leg.option.greeks.gamma,
                        theta=leg.option.greeks.theta,
                        vega=leg.option.greeks.vega,
                        rho=leg.option.greeks.rho,
                    )
                
                legs.append(StrategyLegResponse(
                    option=OptionResponse(
                        symbol=leg.option.symbol,
                        strike=leg.option.strike,
                        expiration_date=leg.option.expiration_date,
                        option_type=leg.option.option_type.value,
                        current_price=leg.option.current_price,
                        bid=leg.option.bid,
                        ask=leg.option.ask,
                        volume=leg.option.volume,
                        open_interest=leg.option.open_interest,
                        implied_volatility=leg.option.implied_volatility,
                        underlying_price=leg.option.underlying_price,
                        days_to_expiration=leg.option.days_to_expiration,
                        moneyness=leg.option.moneyness,
                        greeks=greeks_resp,
                    ),
                    quantity=leg.quantity,
                    entry_price=leg.entry_price,
                    total_cost=leg.total_cost,
                ))
            
            recommended_strategies.append(StrategyScoreResponse(
                strategy_type=strat.strategy_type.value,
                symbol=strat.symbol,
                score=strat.score,
                probability_of_profit=strat.probability_of_profit,
                return_on_risk=strat.return_on_risk,
                max_profit=strat.max_profit,
                max_loss=strat.max_loss,
                breakeven_points=strat.breakeven_points,
                legs=legs,
                rationale=strat.rationale,
            ))
        
        return recommended_strategies
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
