"""
Voice Stress Analysis Module

Analyzes voice stress based on physiological speech signal properties:
- Pitch (F0) variability
- Jitter (pitch perturbation)
- Energy instability
- Speaking rate (zero crossing rate)

No emotion classification - purely signal-based stress markers.
CPU-only, no deep learning required.
"""

import numpy as np
import librosa
from typing import Dict, Tuple, Optional
from scipy import signal as scipy_signal
import warnings

warnings.filterwarnings('ignore', category=UserWarning)


class VoiceStressAnalyzer:
    """
    Production-ready voice stress analyzer using acoustic instability markers.
    
    Attributes:
        sample_rate (int): Audio sampling rate (default: 16000 Hz)
        window_size (float): Analysis window size in seconds (default: 1.5 seconds)
        hop_length (int): Number of samples between frames for analysis
    """
    
    def __init__(self, sample_rate: int = 16000, window_size: float = 1.5):
        """
        Initialize the Voice Stress Analyzer.
        
        Args:
            sample_rate: Sampling rate for audio processing (Hz)
            window_size: Size of analysis window in seconds
        """
        self.sample_rate = sample_rate
        self.window_size = window_size
        self.hop_length = 512
        
        # Normalization ranges (empirically determined from voice data)
        self.pitch_var_range = (0.0, 50.0)  # Hz std dev
        self.jitter_range = (0.0, 5.0)  # Hz mean absolute difference
        self.energy_range = (0.0, 0.15)  # RMS energy std dev
        self.zcr_range = (0.0, 0.3)  # Zero crossing rate std dev
        
    def analyze_audio(self, audio_data: np.ndarray, sr: Optional[int] = None) -> Dict:
        """
        Analyze audio for voice stress indicators.
        
        Args:
            audio_data: Audio waveform as numpy array (mono)
            sr: Sample rate of the audio (if None, uses self.sample_rate)
            
        Returns:
            Dictionary containing stress score and component features
        """
        if sr is None:
            sr = self.sample_rate
            
        # Resample if necessary
        if sr != self.sample_rate:
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)
            sr = self.sample_rate
            
        # Ensure mono audio
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
            
        # Normalize audio amplitude
        audio_data = self._normalize_audio(audio_data)
        
        # Extract features
        pitch_variability = self._compute_pitch_variability(audio_data, sr)
        jitter = self._compute_jitter(audio_data, sr)
        energy_instability = self._compute_energy_instability(audio_data, sr)
        speaking_rate = self._compute_speaking_rate(audio_data, sr)
        
        # Normalize features to 0-1 range
        norm_pitch = self._normalize_feature(pitch_variability, self.pitch_var_range)
        norm_jitter = self._normalize_feature(jitter, self.jitter_range)
        norm_energy = self._normalize_feature(energy_instability, self.energy_range)
        norm_zcr = self._normalize_feature(speaking_rate, self.zcr_range)
        
        # Compute weighted stress score (0-100)
        voice_stress = self._compute_stress_score(
            norm_pitch, norm_jitter, norm_energy, norm_zcr
        )
        
        return {
            "voice_stress": round(voice_stress, 2),
            "pitch_variability": round(norm_pitch, 3),
            "jitter": round(norm_jitter, 3),
            "energy": round(norm_energy, 3),
            "speaking_rate": round(norm_zcr, 3),
            "raw_features": {
                "pitch_std_hz": round(pitch_variability, 2),
                "jitter_hz": round(jitter, 4),
                "energy_std": round(energy_instability, 4),
                "zcr_std": round(speaking_rate, 4)
            }
        }
    
    def analyze_file(self, audio_path: str) -> Dict:
        """
        Analyze an audio file for voice stress.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary containing stress analysis results
        """
        audio_data, sr = librosa.load(audio_path, sr=self.sample_rate, mono=True)
        return self.analyze_audio(audio_data, sr)
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio amplitude to -1 to 1 range."""
        max_val = np.abs(audio).max()
        if max_val > 0:
            return audio / max_val
        return audio
    
    def _compute_pitch_variability(self, audio: np.ndarray, sr: int) -> float:
        """
        Compute pitch (F0) variability using standard deviation.
        
        Higher variability indicates vocal fold tension and instability.
        
        Args:
            audio: Audio waveform
            sr: Sample rate
            
        Returns:
            Standard deviation of pitch values (Hz)
        """
        try:
            # Extract pitch using probabilistic YIN algorithm
            f0, voiced_flag, voiced_probs = librosa.pyin(
                audio,
                fmin=librosa.note_to_hz('C2'),  # ~65 Hz
                fmax=librosa.note_to_hz('C7'),  # ~2093 Hz
                sr=sr,
                frame_length=2048,
                hop_length=self.hop_length
            )
            
            # Filter out unvoiced frames and NaN values
            valid_f0 = f0[~np.isnan(f0) & (voiced_probs > 0.5)]
            
            if len(valid_f0) > 5:  # Need sufficient voiced frames
                pitch_std = np.std(valid_f0)
                return float(pitch_std)
            else:
                return 0.0
                
        except Exception as e:
            print(f"Warning: Pitch extraction failed: {e}")
            return 0.0
    
    def _compute_jitter(self, audio: np.ndarray, sr: int) -> float:
        """
        Compute jitter (pitch perturbation).
        
        Mean absolute difference between consecutive pitch periods.
        Micro-tremors in speech increase jitter.
        
        Args:
            audio: Audio waveform
            sr: Sample rate
            
        Returns:
            Mean absolute jitter value (Hz)
        """
        try:
            f0, voiced_flag, voiced_probs = librosa.pyin(
                audio,
                fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7'),
                sr=sr,
                frame_length=2048,
                hop_length=self.hop_length
            )
            
            # Filter valid pitch values
            valid_f0 = f0[~np.isnan(f0) & (voiced_probs > 0.5)]
            
            if len(valid_f0) > 5:
                # Compute absolute differences between consecutive pitch values
                pitch_diffs = np.abs(np.diff(valid_f0))
                jitter = np.mean(pitch_diffs)
                return float(jitter)
            else:
                return 0.0
                
        except Exception as e:
            print(f"Warning: Jitter computation failed: {e}")
            return 0.0
    
    def _compute_energy_instability(self, audio: np.ndarray, sr: int) -> float:
        """
        Compute energy instability using RMS energy variations.
        
        Stress causes irregular energy distribution in speech.
        
        Args:
            audio: Audio waveform
            sr: Sample rate
            
        Returns:
            Standard deviation of RMS energy
        """
        try:
            # Compute RMS energy
            rms = librosa.feature.rms(
                y=audio,
                frame_length=2048,
                hop_length=self.hop_length
            )[0]
            
            # Compute standard deviation of energy
            energy_std = np.std(rms)
            return float(energy_std)
            
        except Exception as e:
            print(f"Warning: Energy computation failed: {e}")
            return 0.0
    
    def _compute_speaking_rate(self, audio: np.ndarray, sr: int) -> float:
        """
        Compute speaking rate proxy using Zero Crossing Rate (ZCR).
        
        ZCR variability indicates speech rate irregularities under stress.
        
        Args:
            audio: Audio waveform
            sr: Sample rate
            
        Returns:
            Standard deviation of zero crossing rate
        """
        try:
            # Compute zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(
                audio,
                frame_length=2048,
                hop_length=self.hop_length
            )[0]
            
            # Compute standard deviation
            zcr_std = np.std(zcr)
            return float(zcr_std)
            
        except Exception as e:
            print(f"Warning: ZCR computation failed: {e}")
            return 0.0
    
    def _normalize_feature(self, value: float, value_range: Tuple[float, float]) -> float:
        """
        Normalize feature value to 0-1 range.
        
        Args:
            value: Raw feature value
            value_range: (min, max) expected range
            
        Returns:
            Normalized value between 0 and 1
        """
        min_val, max_val = value_range
        normalized = (value - min_val) / (max_val - min_val)
        # Clip to 0-1 range
        return float(np.clip(normalized, 0.0, 1.0))
    
    def _compute_stress_score(
        self,
        pitch_var: float,
        jitter: float,
        energy: float,
        zcr: float
    ) -> float:
        """
        Compute weighted voice stress score.
        
        Weights based on physiological significance:
        - Pitch variability: 35% (primary stress indicator)
        - Jitter: 25% (vocal fold tension)
        - Energy: 20% (speech intensity variation)
        - Speaking rate: 20% (speech rhythm disruption)
        
        Args:
            pitch_var: Normalized pitch variability (0-1)
            jitter: Normalized jitter (0-1)
            energy: Normalized energy instability (0-1)
            zcr: Normalized zero crossing rate (0-1)
            
        Returns:
            Voice stress score (0-100)
        """
        stress_score = (
            0.35 * pitch_var +
            0.25 * jitter +
            0.20 * energy +
            0.20 * zcr
        )
        
        # Scale to 0-100 range
        return float(stress_score * 100.0)


def analyze_realtime_audio(
    audio_chunk: np.ndarray,
    sample_rate: int = 16000
) -> Dict:
    """
    Convenience function for real-time audio analysis.
    
    Args:
        audio_chunk: Audio data chunk (mono)
        sample_rate: Sampling rate
        
    Returns:
        Stress analysis results
    """
    analyzer = VoiceStressAnalyzer(sample_rate=sample_rate)
    return analyzer.analyze_audio(audio_chunk, sample_rate)


def analyze_audio_file(audio_path: str) -> Dict:
    """
    Convenience function for file-based audio analysis.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Stress analysis results
    """
    analyzer = VoiceStressAnalyzer()
    return analyzer.analyze_file(audio_path)


if __name__ == "__main__":
    # Example usage
    print("Voice Stress Analyzer - Ready")
    print("=" * 50)
    print("\nThis module provides voice stress analysis based on:")
    print("  • Pitch (F0) variability")
    print("  • Jitter (pitch perturbation)")
    print("  • Energy instability")
    print("  • Speaking rate variations")
    print("\nUse analyze_audio_file() or create VoiceStressAnalyzer instance.")
