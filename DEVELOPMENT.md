# 期权交易引擎开发指南

## 架构概述

本项目采用模块化设计，分为以下几个核心层次：

```
┌─────────────────────────────────┐
│     REST API Layer (FastAPI)     │  <- 外部接口
├─────────────────────────────────┤
│   Application Service Layer      │  <- 业务逻辑
│  ┌──────────────────────────┐   │
│  │ Strategy Scorer          │   │  评分引擎
│  │ Option Screener          │   │  筛选引擎
│  └──────────────────────────┘   │
├─────────────────────────────────┤
│    Core Domain Layer             │  <- 核心算法
│  ┌──────────────────────────┐   │
│  │ Pricing (Greeks)         │   │  定价和希腊值
│  │ Strategy Definitions     │   │  策略定义
│  │ Data Models              │   │  数据模型
│  └──────────────────────────┘   │
├─────────────────────────────────┤
│    Data Layer                    │  <- 数据源
│  ┌──────────────────────────┐   │
│  │ Mock Provider            │   │  
│  │ Polygon Provider (TODO)  │   │
│  │ QuantConnect Provider    │   │
│  └──────────────────────────┘   │
└─────────────────────────────────┘
```

## 核心类说明

### 1. OptionScreener (品种筛选)

**职责**：根据条件过滤期权合约

```python
screener = OptionScreener()
result = screener.screen_options(option_chain, criteria)
```

**关键方法**：
- `screen_options()` - 执行筛选
- `_apply_filters()` - 应用所有过滤器
- `_sort_options()` - 排序结果

**支持的过滤条件**：
- 成交量、持仓量
- 隐含波动率
- 天数到期
- 行权价距离（Moneyness）
- 期权类型（看涨/看跌）

### 2. StrategyScorer (策略评分)

**职责**：为交易策略打分和排名

```python
scorer = StrategyScorer()
scores = scorer.score_strategies(option_chain)
```

**评分权重**：
- 40% - 盈利概率 (POP)
- 30% - 收益率 (RoR)
- 20% - 流动性 (Volume + OI)
- 10% - 时间衰减 (Theta)

**返回值**：按评分降序排列的 StrategyScore 列表

### 3. 策略类 (IronCondor, BullCallSpread, LongStraddle)

**基类**：`BaseStrategy`

**实现的方法**：

```python
class BaseStrategy:
    def identify_legs(option_chain) -> List[StrategyLeg]
        """识别策略的各条腿"""
    
    def calculate_pnl(legs, underlying_price) -> Tuple[float, float]
        """计算最大利润和最大损失"""
    
    def calculate_probability_of_profit(legs, underlying_price) -> float
        """计算盈利概率"""
```

### 4. BlackScholesCalculator (定价)

**职责**：计算期权理论价格

```python
call_price = BlackScholesCalculator.calculate_call_price(S, K, T, r, sigma)
put_price = BlackScholesCalculator.calculate_put_price(S, K, T, r, sigma)
```

### 5. GreeksCalculator (希腊值)

**职责**：计算期权的 Greeks

```python
greeks = GreeksCalculator.calculate_all_greeks(S, K, T, r, sigma, "call")
# 返回 Greeks 对象，包含 delta, gamma, theta, vega, rho
```

## 如何扩展

### 添加新的筛选条件

1. 在 `models.py` 的 `ScreeningCriteria` 中添加字段
2. 在 `screener.py` 的 `_apply_filters()` 中实现过滤逻辑
3. 在 `api/main.py` 中添加 API 参数

### 添加新的策略

1. 在 `strategies.py` 中创建新类继承 `BaseStrategy`
2. 实现 `identify_legs()`, `calculate_pnl()`, `calculate_probability_of_profit()`
3. 在 `scorer.py` 的 `score_strategies()` 中注册新策略
4. 在 `models.py` 的 `StrategyType` Enum 中添加新策略类型

### 集成新的数据源

1. 在 `data/provider.py` 中创建新类继承 `DataProvider`
2. 实现 `get_option_chain()` 和 `get_historical_data()`
3. 在 `config/settings.py` 中添加配置
4. 在 `api/main.py` 中切换数据提供者

## 测试策略

### 单元测试

```bash
pytest tests/test_screening.py -v
pytest tests/test_strategy.py -v
pytest tests/test_pricing.py -v
```

### 集成测试

```bash
pytest tests/ -v --cov=core
```

### 手动测试 API

```bash
# 启动服务
python -m api.main

# 在另一个终端测试
curl http://localhost:8000/health
```

## 性能优化建议

1. **缓存** - 使用 Redis 缓存期权链数据
2. **批量处理** - 一次性计算多个期权的希腊值
3. **向量化** - 使用 NumPy 向量化计算
4. **异步** - 使用 FastAPI 的异步特性
5. **数据库索引** - 如果使用数据库，建立适当的索引

## 常见问题

### Q: 如何切换数据源？
A: 在 `api/main.py` 中修改数据提供者的实例化方式。

### Q: 如何调整评分权重？
A: 修改 `scorer.py` 中 `_calculate_composite_score()` 方法的权重系数。

### Q: 如何添加新的希腊值？
A: 在 `greeks.py` 中添加新方法，然后在 `Greeks` 数据类中添加字段。

### Q: 可以用于实盘交易吗？
A: 当前版本为演示和教育用途。实盘交易需要额外的风控、订单管理等功能。

## 参考资源

- Black-Scholes 模型：https://en.wikipedia.org/wiki/Black%E2%80%93Scholes_model
- 期权策略：https://www.investopedia.com/terms/o/option-strategies.asp
- QuantLib 文档：https://www.quantlib.org/
- 标准差和波动率：https://www.investopedia.com/terms/v/volatility.asp
