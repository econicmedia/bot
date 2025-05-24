# Technical Analysis Engine Documentation

## Overview

The Technical Analysis Engine is a comprehensive module that provides advanced market analysis capabilities for the AI Trading Bot. It includes a wide range of technical indicators, pattern recognition algorithms, and integrated analysis tools.

## Architecture

### Core Components

```
src/analysis/
├── __init__.py                 # Main module exports
├── indicators/                 # Technical indicators
│   ├── __init__.py
│   ├── base.py                # Base indicator classes
│   ├── moving_averages.py     # MA indicators (SMA, EMA, WMA, HMA)
│   ├── oscillators.py         # RSI, Stochastic, Williams %R
│   ├── momentum.py            # MACD, CCI
│   └── volatility.py          # Bollinger Bands, ATR
└── patterns/                  # Pattern recognition
    ├── __init__.py
    ├── base.py               # Base pattern classes
    ├── candlestick.py        # Candlestick patterns
    └── chart_patterns.py     # Chart patterns
```

## Technical Indicators

### Base Framework

All indicators inherit from `IndicatorBase` which provides:
- Consistent interface across all indicators
- Automatic data management and history tracking
- Signal generation and confidence scoring
- Multi-timeframe support
- Performance optimization

### Available Indicators

#### Moving Averages (`MovingAverageIndicator`)
- **Simple Moving Average (SMA)**: Arithmetic mean of prices
- **Exponential Moving Average (EMA)**: Weighted average favoring recent prices
- **Weighted Moving Average (WMA)**: Linear weighted average
- **Hull Moving Average (HMA)**: Reduced lag moving average

**Usage:**
```python
from src.analysis.indicators import MovingAverageIndicator

# Create 20-period SMA
sma = MovingAverageIndicator(period=20, ma_type="sma")

# Update with candle data
result = sma.update(candle)
if result:
    print(f"SMA Value: {result.value}")
    print(f"Signal: {result.signal}")
    print(f"Confidence: {result.confidence}")
```

#### RSI Oscillator (`RSIIndicator`)
- Measures momentum with overbought/oversold levels
- Default: 14-period, overbought=70, oversold=30
- Uses Wilder's smoothing method

#### MACD (`MACDIndicator`)
- Moving Average Convergence Divergence
- Default: 12/26/9 periods (fast/slow/signal)
- Provides MACD line, signal line, and histogram

#### Bollinger Bands (`BollingerBandsIndicator`)
- Volatility bands around moving average
- Default: 20-period, 2 standard deviations
- Provides upper/middle/lower bands and %B

#### Stochastic Oscillator (`StochasticIndicator`)
- %K and %D momentum oscillator
- Default: 14/3 periods, overbought=80, oversold=20

#### Williams %R (`WilliamsRIndicator`)
- Momentum oscillator similar to Stochastic
- Default: 14-period, overbought=-20, oversold=-80

#### Commodity Channel Index (`CCIIndicator`)
- Momentum indicator measuring deviation from average
- Default: 20-period, overbought=100, oversold=-100

#### Average True Range (`ATRIndicator`)
- Volatility indicator measuring price range
- Default: 14-period with EMA smoothing
- Provides volatility level classification

## Pattern Recognition

### Candlestick Patterns (`CandlestickPatterns`)

#### Single Candlestick Patterns
- **Doji**: Indecision pattern with small body
- **Hammer**: Bullish reversal with long lower shadow
- **Shooting Star**: Bearish reversal with long upper shadow
- **Spinning Top**: Indecision with long shadows both sides

#### Multi-Candlestick Patterns
- **Bullish/Bearish Engulfing**: Large candle engulfs previous
- **Bullish/Bearish Harami**: Small candle inside previous large candle

**Usage:**
```python
from src.analysis.patterns import CandlestickPatterns

# Create pattern detector
detector = CandlestickPatterns(timeframe="1h")

# Update with candle data
patterns = detector.update(candle)
for pattern in patterns:
    print(f"Pattern: {pattern.pattern_name}")
    print(f"Signal: {pattern.signal.value}")
    print(f"Confidence: {pattern.confidence}")
```

### Chart Patterns (`ChartPatterns`)

#### Support and Resistance
- Automatic detection of key price levels
- Minimum touch requirements for validation
- Confidence scoring based on number of touches

#### Triangle Patterns
- **Ascending Triangle**: Flat resistance, rising support
- **Descending Triangle**: Flat support, falling resistance  
- **Symmetrical Triangle**: Converging support and resistance

