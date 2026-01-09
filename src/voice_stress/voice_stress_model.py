"""
Voice Stress Model - Main Integration Module
Integrates all components for real-time voice stress detection
"""

import numpy as np
import time
from typing import Dict, Optional, List
from collections import deque

from .audio_handler import AudioHandler
from .feature_extractor import VoiceFeatureExtractor
from .stress_calculator import StressIndexCalculator
from .config import (
    SAMPLE_RATE, MIN_AUDIO_DURATION, 
    TARGET_LATENCY_MS, HIGH_STRESS_THRESHOLD
)


class VoiceStressModel:
    """
    Main voice stress detection model
    Provides real-time stress analysis from audio input
    """
    
    def __init__(self, 
                 sample_rate: int = SAMPLE_RATE,
                 history_length: int = 10):
        """
        Initialize voice stress model
        
        Args:
            sample_rate: Audio sampling rate
            history_length: Number of recent stress scores to keep for trend analysis
        """
        self.sample_rate = sample_rate
        self.history_length = history_length
        
        # Initialize components
        self.audio_handler = AudioHandler(sample_rate=sample_rate)
        self.feature_extractor = VoiceFeatureExtractor(sample_rate=sample_rate)
        self.stress_calculator = StressIndexCalculator()
        
        # Stress history for temporal analysis
        self.stress_history = deque(maxlen=history_length)
        
        # Performance metrics
        self.inference_times = deque(maxlen=20)
        
        print("Voice Stress Model initialized")
    
    def process_audio(self, audio_data: np.ndarray, 
                     preprocess: bool = True) -> Dict:
        """
        Process audio and return stress analysis
        
        Args:
            audio_data: Raw audio samples
            preprocess: Whether to preprocess audio
            
        Returns:
            Dictionary with stress analysis results
        """
        start_time = time.time()
        
        try:
            # Preprocess audio if needed
            if preprocess:
                processed_audio = self.audio_handler.preprocess_audio(
                    audio_data,
                    apply_noise_reduction=True,
                    apply_lowpass=True
                )
            else:
                processed_audio = audio_data
            
            # Extract features
            features = self.feature_extractor.extract_all_features(processed_audio)
            
            # Calculate stress index
            stress_index = self.stress_calculator.calculate_stress_index(features)
            
            # Update history
            self.stress_history.append(stress_index)
            
            # Get detailed analysis
            analysis = self.stress_calculator.get_detailed_analysis(features, stress_index)
            
            # Add temporal trend if enough history
            if len(self.stress_history) > 1:
                trend = self.stress_calculator.calculate_temporal_trend(
                    list(self.stress_history)
                )
                analysis['temporal_trend'] = trend
            
            # Calculate inference time
            inference_time = (time.time() - start_time) * 1000  # Convert to ms
            self.inference_times.append(inference_time)
            
            # Add performance metrics
            analysis['performance'] = {
                'inference_time_ms': round(inference_time, 2),
                'avg_inference_time_ms': round(np.mean(self.inference_times), 2),
                'target_latency_ms': TARGET_LATENCY_MS,
                'meets_target': inference_time < TARGET_LATENCY_MS
            }
            
            # Add timestamp
            analysis['timestamp'] = time.time()
            
            return analysis
            
        except Exception as e:
            print(f"Error processing audio: {e}")
            return {
                'error': str(e),
                'stress_index': 0.0,
                'stress_level': 'ERROR'
            }
    
    def analyze_file(self, file_path: str) -> Dict:
        """
        Analyze audio file and return stress analysis
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Stress analysis results
        """
        print(f"Analyzing audio file: {file_path}")
        
        # Load audio file
        audio_data, sr = self.audio_handler.load_audio_file(file_path)
        
        # Process audio
        result = self.process_audio(audio_data, preprocess=True)
        
        return result
    
    def start_realtime_analysis(self, 
                               callback: Optional[callable] = None,
                               duration_seconds: Optional[float] = None):
        """
        Start real-time audio analysis from microphone
        
        Args:
            callback: Function to call with each analysis result
            duration_seconds: How long to run (None = until stopped)
        """
        print("Starting real-time voice stress analysis...")
        print("Speak into your microphone. Press Ctrl+C to stop.")
        
        # Start audio stream
        self.audio_handler.start_stream()
        
        start_time = time.time()
        
        try:
            while True:
                # Check duration limit
                if duration_seconds and (time.time() - start_time) > duration_seconds:
                    break
                
                # Get audio chunk
                audio_chunk = self.audio_handler.get_audio_chunk(
                    duration=MIN_AUDIO_DURATION
                )
                
                if audio_chunk is not None and len(audio_chunk) > 0:
                    # Process audio
                    result = self.process_audio(audio_chunk, preprocess=True)
                    
                    # Call callback if provided
                    if callback:
                        callback(result)
                    else:
                        # Default: print results
                        self._print_result(result)
                
                # Small sleep to prevent overwhelming CPU
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nStopping real-time analysis...")
        finally:
            self.audio_handler.stop_stream()
            print("Real-time analysis stopped")
    
    def _print_result(self, result: Dict):
        """Print formatted analysis result"""
        if 'error' in result:
            print(f"Error: {result['error']}")
            return
        
        stress_index = result['stress_index']
        stress_level = result['stress_level']
        inference_time = result['performance']['inference_time_ms']
        
        # Create visual stress meter
        bar_length = 30
        filled = int((stress_index / 100) * bar_length)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\n{'='*60}")
        print(f"Stress Index: {stress_index:.1f}/100 | Level: {stress_level}")
        print(f"[{bar}]")
        print(f"Inference Time: {inference_time:.1f}ms")
        
        if result.get('temporal_trend'):
            trend = result['temporal_trend']
            print(f"Trend: {trend['trend']} (slope: {trend['slope']:.2f})")
        
        if stress_index >= HIGH_STRESS_THRESHOLD:
            print("⚠️  HIGH STRESS DETECTED!")
        
        print(f"{'='*60}")
    
    def get_stress_summary(self) -> Dict:
        """
        Get summary of stress analysis from history
        
        Returns:
            Summary statistics
        """
        if len(self.stress_history) == 0:
            return {'message': 'No stress data available'}
        
        history = list(self.stress_history)
        
        return {
            'count': len(history),
            'current': round(history[-1], 2),
            'average': round(np.mean(history), 2),
            'min': round(np.min(history), 2),
            'max': round(np.max(history), 2),
            'std': round(np.std(history), 2),
            'trend': self.stress_calculator.calculate_temporal_trend(history),
            'high_stress_events': sum(1 for s in history if s >= HIGH_STRESS_THRESHOLD)
        }
    
    def reset_history(self):
        """Clear stress history"""
        self.stress_history.clear()
        print("Stress history cleared")
    
    def cleanup(self):
        """Clean up resources"""
        self.audio_handler.cleanup()
        print("Voice Stress Model cleaned up")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()


# Convenience function for quick inference
def analyze_voice_stress(audio_input, 
                        input_type: str = 'file',
                        sample_rate: int = SAMPLE_RATE) -> Dict:
    """
    Quick inference function for voice stress analysis
    
    Args:
        audio_input: Path to audio file or numpy array
        input_type: 'file' or 'array'
        sample_rate: Audio sampling rate
        
    Returns:
        Stress analysis results
    """
    model = VoiceStressModel(sample_rate=sample_rate)
    
    try:
        if input_type == 'file':
            result = model.analyze_file(audio_input)
        elif input_type == 'array':
            result = model.process_audio(audio_input, preprocess=True)
        else:
            raise ValueError(f"Invalid input_type: {input_type}")
        
        return result
    finally:
        model.cleanup()
