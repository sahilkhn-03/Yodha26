"""
Audio Handler Module
Handles real-time audio capture and preprocessing using PyAudio
"""

import numpy as np
import pyaudio
import wave
from typing import Optional, Callable
from scipy import signal
import noisereduce as nr

from .config import (
    SAMPLE_RATE, CHUNK_SIZE, CHANNELS, 
    LOWPASS_CUTOFF, FILTER_ORDER, MIN_AUDIO_DURATION
)


class AudioHandler:
    """Handles real-time audio input and preprocessing"""
    
    def __init__(self, sample_rate: int = SAMPLE_RATE, 
                 chunk_size: int = CHUNK_SIZE,
                 channels: int = CHANNELS):
        """
        Initialize audio handler
        
        Args:
            sample_rate: Audio sampling rate (Hz)
            chunk_size: Size of audio buffer
            channels: Number of audio channels (1=mono, 2=stereo)
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.is_recording = False
        self.audio_buffer = []
        
    def start_stream(self):
        """Start audio input stream"""
        try:
            self.stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            self.is_recording = True
            self.stream.start_stream()
            print(f"Audio stream started (Sample Rate: {self.sample_rate} Hz)")
        except Exception as e:
            print(f"Error starting audio stream: {e}")
            raise
    
    def stop_stream(self):
        """Stop audio input stream"""
        if self.stream:
            self.is_recording = False
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            print("Audio stream stopped")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback function for audio stream"""
        if status:
            print(f"Audio stream status: {status}")
        
        # Convert bytes to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        self.audio_buffer.append(audio_data)
        
        return (in_data, pyaudio.paContinue)
    
    def get_audio_chunk(self, duration: float = MIN_AUDIO_DURATION) -> np.ndarray:
        """
        Get audio chunk of specified duration
        
        Args:
            duration: Duration of audio chunk in seconds
            
        Returns:
            Numpy array of audio samples
        """
        required_chunks = int(np.ceil(duration * self.sample_rate / self.chunk_size))
        
        if len(self.audio_buffer) >= required_chunks:
            # Get required chunks and remove from buffer
            chunks = self.audio_buffer[:required_chunks]
            self.audio_buffer = self.audio_buffer[required_chunks:]
            return np.concatenate(chunks)
        else:
            return None
    
    def preprocess_audio(self, audio_data: np.ndarray, 
                        apply_noise_reduction: bool = True,
                        apply_lowpass: bool = True) -> np.ndarray:
        """
        Preprocess audio data with noise reduction and filtering
        
        Args:
            audio_data: Raw audio samples
            apply_noise_reduction: Whether to apply noise reduction
            apply_lowpass: Whether to apply low-pass filter
            
        Returns:
            Preprocessed audio data
        """
        processed = audio_data.copy()
        
        # Normalize audio
        if np.max(np.abs(processed)) > 0:
            processed = processed / np.max(np.abs(processed))
        
        # Apply noise reduction
        if apply_noise_reduction:
            try:
                processed = nr.reduce_noise(
                    y=processed, 
                    sr=self.sample_rate,
                    stationary=True
                )
            except Exception as e:
                print(f"Noise reduction failed: {e}")
        
        # Apply low-pass filter for noise robustness
        if apply_lowpass:
            nyquist = self.sample_rate / 2
            normal_cutoff = LOWPASS_CUTOFF / nyquist
            b, a = signal.butter(FILTER_ORDER, normal_cutoff, btype='low')
            processed = signal.filtfilt(b, a, processed)
        
        return processed
    
    def load_audio_file(self, file_path: str) -> tuple[np.ndarray, int]:
        """
        Load audio from file
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        import librosa
        audio_data, sr = librosa.load(file_path, sr=self.sample_rate, mono=True)
        return audio_data, sr
    
    def save_audio(self, audio_data: np.ndarray, file_path: str):
        """
        Save audio data to WAV file
        
        Args:
            audio_data: Audio samples to save
            file_path: Output file path
        """
        import soundfile as sf
        sf.write(file_path, audio_data, self.sample_rate)
        print(f"Audio saved to {file_path}")
    
    def cleanup(self):
        """Clean up audio resources"""
        self.stop_stream()
        self.audio.terminate()
        print("Audio handler cleaned up")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
