"""
Stress Index Calculator Module
Converts extracted voice features into a stress index (0-100)
"""

import numpy as np
from typing import Dict
from sklearn.preprocessing import MinMaxScaler

from .config import STRESS_MIN, STRESS_MAX, HIGH_STRESS_THRESHOLD


class StressIndexCalculator:
    """Calculates voice stress index from extracted features"""
    
    def __init__(self):
        """Initialize stress calculator with feature weights and thresholds"""
        
        # Feature weights (determined based on stress indicators research)
        # Higher weight = more important for stress detection
        self.feature_weights = {
            'pitch_variation': 0.15,      # High variation indicates stress
            'jitter': 0.20,                # High jitter = vocal tension
            'speaking_rate': 0.15,         # Faster rate may indicate anxiety
            'energy_variation': 0.15,      # Irregular energy = emotional arousal
            'spectral_centroid_mean': 0.10,  # Higher frequency = tension
            'zero_crossing_rate_mean': 0.10,  # Voice quality indicator
            'rms_std': 0.10,               # Energy variability
            'pitch_range': 0.05            # Pitch range variation
        }
        
        # Expected normal ranges for features (for normalization)
        # These are based on typical human voice characteristics
        self.feature_ranges = {
            'pitch_mean': (100, 300),      # Hz
            'pitch_std': (0, 50),          # Hz
            'pitch_range': (0, 200),       # Hz
            'pitch_variation': (0, 0.5),   # Coefficient of variation
            'jitter': (0, 5),              # Percentage
            'speaking_rate': (0, 10),      # Syllables per second
            'rms_mean': (0, 0.5),          # Normalized
            'rms_std': (0, 0.3),           # Normalized
            'energy_variation': (0, 2),    # Coefficient of variation
            'spectral_centroid_mean': (0, 5000),  # Hz
            'spectral_bandwidth_mean': (0, 4000),  # Hz
            'zero_crossing_rate_mean': (0, 0.5),   # Rate
            'mfcc_mean': (-50, 50)         # MFCC values
        }
        
        # Stress thresholds (feature values indicating stress)
        self.stress_thresholds = {
            'jitter': 2.0,                 # > 2% indicates stress
            'pitch_variation': 0.25,       # > 0.25 indicates stress
            'speaking_rate': 5.0,          # > 5 syllables/sec indicates stress
            'energy_variation': 1.0        # > 1.0 indicates stress
        }
    
    def normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize features to 0-1 range based on expected ranges
        
        Args:
            features: Raw feature values
            
        Returns:
            Normalized feature values
        """
        normalized = {}
        
        for feature_name, value in features.items():
            if feature_name in self.feature_ranges:
                min_val, max_val = self.feature_ranges[feature_name]
                # Normalize to 0-1 range
                normalized_value = (value - min_val) / (max_val - min_val + 1e-6)
                # Clip to 0-1
                normalized[feature_name] = float(np.clip(normalized_value, 0, 1))
            else:
                normalized[feature_name] = value
        
        return normalized
    
    def calculate_stress_index(self, features: Dict[str, float]) -> float:
        """
        Calculate overall stress index from features
        
        Args:
            features: Extracted voice features
            
        Returns:
            Stress index (0-100)
        """
        # Normalize features
        normalized = self.normalize_features(features)
        
        # Calculate weighted stress score
        stress_score = 0.0
        total_weight = 0.0
        
        for feature_name, weight in self.feature_weights.items():
            if feature_name in normalized:
                # Get normalized feature value
                feature_value = normalized[feature_name]
                
                # Check if feature exceeds stress threshold
                if feature_name in self.stress_thresholds:
                    raw_value = features[feature_name]
                    threshold = self.stress_thresholds[feature_name]
                    
                    # Amplify contribution if threshold exceeded
                    if raw_value > threshold:
                        excess_ratio = raw_value / threshold
                        feature_value = min(1.0, feature_value * excess_ratio)
                
                # Add weighted contribution
                stress_score += feature_value * weight
                total_weight += weight
        
        # Normalize to 0-1 range
        if total_weight > 0:
            stress_score = stress_score / total_weight
        
        # Scale to 0-100
        stress_index = stress_score * 100
        
        # Apply smoothing and ensure within bounds
        stress_index = np.clip(stress_index, STRESS_MIN, STRESS_MAX)
        
        return float(stress_index)
    
    def get_stress_level(self, stress_index: float) -> str:
        """
        Get categorical stress level from stress index
        
        Args:
            stress_index: Stress score (0-100)
            
        Returns:
            Stress level category
        """
        if stress_index < 30:
            return "LOW"
        elif stress_index < 50:
            return "MILD"
        elif stress_index < HIGH_STRESS_THRESHOLD:
            return "MODERATE"
        else:
            return "HIGH"
    
    def get_detailed_analysis(self, features: Dict[str, float], 
                             stress_index: float) -> Dict:
        """
        Get detailed stress analysis with feature contributions
        
        Args:
            features: Extracted voice features
            stress_index: Calculated stress index
            
        Returns:
            Detailed analysis dictionary
        """
        normalized = self.normalize_features(features)
        
        # Calculate feature contributions
        contributions = {}
        for feature_name, weight in self.feature_weights.items():
            if feature_name in normalized:
                contribution = normalized[feature_name] * weight * 100
                contributions[feature_name] = round(contribution, 2)
        
        # Identify stress indicators
        stress_indicators = []
        for feature_name, threshold in self.stress_thresholds.items():
            if feature_name in features and features[feature_name] > threshold:
                stress_indicators.append({
                    'feature': feature_name,
                    'value': round(features[feature_name], 2),
                    'threshold': threshold,
                    'severity': 'HIGH' if features[feature_name] > threshold * 1.5 else 'MODERATE'
                })
        
        return {
            'stress_index': round(stress_index, 2),
            'stress_level': self.get_stress_level(stress_index),
            'is_high_stress': stress_index >= HIGH_STRESS_THRESHOLD,
            'feature_contributions': contributions,
            'stress_indicators': stress_indicators,
            'raw_features': {k: round(v, 2) for k, v in features.items()},
            'normalized_features': {k: round(v, 3) for k, v in normalized.items()}
        }
    
    def calculate_temporal_trend(self, stress_history: list) -> Dict:
        """
        Calculate temporal trend from stress index history
        
        Args:
            stress_history: List of recent stress indices
            
        Returns:
            Trend analysis
        """
        if len(stress_history) < 2:
            return {
                'trend': 'INSUFFICIENT_DATA',
                'slope': 0.0,
                'recent_average': stress_history[0] if stress_history else 0.0
            }
        
        # Calculate linear trend
        x = np.arange(len(stress_history))
        y = np.array(stress_history)
        
        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]
        recent_avg = np.mean(stress_history[-5:]) if len(stress_history) >= 5 else np.mean(stress_history)
        
        # Determine trend direction
        if slope > 2:
            trend = 'INCREASING'
        elif slope < -2:
            trend = 'DECREASING'
        else:
            trend = 'STABLE'
        
        return {
            'trend': trend,
            'slope': round(float(slope), 2),
            'recent_average': round(float(recent_avg), 2),
            'min': round(float(np.min(y)), 2),
            'max': round(float(np.max(y)), 2),
            'std': round(float(np.std(y)), 2)
        }
