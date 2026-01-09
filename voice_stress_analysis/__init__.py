"""
Voice Stress Analysis Package

Physiological speech signal analysis for stress detection.
Based on acoustic instability markers, not emotion classification.

Main exports:
- VoiceStressAnalyzer: Primary analyzer class
- analyze_audio_file: Convenience function for file analysis
- analyze_realtime_audio: Convenience function for real-time analysis
"""

from .voice_stress_analyzer import (
    VoiceStressAnalyzer,
    analyze_audio_file,
    analyze_realtime_audio
)

__version__ = "1.0.0"
__author__ = "Yodha26 Team"
__all__ = [
    "VoiceStressAnalyzer",
    "analyze_audio_file",
    "analyze_realtime_audio"
]
