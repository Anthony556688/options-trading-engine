# Options Trading Engine

一个高性能的期权交易算法库，包含品种筛选、策略评分和风险管理模块。

## 功能特性

### 1. 品种筛选模块 (Screening)
- ✅ 多条件过滤（成交量、持仓量、IV、DTE等）
- ✅ 行权价距离（Moneyness）筛选
- ✅ 灵活的排序选项
- ✅ 支持看涨/看跌期权分离

### 2. 策略评分模块 (Strategy Scoring)
**三核心策略实现：**
- ✅ **Iron Condor** - 中性策略，高胜率
- ✅ **Bull Call Spread** - 看涨策略
- ✅ **Long Straddle** - 波动率策略

**评分指标：**
- 盈利概率 (Probability of Profit, POP)
- 收益率 (Return on Risk, RoR)
- 最大利润/损失
- 损益平衡点
- 综合评分 (0-100)

### 3. 期权定价模块 (Pricing)
- ✅ Black-Scholes 定价模型
- ✅ 四大希腊值计算 (Delta, Gamma, Theta, Vega, Rho)
- ✅ 隐含波动率计算

### 4. REST API 接口
- ✅ `/api/v1/screening` - 期权筛选
- ✅ `/api/v1/strategies` - 策略推荐
- ✅ `/health` - 健康检查
- ✅ Swagger 文档支��

## 项目结构

```
options-trading-engine/
├── core/
│   ├── __init__.py
│   ├── models.py              # 数据模型
│   ├── pricing/
│   │   ├── __init__.py
│   │   ├── black_scholes.py   # Black-Scholes 定价
│   │   └── greeks.py          # 希腊值计算
│   ├── screening/
│   │   ├── __init__.py
│   │   └── screener.py        # 筛选引擎
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── strategies.py      # 三个核心策略
│   │   └── scorer.py          # 策略评分引擎
│   └── data/
│       ├── __init__.py
│       └── provider.py        # 数据提供者
├── api/
│   ├── __init__.py
│   └── main.py                # FastAPI 应用
├── config/
│   ├── __init__.py
│   └── settings.py            # 配置文件
├── tests/
│   ├── __init__.py
│   ├── test_screening.py      # 筛选测试
│   ├── test_strategy.py       # 策略测试
│   └── test_pricing.py        # 定价测试
├── requirements.txt           # 依赖列表
├── .env.example              # 环境变量示例
└── README.md                 # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入您的 Polygon API 密钥
```

### 3. 运行 API 服务

```bash
python -m api.main
```

访问 http://localhost:8000/docs 查看 Swagger 文档

### 4. 运行测试

```bash
pytest tests/ -v
pytest tests/ --cov=core  # 查看覆盖率
```

## API 使用示例

### 筛选期权

```bash
curl -X POST "http://localhost:8000/api/v1/screening" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "min_volume": 100,
    "min_open_interest": 50,
    "min_dte": 7,
    "max_dte": 60
  }'
```

### 获取策略推荐

```bash
curl -X POST "http://localhost:8000/api/v1/strategies" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "strategies": ["iron_condor", "bull_call_spread", "long_straddle"]
  }'
```

## 核心算法详解

### Iron Condor（铁鹰策略）
```
结构：
  - 卖出 OTM Call Spread（1 short call + 1 long call）
  - 卖出 OTM Put Spread（1 short put + 1 long put）n
适用：中性行情，期权IV偏高
优点：高胜率、时间衰减有利
风险：IV 回落、大幅波动
```

### Bull Call Spread（牛市看涨价差）
```
结构：
  - 买入 ATM Call
  - 卖出 OTM Call

适用：温和看涨行情
优点：降低成本、风险有限
风险：收益有限
```

### Long Straddle（长跨式）
```
结构：
  - 买入 ATM Call
  - 买入 ATM Put（同行权价）

适用：预期大幅波动
优点：双向获利、IV 扩张受益
风险：时间衰减、IV 萎缩
```

## 数据模型

### OptionData
```python
@dataclass
class OptionData:
    symbol: str
    strike: float
    expiration_date: datetime
    option_type: OptionType  # CALL 或 PUT
    current_price: float
    bid: float
    ask: float
    volume: int
    open_interest: int
    implied_volatility: float
    underlying_price: float
    greeks: Optional[Greeks]
```

### StrategyScore
```python
@dataclass
class StrategyScore:
    strategy_type: StrategyType
    symbol: str
    score: float  # 0-100
    probability_of_profit: float
    return_on_risk: float
    max_profit: float
    max_loss: float
    breakeven_points: List[float]
    legs: List[StrategyLeg]
```

## 配置说明

在 `config/settings.py` 中配置：

```python
# 筛选条件
SCREENING_CONFIG = {
    "min_volume": 100,
    "min_open_interest": 50,
    "iv_percentile_range": (10, 90),
    "default_dte_range": (7, 60),
}

# 策略参数
STRATEGY_CONFIG = {
    "iron_condor": {
        "min_probability": 0.50,
        "min_return_on_risk": 0.10,
    },
    "bull_call_spread": {
        "min_probability": 0.55,
        "min_return_on_risk": 0.15,
    },
    "long_straddle": {
        "min_probability": 0.45,
        "min_return_on_risk": 0.20,
    },
}
```

## 下一步开发

### Phase 2（增强功能）
- [ ] 集成 Polygon.io API 获取实时数据
- [ ] 添加 Bollinger Band、RSI 等技术指标
- [ ] 实现回测引擎
- [ ] 资金流异常检测
- [ ] WebSocket 实时推送

### Phase 3（企业级功能）
- [ ] 数据库持久化（PostgreSQL）
- [ ] Redis 缓存
- [ ] 用户认证和权限管理
- [ ] 投资组合 PnL 计算
- [ ] 风险监控告警
- [ ] 前端仪表板（React）

## 贡献指南

欢迎提交 PR 和 Issue！

## 许可证

MIT License

## 联系方式

有问题？在 GitHub Issues 中提交或发送邮件。
