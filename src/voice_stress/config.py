"""
Configuration parameters for Voice Stress Detection
"""

# Audio Processing Parameters
SAMPLE_RATE = 22050  # Standard for librosa
CHUNK_SIZE = 2048  # Audio buffer size
CHANNELS = 1  # Mono audio
AUDIO_FORMAT = 'float32'

# Feature Extraction Parameters
FRAME_LENGTH = 2048  # For STFT
HOP_LENGTH = 512  # For STFT
N_MFCC = 13  # Number of MFCCs
N_FFT = 2048  # FFT window size

# Stress Index Parameters
STRESS_MIN = 0
STRESS_MAX = 100
HIGH_STRESS_THRESHOLD = 70

# Filter Parameters (Low-pass for noise robustness)
LOWPASS_CUTOFF = 4000  # Hz
FILTER_ORDER = 5

# Real-time Processing
TARGET_LATENCY_MS = 500  # Target inference time
MIN_AUDIO_DURATION = 1.0  # Minimum audio duration for analysis (seconds)
