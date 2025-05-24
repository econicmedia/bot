"""
Unit tests for technical indicators

Tests all technical indicators for correctness, edge cases, and performance.
"""

import pytest
from datetime import datetime, timedelta
from typing import List
import numpy as np

from src.core.data_manager import Candle
from src.analysis.indicators import (
    MovingAverageIndicator,
    RSIIndicator,
    MACDIndicator,
    BollingerBandsIndicator,
    StochasticIndicator,
    WilliamsRIndicator,
    CCIIndicator,
    ATRIndicator,
    IndicatorResult,
    IndicatorType
)


class TestIndicatorHelpers:
    """Helper methods for testing indicators"""
    
    @staticmethod
    def create_test_candles(count: int = 50, base_price: float = 100.0) -> List[Candle]:
        """Create test candle data with realistic price movements"""
        candles = []
        current_price = base_price
        
        for i in range(count):
            # Simulate price movement with some randomness
            change_pct = np.random.normal(0, 0.02)  # 2% volatility
            new_price = current_price * (1 + change_pct)
            
            # Create OHLC with realistic relationships
            open_price = current_price
            close_price = new_price
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.005)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.005)))
            
            candle = Candle(
                symbol="TESTUSDT",
                timeframe="1m",
                timestamp=datetime.utcnow() + timedelta(minutes=i),
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=1000.0 + np.random.normal(0, 100)
            )
            
            candles.append(candle)
            current_price = new_price
        
        return candles
    
    @staticmethod
    def create_trending_candles(count: int = 50, trend: str = "up") -> List[Candle]:
        """Create candles with a specific trend"""
        candles = []
        base_price = 100.0
        
        for i in range(count):
            if trend == "up":
                price_change = 0.01 + np.random.normal(0, 0.005)  # Upward trend
            elif trend == "down":
                price_change = -0.01 + np.random.normal(0, 0.005)  # Downward trend
            else:
                price_change = np.random.normal(0, 0.005)  # Sideways
            
            new_price = base_price * (1 + price_change)
            
            candle = Candle(
                symbol="TESTUSDT",
                timeframe="1m",
                timestamp=datetime.utcnow() + timedelta(minutes=i),
                open_price=base_price,
                high_price=max(base_price, new_price) * 1.005,
                low_price=min(base_price, new_price) * 0.995,
                close_price=new_price,
                volume=1000.0
            )
            
            candles.append(candle)
            base_price = new_price
        
        return candles


class TestMovingAverageIndicator:
    """Test MovingAverageIndicator"""
    
    def test_sma_calculation(self):
        """Test Simple Moving Average calculation"""
        indicator = MovingAverageIndicator(period=5, ma_type="sma")
        candles = TestIndicatorHelpers.create_test_candles(10)
        
        # Test with insufficient data
        result = indicator.calculate(candles[:3])
        assert result is None
        
        # Test with sufficient data
        result = indicator.calculate(candles[:5])
        assert result is not None
        assert isinstance(result.value, float)
        
        # Verify SMA calculation
        expected_sma = sum(c.close for c in candles[:5]) / 5
        assert abs(result.value - expected_sma) < 0.001
    
    def test_ema_calculation(self):
        """Test Exponential Moving Average calculation"""
        indicator = MovingAverageIndicator(period=5, ma_type="ema")
        candles = TestIndicatorHelpers.create_test_candles(10)
        
        # Update with candles one by one
        results = []
        for candle in candles:
            result = indicator.update(candle)
            if result:
                results.append(result)
        
        assert len(results) > 0
        assert all(isinstance(r.value, float) for r in results)
    
    def test_signal_generation(self):
        """Test signal generation"""
        indicator = MovingAverageIndicator(period=5, ma_type="sma")
        
        # Create trending up candles
        up_candles = TestIndicatorHelpers.create_trending_candles(20, "up")
        
        for candle in up_candles:
            result = indicator.update(candle)
            if result and len(indicator.results) > 1:
                # In uptrend, should generate buy signals
                assert result.signal in ["buy", "hold"]
    
    def test_crossover_detection(self):
        """Test MA crossover detection"""
        fast_ma = MovingAverageIndicator(period=5, ma_type="sma")
        slow_ma = MovingAverageIndicator(period=10, ma_type="sma")
        
        candles = TestIndicatorHelpers.create_test_candles(30)
        
        for candle in candles:
            fast_ma.update(candle)
            slow_ma.update(candle)
        
        # Test crossover detection
        cross_signal = fast_ma.get_ma_cross_signals(slow_ma)
        assert cross_signal in ["golden_cross", "death_cross", None]


