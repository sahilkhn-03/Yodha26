"""
Voice Feature Extractor Module
Extracts stress-related features from audio using librosa
"""

import numpy as np
import librosa
from scipy import signal
from typing import Dict, Tuple

from .config import (
    SAMPLE_RATE, FRAME_LENGTH, HOP_LENGTH,
    N_MFCC, N_FFT
)


class VoiceFeatureExtractor:
    """Extracts voice features related to stress detection"""
    
    def __init__(self, sample_rate: int = SAMPLE_RATE):
        """
        Initialize feature extractor
        
        Args:
            sample_rate: Audio sampling rate (Hz)
        """
        self.sample_rate = sample_rate
        
    def extract_all_features(self, audio_data: np.ndarray) -> Dict[str, float]:
        """
        Extract all stress-related features from audio
        
        Args:
            audio_data: Preprocessed audio samples
            
        Returns:
            Dictionary containing all extracted features
        """
        features = {}
        
        # Extract pitch-related features
        pitch_features = self.extract_pitch_features(audio_data)
        features.update(pitch_features)
        
        # Extract jitter (pitch variation)
        jitter = self.calculate_jitter(audio_data)
        features['jitter'] = jitter
        
        # Extract speaking rate
        speaking_rate = self.estimate_speaking_rate(audio_data)
        features['speaking_rate'] = speaking_rate
        
        # Extract energy envelope
        energy_features = self.extract_energy_features(audio_data)
        features.update(energy_features)
        
        # Extract additional features
        spectral_features = self.extract_spectral_features(audio_data)
        features.update(spectral_features)
        
        return features
    
    def extract_pitch_features(self, audio_data: np.ndarray) -> Dict[str, float]:
        """
        Extract pitch-related features (fundamental frequency)
        
        Args:
            audio_data: Audio samples
            
        Returns:
            Dictionary with pitch features
        """
        # Extract fundamental frequency (F0) using librosa's piptrack
        pitches, magnitudes = librosa.piptrack(
            y=audio_data,
            sr=self.sample_rate,
            fmin=75,  # Minimum frequency (typical human voice)
            fmax=400  # Maximum frequency
        )
        
        # Get pitch values where magnitude is highest
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:  # Valid pitch
                pitch_values.append(pitch)
        
        if len(pitch_values) > 0:
            pitch_array = np.array(pitch_values)
            
            return {
                'pitch_mean': float(np.mean(pitch_array)),
                'pitch_std': float(np.std(pitch_array)),
                'pitch_min': float(np.min(pitch_array)),
                'pitch_max': float(np.max(pitch_array)),
                'pitch_range': float(np.max(pitch_array) - np.min(pitch_array)),
                'pitch_variation': float(np.std(pitch_array) / (np.mean(pitch_array) + 1e-6))
            }
        else:
            return {
                'pitch_mean': 0.0,
                'pitch_std': 0.0,
                'pitch_min': 0.0,
                'pitch_max': 0.0,
                'pitch_range': 0.0,
                'pitch_variation': 0.0
            }
    
    def calculate_jitter(self, audio_data: np.ndarray) -> float:
        """
        Calculate jitter (cycle-to-cycle variation in pitch)
        Higher jitter indicates stress/tension in voice
        
        Args:
            audio_data: Audio samples
            
        Returns:
            Jitter percentage
        """
        # Extract F0 contour
        f0 = librosa.yin(
            audio_data,
            fmin=75,
            fmax=400,
            sr=self.sample_rate
        )
        
        # Remove unvoiced frames (where f0 is very low)
        voiced_f0 = f0[f0 > 75]
        
        if len(voiced_f0) > 1:
            # Calculate period differences
            periods = 1.0 / (voiced_f0 + 1e-6)
            period_diffs = np.abs(np.diff(periods))
            
            # Jitter is average absolute difference between consecutive periods
            jitter = np.mean(period_diffs) / np.mean(periods) * 100
            return float(jitter)
        else:
            return 0.0
    
    def estimate_speaking_rate(self, audio_data: np.ndarray) -> float:
        """
        Estimate speaking rate (syllables per second)
        Faster speaking rate can indicate stress
        
        Args:
            audio_data: Audio samples
            
        Returns:
            Estimated speaking rate
        """
        # Use onset strength to detect syllables
        onset_env = librosa.onset.onset_strength(
            y=audio_data,
            sr=self.sample_rate,
            hop_length=HOP_LENGTH
        )
        
        # Detect peaks (syllable onsets)
        peaks = librosa.util.peak_pick(
            onset_env,
            pre_max=3,
            post_max=3,
            pre_avg=3,
            post_avg=5,
            delta=0.5,
            wait=10
        )
        
        # Calculate speaking rate
        duration = len(audio_data) / self.sample_rate
        syllable_count = len(peaks)
        speaking_rate = syllable_count / duration if duration > 0 else 0.0
        
        return float(speaking_rate)
    
    def extract_energy_features(self, audio_data: np.ndarray) -> Dict[str, float]:
        """
        Extract energy envelope features
        Energy variations can indicate emotional arousal
        
        Args:
            audio_data: Audio samples
            
        Returns:
            Dictionary with energy features
        """
        # Calculate RMS energy
        rms = librosa.feature.rms(
            y=audio_data,
            frame_length=FRAME_LENGTH,
            hop_length=HOP_LENGTH
        )[0]
        
        # Calculate energy envelope
        energy = audio_data ** 2
        
        return {
            'rms_mean': float(np.mean(rms)),
            'rms_std': float(np.std(rms)),
            'rms_max': float(np.max(rms)),
            'energy_mean': float(np.mean(energy)),
            'energy_std': float(np.std(energy)),
            'energy_variation': float(np.std(rms) / (np.mean(rms) + 1e-6))
        }
    
    def extract_spectral_features(self, audio_data: np.ndarray) -> Dict[str, float]:
        """
        Extract spectral features
        Spectral characteristics change under stress
        
        Args:
            audio_data: Audio samples
            
        Returns:
            Dictionary with spectral features
        """
        # Spectral centroid (brightness)
        spectral_centroid = librosa.feature.spectral_centroid(
            y=audio_data,
            sr=self.sample_rate,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH
        )[0]
        
        # Spectral bandwidth
        spectral_bandwidth = librosa.feature.spectral_bandwidth(
            y=audio_data,
            sr=self.sample_rate,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH
        )[0]
        
        # Spectral rolloff
        spectral_rolloff = librosa.feature.spectral_rolloff(
            y=audio_data,
            sr=self.sample_rate,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH
        )[0]
        
        # Zero crossing rate (voice quality indicator)
        zcr = librosa.feature.zero_crossing_rate(
            audio_data,
            frame_length=FRAME_LENGTH,
            hop_length=HOP_LENGTH
        )[0]
        
        # MFCCs (voice timbre)
        mfcc = librosa.feature.mfcc(
            y=audio_data,
            sr=self.sample_rate,
            n_mfcc=N_MFCC,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH
        )
        
        return {
            'spectral_centroid_mean': float(np.mean(spectral_centroid)),
            'spectral_centroid_std': float(np.std(spectral_centroid)),
            'spectral_bandwidth_mean': float(np.mean(spectral_bandwidth)),
            'spectral_rolloff_mean': float(np.mean(spectral_rolloff)),
            'zero_crossing_rate_mean': float(np.mean(zcr)),
            'zero_crossing_rate_std': float(np.std(zcr)),
            'mfcc_mean': float(np.mean(mfcc)),
            'mfcc_std': float(np.std(mfcc))
        }
    
    def get_feature_vector(self, features: Dict[str, float]) -> np.ndarray:
        """
        Convert feature dictionary to ordered vector
        
        Args:
            features: Dictionary of extracted features
            
        Returns:
            Numpy array of features in consistent order
        """
        feature_order = [
            'pitch_mean', 'pitch_std', 'pitch_range', 'pitch_variation',
            'jitter', 'speaking_rate',
            'rms_mean', 'rms_std', 'energy_variation',
            'spectral_centroid_mean', 'spectral_bandwidth_mean',
            'zero_crossing_rate_mean', 'mfcc_mean'
        ]
        
        vector = [features.get(key, 0.0) for key in feature_order]
        return np.array(vector)