## Integration with Trading Strategy

### Technical Analysis Strategy

The `TechnicalAnalysisStrategy` demonstrates how to combine multiple indicators and patterns:

```python
from src.strategies.technical_analysis_strategy import TechnicalAnalysisStrategy

# Create strategy
strategy = TechnicalAnalysisStrategy("TechAnalysis", settings)

# The strategy automatically:
# 1. Updates all indicators with new candle data
# 2. Detects patterns in real-time
# 3. Combines signals for comprehensive analysis
# 4. Generates trading signals with confidence scores
```

### Signal Generation Process

1. **Data Input**: New candle data received
2. **Indicator Updates**: All indicators process the new data
3. **Pattern Detection**: Pattern recognition algorithms analyze recent candles
4. **Signal Aggregation**: Combine signals from multiple sources
5. **Confidence Calculation**: Score based on signal strength and agreement
6. **Position Sizing**: Adjust based on volatility (ATR) and confidence
7. **Signal Output**: Generate final trading recommendation

### Signal Combination Logic

The strategy requires multiple confirming signals:
- Minimum 2 indicators must agree for signal generation
- Pattern recognition provides additional confirmation
- Volatility (ATR) influences position sizing
- Recent signal history prevents over-trading

## Performance Features

### Optimization
- Efficient data structures (deques for rolling windows)
- Minimal memory footprint with configurable history limits
- Vectorized calculations using NumPy where possible
- Lazy evaluation for expensive calculations

### Reliability
- Comprehensive input validation
- Graceful handling of edge cases (division by zero, insufficient data)
- Robust error handling with detailed logging
- Consistent interfaces across all components

### Extensibility
- Base classes for easy addition of new indicators
- Plugin architecture for custom patterns
- Configurable parameters for all components
- Support for multiple timeframes

## Testing

### Unit Tests
Comprehensive test suite covering:
- Individual indicator calculations
- Pattern detection accuracy
- Edge case handling
- Performance benchmarks

### Integration Tests
- Multi-indicator signal generation
- Strategy performance validation
- Real-time data processing
- Memory usage monitoring

## Usage Examples

### Basic Indicator Usage
```python
# Create and use RSI indicator
rsi = RSIIndicator(period=14)
for candle in candles:
    result = rsi.update(candle)
    if result:
        if result.value > 70:
            print("Overbought condition")
        elif result.value < 30:
            print("Oversold condition")
```

### Multi-Indicator Analysis
```python
# Combine multiple indicators
indicators = {
    "sma": MovingAverageIndicator(period=20),
    "rsi": RSIIndicator(period=14),
    "bb": BollingerBandsIndicator(period=20)
}

for candle in candles:
    signals = []
    for name, indicator in indicators.items():
        result = indicator.update(candle)
        if result and result.signal != "hold":
            signals.append(f"{name}: {result.signal}")
    
    if len(signals) >= 2:  # Multiple confirmations
        print(f"Strong signal: {signals}")
```

### Pattern Recognition
```python
# Detect candlestick patterns
patterns = CandlestickPatterns()
for candle in candles:
    detected = patterns.update(candle)
    for pattern in detected:
        if pattern.confidence > 0.7:
            print(f"High confidence {pattern.pattern_name}: {pattern.signal.value}")
```

## Configuration

### Indicator Parameters
All indicators support customizable parameters:
- Period lengths
- Threshold values (overbought/oversold)
- Smoothing methods
- Price types (close, hl2, hlc3, etc.)

### Pattern Detection Settings
- Minimum confidence thresholds
- Pattern validation criteria
- Historical lookback periods
- Signal filtering options

## Future Enhancements

### Planned Features
- Additional candlestick patterns (Three White Soldiers, etc.)
- Advanced chart patterns (Head & Shoulders, Flags, Pennants)
- Volume-based indicators (OBV, Volume Profile)
- Custom indicator builder interface
- Machine learning pattern recognition
- Multi-timeframe analysis framework

### Performance Improvements
- GPU acceleration for complex calculations
- Parallel processing for multiple symbols
- Advanced caching strategies
- Real-time streaming optimizations

## Conclusion

The Technical Analysis Engine provides a robust foundation for sophisticated market analysis. Its modular design, comprehensive indicator library, and pattern recognition capabilities make it suitable for both simple and complex trading strategies. The consistent interfaces and extensive documentation ensure easy integration and maintenance.