class TestRSIIndicator:
    """Test RSIIndicator"""
    
    def test_rsi_calculation(self):
        """Test RSI calculation"""
        indicator = RSIIndicator(period=14)
        candles = TestIndicatorHelpers.create_test_candles(30)
        
        result = indicator.calculate(candles)
        assert result is not None
        assert 0 <= result.value <= 100
    
    def test_rsi_signals(self):
        """Test RSI signal generation"""
        indicator = RSIIndicator(period=14, overbought=70, oversold=30)
        
        # Create overbought scenario (strong uptrend)
        up_candles = TestIndicatorHelpers.create_trending_candles(30, "up")
        
        for candle in up_candles:
            result = indicator.update(candle)
            if result and result.value >= 70:
                assert result.signal == "sell"
    
    def test_rsi_edge_cases(self):
        """Test RSI edge cases"""
        indicator = RSIIndicator(period=5)
        
        # Test with identical prices (should handle division by zero)
        candles = []
        for i in range(10):
            candle = Candle(
                symbol="TEST",
                timeframe="1m",
                timestamp=datetime.utcnow() + timedelta(minutes=i),
                open_price=100.0,
                high_price=100.0,
                low_price=100.0,
                close_price=100.0,
                volume=1000.0
            )
            candles.append(candle)
        
        result = indicator.calculate(candles)
        assert result is not None
        # RSI should be 100 when there are only gains (or 0 when only losses)


class TestMACDIndicator:
    """Test MACDIndicator"""
    
    def test_macd_calculation(self):
        """Test MACD calculation"""
        indicator = MACDIndicator(fast_period=12, slow_period=26, signal_period=9)
        candles = TestIndicatorHelpers.create_test_candles(50)
        
        result = indicator.calculate(candles)
        assert result is not None
        assert isinstance(result.value, dict)
        assert "macd" in result.value
        assert "signal" in result.value
        assert "histogram" in result.value
    
    def test_macd_signals(self):
        """Test MACD signal generation"""
        indicator = MACDIndicator()
        candles = TestIndicatorHelpers.create_trending_candles(50, "up")
        
        signals = []
        for candle in candles:
            result = indicator.update(candle)
            if result and result.signal:
                signals.append(result.signal)
        
        # Should generate some signals in trending market
        assert len(signals) > 0


class TestBollingerBandsIndicator:
    """Test BollingerBandsIndicator"""
    
    def test_bollinger_bands_calculation(self):
        """Test Bollinger Bands calculation"""
        indicator = BollingerBandsIndicator(period=20, std_dev=2.0)
        candles = TestIndicatorHelpers.create_test_candles(30)
        
        result = indicator.calculate(candles)
        assert result is not None
        assert isinstance(result.value, dict)
        
        bands = result.value
        assert "upper" in bands
        assert "middle" in bands
        assert "lower" in bands
        assert "width" in bands
        assert "percent_b" in bands
        
        # Upper band should be above middle, middle above lower
        assert bands["upper"] > bands["middle"] > bands["lower"]
    
    def test_bollinger_signals(self):
        """Test Bollinger Bands signal generation"""
        indicator = BollingerBandsIndicator(period=10, std_dev=2.0)
        candles = TestIndicatorHelpers.create_test_candles(30)
        
        for candle in candles:
            result = indicator.update(candle)
            if result:
                # Signals should be valid
                assert result.signal in ["buy", "sell", "hold"]


