# 股票技术分析数据样例设计方案

## 数据结构设计

### 1. 基础数据结构

#### 1.1 股票基本信息
```json
{
  "symbol": "000001",
  "name": "平安银行",
  "period": "daily",
  "time_range": {
    "start_date": "2024-01-01",
    "end_date": "2024-02-01",
    "days_count": 22
  }
}
```

#### 1.2 K线数据（近期数据）
```json
{
  "kline": [
    {
      "date": "2024-02-01",
      "open": 15.20,
      "high": 15.50,
      "low": 15.10,
      "close": 15.40,
      "volume": 125000000
    },
    {
      "date": "2024-01-31",
      "open": 15.00,
      "high": 15.30,
      "low": 14.90,
      "close": 15.20,
      "volume": 110000000
    }
    // 只包含最近10-15天的数据
  ]
}
```

### 2. 技术指标数据

#### 2.1 移动平均线（MA）
```json
{
  "ma": {
    "periods": [5, 10, 20, 60],
    "data": [
      {
        "date": "2024-02-01",
        "ma5": 15.30,
        "ma10": 15.10,
        "ma20": 14.90,
        "ma60": 14.50,
        "trend": "bullish" // bullish, bearish, sideways
      }
    ],
    "signals": [
      {
        "date": "2024-01-25",
        "type": "golden_cross", // golden_cross, death_cross
        "periods": [5, 10],
        "strength": "strong"
      }
    ]
  }
}
```

#### 2.2 成交量（VOL）
```json
{
  "volume": {
    "data": [
      {
        "date": "2024-02-01",
        "volume": 125000000,
        "avg_volume_20d": 100000000,
        "volume_ratio": 1.25,
        "money_flow": "inflow" // inflow, outflow, neutral
      }
    ],
    "patterns": [
      {
        "date": "2024-01-30",
        "pattern": "volume_spike",
        "description": "成交量突然放大，价格上涨"
      }
    ]
  }
}
```

#### 2.3 MACD指标
```json
{
  "macd": {
    "parameters": {
      "fast_period": 12,
      "slow_period": 26,
      "signal_period": 9
    },
    "data": [
      {
        "date": "2024-02-01",
        "dif": 0.15,
        "dea": 0.10,
        "macd_hist": 0.10,
        "trend": "bullish",
        "momentum": "increasing"
      }
    ],
    "signals": [
      {
        "date": "2024-01-28",
        "type": "macd_cross", // macd_cross, histogram_change
        "direction": "bullish",
        "strength": "medium"
      }
    ]
  }
}
```

#### 2.4 RSI指标
```json
{
  "rsi": {
    "parameters": {
      "period": 14
    },
    "data": [
      {
        "date": "2024-02-01",
        "rsi": 65.5,
        "status": "neutral", // overbought, oversold, neutral
        "情绪": "positive"
      }
    ],
    "signals": [
      {
        "date": "2024-01-20",
        "type": "oversold",
        "value": 30.2,
        "strength": "strong"
      }
    ]
  }
}
```

#### 2.5 KDJ指标
```json
{
  "kdj": {
    "parameters": {
      "period": 9,
      "k_period": 3,
      "d_period": 3
    },
    "data": [
      {
        "date": "2024-02-01",
        "k": 70.5,
        "d": 65.2,
        "j": 81.1,
        "status": "neutral"
      }
    ],
    "signals": [
      {
        "date": "2024-01-25",
        "type": "kd_cross", // kd_cross, j_overbought, j_oversold
        "direction": "bullish",
        "strength": "medium"
      }
    ]
  }
}
```

#### 2.6 布林带（BOLL）
```json
{
  "boll": {
    "parameters": {
      "period": 20,
      "std_dev": 2
    },
    "data": [
      {
        "date": "2024-02-01",
        "upper": 16.00,
        "middle": 15.00,
        "lower": 14.00,
        "close": 15.40,
        "position": "middle", // upper, middle, lower
        "band_width": 0.133,
        "volatility": "medium"
      }
    ],
    "support_resistance": [
      {
        "level": "resistance",
        "price": 16.00,
        "strength": "strong"
      },
      {
        "level": "support",
        "price": 14.00,
        "strength": "strong"
      }
    ]
  }
}
```

### 3. 综合分析数据

#### 3.1 信号汇总
```json
{
  "signals_summary": {
    "bullish_signals": 5,
    "bearish_signals": 2,
    "neutral_signals": 3,
    "dominant_trend": "bullish",
    "signal_strength": "medium"
  }
}
```

#### 3.2 关键点位
```json
{
  "key_levels": {
    "resistance": [16.00, 16.50, 17.00],
    "support": [14.00, 13.50, 13.00],
    "current_position": "靠近阻力位"
  }
}
```

## 完整数据样例

