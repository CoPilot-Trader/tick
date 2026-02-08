"""
Fusion Agent - Main agent implementation.

Combines all prediction components into unified trading signals:
- Price Forecast Agent output
- Trend Classification Agent output
- Support/Resistance Agent output
- Sentiment Aggregator output

Developer: Lead Developer
Milestone: M3 - Sentiment & Fusion
Version: 2.0.0
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from core.interfaces.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class FusionAgent(BaseAgent):
    """
    Fusion Agent for combining all predictions into unified trading signals.

    This agent:
    1. Receives signals from all prediction components
    2. Applies weighted combination (configurable)
    3. Applies rule-based logic for edge cases
    4. Generates unified BUY/SELL/HOLD signal with confidence

    Component Weights (default):
    - Price Forecast: 30%
    - Trend Classification: 25%
    - Support/Resistance: 20%
    - Sentiment: 25%

    Developer: Lead Developer
    Milestone: M3 - Sentiment & Fusion
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Fusion Agent."""
        super().__init__(name="fusion_agent", config=config)
        self.version = "2.0.0"

        # Default component weights (configurable)
        self.component_weights = self.config.get("component_weights", {
            "price_forecast": 0.30,
            "trend_classification": 0.25,
            "support_resistance": 0.20,
            "sentiment": 0.25
        })

        # Signal thresholds
        self.buy_threshold = self.config.get("buy_threshold", 0.3)
        self.sell_threshold = self.config.get("sell_threshold", -0.3)

        # Confidence thresholds
        self.min_confidence = self.config.get("min_confidence", 0.4)
        self.high_confidence_threshold = self.config.get("high_confidence_threshold", 0.7)

        # Rule-based adjustments
        self.enable_rule_adjustments = self.config.get("enable_rule_adjustments", True)
        self.support_resistance_proximity = self.config.get("support_resistance_proximity", 0.02)  # 2%

    def initialize(self) -> bool:
        """
        Initialize the Fusion Agent.

        Sets up:
        - Weight validation
        - Rule configuration
        """
        try:
            # Validate weights sum to 1.0
            total_weight = sum(self.component_weights.values())
            if abs(total_weight - 1.0) > 0.01:
                logger.warning(f"Component weights sum to {total_weight}, normalizing...")
                for key in self.component_weights:
                    self.component_weights[key] /= total_weight

            self.initialized = True
            logger.info(f"Fusion Agent v{self.version} initialized with weights: {self.component_weights}")
            return True
        except Exception as e:
            logger.error(f"Error initializing Fusion Agent: {e}", exc_info=True)
            self.initialized = False
            return False

    def process(self, symbol: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate fused trading signal for a given symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            params: Optional parameters:
                   - price_forecast: Output from Price Forecast Agent
                   - trend_classification: Output from Trend Classification Agent
                   - support_resistance: Output from Support/Resistance Agent
                   - sentiment: Output from Sentiment Aggregator
                   - current_price: Current stock price (optional)
                   - time_horizon: Prediction time horizon (e.g., "1d")

        Returns:
            Dictionary with fused trading signal:
            {
                "symbol": str,
                "signal": str,  # BUY, SELL, HOLD
                "confidence": float,
                "components": {...},
                "rules_applied": [...],
                "reasoning": str,
                "fused_at": str,
                "status": str
            }
        """
        if not self.initialized:
            return {
                "symbol": symbol,
                "status": "error",
                "message": "Agent not initialized. Call initialize() first."
            }

        params = params or {}

        # Extract component signals
        price_forecast = params.get("price_forecast", {})
        trend_classification = params.get("trend_classification", {})
        support_resistance = params.get("support_resistance", {})
        sentiment = params.get("sentiment", {})
        current_price = params.get("current_price")
        time_horizon = params.get("time_horizon", "1d")

        try:
            # Step 1: Convert each component to normalized signal (-1 to +1)
            component_signals = self._extract_component_signals(
                price_forecast=price_forecast,
                trend_classification=trend_classification,
                support_resistance=support_resistance,
                sentiment=sentiment,
                current_price=current_price
            )

            # Step 2: Calculate weighted combination
            fused_score, component_contributions = self._weighted_combination(component_signals)

            # Step 3: Apply rule-based adjustments
            rules_applied = []
            if self.enable_rule_adjustments:
                fused_score, rules_applied = self._apply_rules(
                    fused_score=fused_score,
                    component_signals=component_signals,
                    support_resistance=support_resistance,
                    current_price=current_price
                )

            # Step 4: Calculate confidence
            confidence = self._calculate_confidence(
                component_signals=component_signals,
                fused_score=fused_score
            )

            # Step 5: Determine final signal
            signal = self._determine_signal(fused_score, confidence)

            # Step 6: Generate reasoning
            reasoning = self._generate_reasoning(
                signal=signal,
                fused_score=fused_score,
                confidence=confidence,
                component_contributions=component_contributions,
                rules_applied=rules_applied
            )

            return {
                "symbol": symbol,
                "signal": signal,
                "confidence": round(confidence, 4),
                "fused_score": round(fused_score, 4),
                "components": component_contributions,
                "rules_applied": rules_applied,
                "reasoning": reasoning,
                "time_horizon": time_horizon,
                "fused_at": datetime.utcnow().isoformat() + "Z",
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error fusing signals for {symbol}: {e}", exc_info=True)
            return {
                "symbol": symbol,
                "status": "error",
                "message": f"Error fusing signals: {str(e)}",
                "signal": "HOLD",
                "confidence": 0.0,
                "fused_at": datetime.utcnow().isoformat() + "Z"
            }

    def _extract_component_signals(
        self,
        price_forecast: Dict[str, Any],
        trend_classification: Dict[str, Any],
        support_resistance: Dict[str, Any],
        sentiment: Dict[str, Any],
        current_price: Optional[float] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract and normalize signals from each component.

        Returns normalized signals between -1 (strong sell) and +1 (strong buy).
        """
        signals = {}

        # Price Forecast Signal
        if price_forecast and price_forecast.get("status") == "success":
            predicted_price = price_forecast.get("predicted_price")
            price_confidence = price_forecast.get("confidence", 0.5)

            if predicted_price and current_price:
                # Calculate expected return
                expected_return = (predicted_price - current_price) / current_price
                # Normalize to -1 to +1 (±10% return = ±1)
                signal_value = max(-1, min(1, expected_return / 0.10))
            elif price_forecast.get("direction"):
                # Use direction if no prices available
                direction = price_forecast.get("direction", "neutral")
                signal_value = {"up": 0.5, "down": -0.5, "neutral": 0.0}.get(direction, 0.0)
            else:
                signal_value = 0.0
                price_confidence = 0.0

            signals["price_forecast"] = {
                "signal_value": signal_value,
                "confidence": price_confidence,
                "raw": price_forecast
            }
        else:
            signals["price_forecast"] = {
                "signal_value": 0.0,
                "confidence": 0.0,
                "raw": price_forecast
            }

        # Trend Classification Signal
        if trend_classification and trend_classification.get("success"):
            trend_signal = trend_classification.get("signal", "HOLD")
            trend_confidence = trend_classification.get("confidence", 0.5)
            probabilities = trend_classification.get("probabilities", {})

            # Convert to signal value
            if trend_signal == "BUY":
                signal_value = probabilities.get("BUY", 0.7) - probabilities.get("SELL", 0.1)
            elif trend_signal == "SELL":
                signal_value = probabilities.get("BUY", 0.1) - probabilities.get("SELL", 0.7)
            else:  # HOLD
                signal_value = (probabilities.get("BUY", 0.33) - probabilities.get("SELL", 0.33)) * 0.5

            signals["trend_classification"] = {
                "signal_value": max(-1, min(1, signal_value)),
                "confidence": trend_confidence,
                "raw_signal": trend_signal,
                "raw": trend_classification
            }
        else:
            signals["trend_classification"] = {
                "signal_value": 0.0,
                "confidence": 0.0,
                "raw": trend_classification
            }

        # Support/Resistance Signal
        if support_resistance and support_resistance.get("status") == "success":
            sr_confidence = support_resistance.get("confidence", 0.5)
            levels = support_resistance.get("levels", {})

            # Calculate position relative to support/resistance
            if current_price and levels:
                nearest_support = levels.get("nearest_support", {}).get("price", 0)
                nearest_resistance = levels.get("nearest_resistance", {}).get("price", float('inf'))

                if nearest_support and nearest_resistance and nearest_resistance > nearest_support:
                    # Calculate where price is in the range
                    range_size = nearest_resistance - nearest_support
                    position_in_range = (current_price - nearest_support) / range_size

                    # Near support (bullish), near resistance (bearish)
                    # Position 0 = at support, Position 1 = at resistance
                    signal_value = 1.0 - (2.0 * position_in_range)  # +1 at support, -1 at resistance
                else:
                    signal_value = 0.0
            else:
                signal_value = 0.0
                sr_confidence = 0.0

            signals["support_resistance"] = {
                "signal_value": max(-1, min(1, signal_value)),
                "confidence": sr_confidence,
                "raw": support_resistance
            }
        else:
            signals["support_resistance"] = {
                "signal_value": 0.0,
                "confidence": 0.0,
                "raw": support_resistance
            }

        # Sentiment Signal
        if sentiment and sentiment.get("status") == "success":
            aggregated_sentiment = sentiment.get("aggregated_sentiment", 0.0)
            sentiment_confidence = sentiment.get("confidence", 0.5)
            impact = sentiment.get("impact", "Low")

            # Scale sentiment by impact
            impact_multiplier = {"High": 1.0, "Medium": 0.7, "Low": 0.4}.get(impact, 0.5)
            signal_value = aggregated_sentiment * impact_multiplier

            signals["sentiment"] = {
                "signal_value": max(-1, min(1, signal_value)),
                "confidence": sentiment_confidence,
                "impact": impact,
                "raw": sentiment
            }
        else:
            signals["sentiment"] = {
                "signal_value": 0.0,
                "confidence": 0.0,
                "raw": sentiment
            }

        return signals

    def _weighted_combination(
        self,
        component_signals: Dict[str, Dict[str, Any]]
    ) -> tuple:
        """
        Calculate weighted combination of component signals.

        Returns:
            Tuple of (fused_score, component_contributions)
        """
        fused_score = 0.0
        total_weight = 0.0
        contributions = {}

        for component, signal_data in component_signals.items():
            weight = self.component_weights.get(component, 0.0)
            signal_value = signal_data.get("signal_value", 0.0)
            confidence = signal_data.get("confidence", 0.0)

            # Skip components with zero confidence
            if confidence < 0.1:
                contributions[component] = {
                    "weight": weight,
                    "signal_value": signal_value,
                    "confidence": confidence,
                    "contribution": 0.0,
                    "status": "skipped_low_confidence"
                }
                continue

            # Weight by both configured weight and confidence
            effective_weight = weight * confidence
            contribution = signal_value * effective_weight

            fused_score += contribution
            total_weight += effective_weight

            contributions[component] = {
                "weight": weight,
                "signal_value": round(signal_value, 4),
                "confidence": round(confidence, 4),
                "effective_weight": round(effective_weight, 4),
                "contribution": round(contribution, 4),
                "status": "included"
            }

        # Normalize by total effective weight
        if total_weight > 0:
            fused_score = fused_score / total_weight

        return fused_score, contributions

    def _apply_rules(
        self,
        fused_score: float,
        component_signals: Dict[str, Dict[str, Any]],
        support_resistance: Dict[str, Any],
        current_price: Optional[float] = None
    ) -> tuple:
        """
        Apply rule-based adjustments to the fused score.

        Rules:
        1. Near resistance + bearish sentiment → reduce bullish signal
        2. Near support + bullish sentiment → increase bullish signal
        3. Strong component disagreement → reduce confidence
        4. All components agree → boost signal

        Returns:
            Tuple of (adjusted_score, rules_applied)
        """
        rules_applied = []
        adjusted_score = fused_score

        # Rule 1 & 2: Support/Resistance proximity rules
        if current_price and support_resistance and support_resistance.get("levels"):
            levels = support_resistance.get("levels", {})
            nearest_support = levels.get("nearest_support", {}).get("price")
            nearest_resistance = levels.get("nearest_resistance", {}).get("price")
            sentiment_value = component_signals.get("sentiment", {}).get("signal_value", 0.0)

            # Near resistance with bearish sentiment
            if nearest_resistance and current_price:
                distance_to_resistance = (nearest_resistance - current_price) / current_price
                if distance_to_resistance < self.support_resistance_proximity and sentiment_value < -0.2:
                    adjustment = -0.1  # Reduce bullish signal
                    adjusted_score += adjustment
                    rules_applied.append({
                        "rule": "near_resistance_bearish_sentiment",
                        "adjustment": adjustment,
                        "reason": f"Price within {self.support_resistance_proximity*100:.1f}% of resistance with bearish sentiment"
                    })

            # Near support with bullish sentiment
            if nearest_support and current_price:
                distance_to_support = (current_price - nearest_support) / current_price
                if distance_to_support < self.support_resistance_proximity and sentiment_value > 0.2:
                    adjustment = 0.1  # Increase bullish signal
                    adjusted_score += adjustment
                    rules_applied.append({
                        "rule": "near_support_bullish_sentiment",
                        "adjustment": adjustment,
                        "reason": f"Price within {self.support_resistance_proximity*100:.1f}% of support with bullish sentiment"
                    })

        # Rule 3: Strong component agreement
        signal_values = [
            s.get("signal_value", 0.0)
            for s in component_signals.values()
            if s.get("confidence", 0.0) > 0.3
        ]

        if len(signal_values) >= 3:
            # Check if all agree on direction
            all_bullish = all(v > 0.2 for v in signal_values)
            all_bearish = all(v < -0.2 for v in signal_values)

            if all_bullish:
                adjustment = 0.1
                adjusted_score += adjustment
                rules_applied.append({
                    "rule": "strong_bullish_agreement",
                    "adjustment": adjustment,
                    "reason": "Multiple components agree on bullish signal"
                })
            elif all_bearish:
                adjustment = -0.1
                adjusted_score += adjustment
                rules_applied.append({
                    "rule": "strong_bearish_agreement",
                    "adjustment": adjustment,
                    "reason": "Multiple components agree on bearish signal"
                })

        # Clamp to valid range
        adjusted_score = max(-1.0, min(1.0, adjusted_score))

        return adjusted_score, rules_applied

    def _calculate_confidence(
        self,
        component_signals: Dict[str, Dict[str, Any]],
        fused_score: float
    ) -> float:
        """
        Calculate confidence score based on component agreement and signal strength.

        High confidence when:
        - Components agree on direction
        - Individual components have high confidence
        - Signal is strong (far from 0)

        Low confidence when:
        - Components disagree
        - Individual components have low confidence
        - Signal is weak (near 0)
        """
        # Factor 1: Average component confidence (40% weight)
        confidences = [
            s.get("confidence", 0.0)
            for s in component_signals.values()
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Factor 2: Component agreement (40% weight)
        signal_values = [
            s.get("signal_value", 0.0)
            for s in component_signals.values()
            if s.get("confidence", 0.0) > 0.2
        ]

        if len(signal_values) >= 2:
            # Calculate variance in signals
            mean_signal = sum(signal_values) / len(signal_values)
            variance = sum((v - mean_signal) ** 2 for v in signal_values) / len(signal_values)
            # Low variance = high agreement
            agreement_score = max(0, 1.0 - (variance * 2))
        else:
            agreement_score = 0.5  # Neutral if insufficient data

        # Factor 3: Signal strength (20% weight)
        signal_strength = min(abs(fused_score) * 2, 1.0)

        # Combine factors
        confidence = (
            avg_confidence * 0.4 +
            agreement_score * 0.4 +
            signal_strength * 0.2
        )

        return max(0.0, min(1.0, confidence))

    def _determine_signal(self, fused_score: float, confidence: float) -> str:
        """
        Determine final trading signal based on fused score and confidence.

        Returns:
            "BUY", "SELL", or "HOLD"
        """
        # Require minimum confidence for non-HOLD signals
        if confidence < self.min_confidence:
            return "HOLD"

        # Determine signal based on thresholds
        if fused_score >= self.buy_threshold:
            return "BUY"
        elif fused_score <= self.sell_threshold:
            return "SELL"
        else:
            return "HOLD"

    def _generate_reasoning(
        self,
        signal: str,
        fused_score: float,
        confidence: float,
        component_contributions: Dict[str, Any],
        rules_applied: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable reasoning for the signal."""

        # Find dominant contributors
        sorted_components = sorted(
            [(k, v) for k, v in component_contributions.items() if v.get("status") == "included"],
            key=lambda x: abs(x[1].get("contribution", 0)),
            reverse=True
        )

        reasoning_parts = []

        # Signal summary
        if signal == "BUY":
            reasoning_parts.append(f"BUY signal with {confidence*100:.1f}% confidence (score: {fused_score:.3f}).")
        elif signal == "SELL":
            reasoning_parts.append(f"SELL signal with {confidence*100:.1f}% confidence (score: {fused_score:.3f}).")
        else:
            reasoning_parts.append(f"HOLD signal (score: {fused_score:.3f}, confidence: {confidence*100:.1f}%).")

        # Component contributions
        if sorted_components:
            top = sorted_components[0]
            component_name = top[0].replace("_", " ").title()
            contribution = top[1].get("contribution", 0)
            direction = "bullish" if contribution > 0 else "bearish"
            reasoning_parts.append(f"Primary driver: {component_name} ({direction}).")

        # Rules applied
        if rules_applied:
            rule_names = [r.get("rule", "unknown").replace("_", " ") for r in rules_applied]
            reasoning_parts.append(f"Rules applied: {', '.join(rule_names)}.")

        return " ".join(reasoning_parts)

    def fuse_signals(
        self,
        price_forecast: Dict[str, Any],
        trend_classification: Dict[str, Any],
        support_resistance: Dict[str, Any],
        sentiment: Dict[str, Any],
        symbol: str = "UNKNOWN",
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to fuse all component signals.

        Args:
            price_forecast: Price forecast from Price Forecast Agent
            trend_classification: Trend classification from Trend Classification Agent
            support_resistance: Levels from Support/Resistance Agent
            sentiment: Aggregated sentiment from Sentiment Aggregator
            symbol: Stock symbol
            current_price: Current stock price (optional)

        Returns:
            Dictionary with fused signal

        Example:
            result = fusion_agent.fuse_signals(
                price_forecast=price_result,
                trend_classification=trend_result,
                support_resistance=sr_result,
                sentiment=sentiment_result,
                symbol="AAPL",
                current_price=175.50
            )
        """
        return self.process(symbol, params={
            "price_forecast": price_forecast,
            "trend_classification": trend_classification,
            "support_resistance": support_resistance,
            "sentiment": sentiment,
            "current_price": current_price
        })

    def update_weights(self, new_weights: Dict[str, float]) -> bool:
        """
        Update component weights dynamically.

        Args:
            new_weights: Dictionary of component -> weight

        Returns:
            True if successful

        Example:
            fusion_agent.update_weights({
                "price_forecast": 0.35,
                "trend_classification": 0.30,
                "support_resistance": 0.15,
                "sentiment": 0.20
            })
        """
        try:
            # Validate weights sum to 1.0
            total = sum(new_weights.values())
            if abs(total - 1.0) > 0.01:
                # Normalize
                new_weights = {k: v / total for k, v in new_weights.items()}

            self.component_weights.update(new_weights)
            logger.info(f"Updated weights: {self.component_weights}")
            return True
        except Exception as e:
            logger.error(f"Error updating weights: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Check Fusion Agent health."""
        return {
            "status": "healthy" if self.initialized else "not_initialized",
            "agent": self.name,
            "version": self.version,
            "component_weights": self.component_weights,
            "thresholds": {
                "buy": self.buy_threshold,
                "sell": self.sell_threshold,
                "min_confidence": self.min_confidence
            },
            "rule_adjustments_enabled": self.enable_rule_adjustments
        }