class TestStochasticIndicator:
    """Test StochasticIndicator"""
    
    def test_stochastic_calculation(self):
        """Test Stochastic calculation"""
        indicator = StochasticIndicator(k_period=14, d_period=3)
        candles = TestIndicatorHelpers.create_test_candles(30)
        
        result = indicator.calculate(candles)
        assert result is not None
        assert isinstance(result.value, dict)
        assert "k" in result.value
        
        # %K should be between 0 and 100
        assert 0 <= result.value["k"] <= 100


class TestATRIndicator:
    """Test ATRIndicator"""
    
    def test_atr_calculation(self):
        """Test ATR calculation"""
        indicator = ATRIndicator(period=14)
        candles = TestIndicatorHelpers.create_test_candles(30)
        
        result = indicator.calculate(candles)
        assert result is not None
        assert isinstance(result.value, float)
        assert result.value >= 0  # ATR should always be positive
    
    def test_atr_volatility_detection(self):
        """Test ATR volatility level detection"""
        indicator = ATRIndicator(period=10)
        
        # Create high volatility candles
        volatile_candles = []
        for i in range(25):
            # High volatility with large price swings
            change = np.random.normal(0, 0.05)  # 5% volatility
            base_price = 100 * (1 + change)
            
            candle = Candle(
                symbol="TEST",
                timeframe="1m",
                timestamp=datetime.utcnow() + timedelta(minutes=i),
                open_price=base_price,
                high_price=base_price * 1.03,
                low_price=base_price * 0.97,
                close_price=base_price * (1 + np.random.normal(0, 0.01)),
                volume=1000.0
            )
            volatile_candles.append(candle)
        
        for candle in volatile_candles:
            indicator.update(candle)
        
        volatility_level = indicator.get_volatility_level()
        assert volatility_level in ["low", "medium", "high", None]


class TestIndicatorIntegration:
    """Test indicator integration and edge cases"""
    
    def test_indicator_reset(self):
        """Test indicator reset functionality"""
        indicator = MovingAverageIndicator(period=5)
        candles = TestIndicatorHelpers.create_test_candles(10)
        
        # Update with data
        for candle in candles:
            indicator.update(candle)
        
        assert len(indicator.candles) > 0
        assert len(indicator.results) > 0
        
        # Reset
        indicator.reset()
        assert len(indicator.candles) == 0
        assert len(indicator.results) == 0
    
    def test_indicator_serialization(self):
        """Test indicator to_dict method"""
        indicator = RSIIndicator(period=14)
        candles = TestIndicatorHelpers.create_test_candles(20)
        
        for candle in candles:
            indicator.update(candle)
        
        indicator_dict = indicator.to_dict()
        assert isinstance(indicator_dict, dict)
        assert "name" in indicator_dict
        assert "type" in indicator_dict
        assert "period" in indicator_dict
        assert "is_ready" in indicator_dict
    
    def test_multiple_indicators_together(self):
        """Test using multiple indicators together"""
        ma_indicator = MovingAverageIndicator(period=10)
        rsi_indicator = RSIIndicator(period=14)
        macd_indicator = MACDIndicator()
        
        candles = TestIndicatorHelpers.create_test_candles(50)
        
        for candle in candles:
            ma_result = ma_indicator.update(candle)
            rsi_result = rsi_indicator.update(candle)
            macd_result = macd_indicator.update(candle)
            
            # All indicators should work independently
            if ma_result:
                assert isinstance(ma_result.value, float)
            if rsi_result:
                assert 0 <= rsi_result.value <= 100
            if macd_result:
                assert isinstance(macd_result.value, dict)


if __name__ == "__main__":
    pytest.main([__file__])