```json
{
  "stock_info": {
    "symbol": "000001",
    "name": "平安银行",
    "period": "daily",
    "time_range": {
      "start_date": "2024-01-15",
      "end_date": "2024-02-01",
      "days_count": 12
    }
  },
  "kline": [
    {
      "date": "2024-02-01",
      "open": 15.20,
      "high": 15.50,
      "low": 15.10,
      "close": 15.40,
      "volume": 125000000
    },
    {
      "date": "2024-01-31",
      "open": 15.00,
      "high": 15.30,
      "low": 14.90,
      "close": 15.20,
      "volume": 110000000
    },
    {
      "date": "2024-01-30",
      "open": 14.80,
      "high": 15.10,
      "low": 14.70,
      "close": 15.00,
      "volume": 130000000
    },
    {
      "date": "2024-01-29",
      "open": 14.60,
      "high": 14.90,
      "low": 14.50,
      "close": 14.80,
      "volume": 95000000
    },
    {
      "date": "2024-01-26",
      "open": 14.40,
      "high": 14.70,
      "low": 14.30,
      "close": 14.60,
      "volume": 85000000
    },
    {
      "date": "2024-01-25",
      "open": 14.20,
      "high": 14.50,
      "low": 14.10,
      "close": 14.40,
      "volume": 100000000
    },
    {
      "date": "2024-01-24",
      "open": 14.00,
      "high": 14.30,
      "low": 13.90,
      "close": 14.20,
      "volume": 90000000
    },
    {
      "date": "2024-01-23",
      "open": 13.80,
      "high": 14.10,
      "low": 13.70,
      "close": 14.00,
      "volume": 80000000
    },
    {
      "date": "2024-01-22",
      "open": 13.60,
      "high": 13.90,
      "low": 13.50,
      "close": 13.80,
      "volume": 75000000
    },
    {
      "date": "2024-01-21",
      "open": 13.40,
      "high": 13.70,
      "low": 13.30,
      "close": 13.60,
      "volume": 70000000
    },
    {
      "date": "2024-01-20",
      "open": 13.20,
      "high": 13.50,
      "low": 13.10,
      "close": 13.40,
      "volume": 65000000
    },
    {
      "date": "2024-01-19",
      "open": 13.00,
      "high": 13.30,
      "low": 12.90,
      "close": 13.20,
      "volume": 60000000
    }
  ],
  "indicators": {
    "ma": {
      "periods": [5, 10, 20, 60],
      "data": [
        {
          "date": "2024-02-01",
          "ma5": 15.00,
          "ma10": 14.50,
          "ma20": 14.00,
          "ma60": 13.50,
          "trend": "bullish"
        }
      ],
      "signals": [
        {
          "date": "2024-01-25",
          "type": "golden_cross",
          "periods": [5, 10],
          "strength": "strong"
        }
      ]
    },
    "volume": {
      "data": [
        {
          "date": "2024-02-01",
          "volume": 125000000,
          "avg_volume_20d": 90000000,
          "volume_ratio": 1.39,
          "money_flow": "inflow"
        }
      ],
      "patterns": [
        {
          "date": "2024-01-30",
          "pattern": "volume_spike",
          "description": "成交量突然放大，价格上涨"
        }
      ]
    },
    "macd": {
      "parameters": {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9
      },
      "data": [
        {
          "date": "2024-02-01",
          "dif": 0.15,
          "dea": 0.10,
          "macd_hist": 0.10,
          "trend": "bullish",
          "momentum": "increasing"
        }
      ],
      "signals": [
        {
          "date": "2024-01-28",
          "type": "macd_cross",
          "direction": "bullish",
          "strength": "medium"
        }
      ]
    },
    "rsi": {
      "parameters": {
        "period": 14
      },
      "data": [
        {
          "date": "2024-02-01",
          "rsi": 65.5,
          "status": "neutral",
          "情绪": "positive"
        }
      ],
      "signals": [
        {
          "date": "2024-01-20",
          "type": "oversold",
          "value": 30.2,
          "strength": "strong"
        }
      ]
    },
    "kdj": {
      "parameters": {
        "period": 9,
        "k_period": 3,
        "d_period": 3
      },
      "data": [
        {
          "date": "2024-02-01",
          "k": 70.5,
          "d": 65.2,
          "j": 81.1,
          "status": "neutral"
        }
      ],
      "signals": [
        {
          "date": "2024-01-25",
          "type": "kd_cross",
          "direction": "bullish",
          "strength": "medium"
        }
      ]
    },
    "boll": {
      "parameters": {
        "period": 20,
        "std_dev": 2
      },
      "data": [
        {
          "date": "2024-02-01",
          "upper": 16.00,
          "middle": 15.00,
          "lower": 14.00,
          "close": 15.40,
          "position": "middle",
          "band_width": 0.133,
          "volatility": "medium"
        }
      ],
      "support_resistance": [
        {
          "level": "resistance",
          "price": 16.00,
          "strength": "strong"
        },
        {
          "level": "support",
          "price": 14.00,
          "strength": "strong"
        }
      ]
    }
  },
  "analysis": {
    "signals_summary": {
      "bullish_signals": 5,
      "bearish_signals": 2,
      "neutral_signals": 3,
      "dominant_trend": "bullish",
      "signal_strength": "medium"
    },
    "key_levels": {
      "resistance": [16.00, 16.50, 17.00],
      "support": [14.00, 13.50, 13.00],
      "current_position": "靠近阻力位"
    }
  }
}
```

## 数据处理建议

### 1. 数据压缩策略
- **时间窗口限制**：只保留最近15-20天的详细数据
- **指标聚合**：将技术指标的信号和趋势特征提取出来
- **关键信息保留**：重点保留信号点和转折点数据

### 2. AI分析优化
- **结构化提示**：使用模板化的提示词，引导AI关注关键指标
- **分层分析**：先分析趋势，再分析信号，最后综合评估
- **指标权重**：根据不同指标的可靠性和时效性设置权重

### 3. 与前端协作
- **标准化接口**：提供统一的JSON格式数据接口
- **增量更新**：只传输变化的数据部分
- **缓存机制**：缓存分析结果，避免重复计算

## 技术实现要点

1. **数据获取**：使用AKShare或其他数据源获取股票数据
2. **指标计算**：使用TA-Lib或自定义函数计算技术指标
3. **数据处理**：实现数据采样、特征提取和信号识别
4. **AI集成**：设计合理的提示词和数据格式，调用AI生成分析
5. **接口设计**：提供RESTful API，支持前端调用

此数据结构设计考虑了token使用优化，只包含必要的近期数据和关键信息，同时保留了所有技术指标的核心分析价值。