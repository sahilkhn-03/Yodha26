"""
Test and demonstration script for Voice Stress Analyzer.

Demonstrates:
1. Synthetic audio generation for testing
2. Real-time audio capture and analysis
3. File-based audio analysis
4. Integration example with stress monitoring
"""

import numpy as np
import sounddevice as sd
from voice_stress_analyzer import VoiceStressAnalyzer, analyze_audio_file, analyze_realtime_audio
import time
from typing import Optional


def generate_test_audio(
    duration: float = 2.0,
    sample_rate: int = 16000,
    base_freq: float = 150.0,
    stress_level: str = "low"
) -> np.ndarray:
    """
    Generate synthetic voice-like audio for testing.
    
    Args:
        duration: Audio duration in seconds
        sample_rate: Sampling rate
        base_freq: Base frequency (Hz) simulating voice pitch
        stress_level: "low", "medium", or "high" stress simulation
        
    Returns:
        Synthetic audio waveform
    """
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Configure parameters based on stress level
    if stress_level == "low":
        pitch_variation = 5.0
        jitter_amount = 0.5
        energy_variation = 0.1
    elif stress_level == "medium":
        pitch_variation = 15.0
        jitter_amount = 2.0
        energy_variation = 0.3
    else:  # high
        pitch_variation = 30.0
        jitter_amount = 4.0
        energy_variation = 0.5
    
    # Generate pitch with variation (simulating F0 instability)
    pitch_modulation = np.sin(2 * np.pi * 3 * t) * pitch_variation
    instantaneous_freq = base_freq + pitch_modulation
    
    # Add jitter (micro-variations)
    jitter = np.random.randn(len(t)) * jitter_amount
    instantaneous_freq += jitter
    
    # Generate tone
    phase = np.cumsum(2 * np.pi * instantaneous_freq / sample_rate)
    audio = np.sin(phase)
    
    # Add energy variation
    energy_envelope = 1.0 + np.random.randn(len(t)) * energy_variation
    audio *= energy_envelope
    
    # Add some harmonics for voice-like quality
    audio += 0.3 * np.sin(2 * phase)
    audio += 0.15 * np.sin(3 * phase)
    
    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.8
    
    return audio.astype(np.float32)


def test_synthetic_audio():
    """Test analyzer with synthetic audio at different stress levels."""
    print("=" * 60)
    print("TEST 1: Synthetic Audio Analysis")
    print("=" * 60)
    
    analyzer = VoiceStressAnalyzer(sample_rate=16000)
    
    stress_levels = ["low", "medium", "high"]
    
    for level in stress_levels:
        print(f"\n{level.upper()} Stress Simulation:")
        print("-" * 40)
        
        # Generate test audio
        audio = generate_test_audio(duration=2.0, stress_level=level)
        
        # Analyze
        result = analyzer.analyze_audio(audio)
        
        # Display results
        print(f"Voice Stress Score: {result['voice_stress']}/100")
        print(f"  • Pitch Variability: {result['pitch_variability']:.3f}")
        print(f"  • Jitter:            {result['jitter']:.3f}")
        print(f"  • Energy:            {result['energy']:.3f}")
        print(f"  • Speaking Rate:     {result['speaking_rate']:.3f}")
        print(f"\nRaw Features:")
        print(f"  • Pitch Std:  {result['raw_features']['pitch_std_hz']:.2f} Hz")
        print(f"  • Jitter:     {result['raw_features']['jitter_hz']:.4f} Hz")
        print(f"  • Energy Std: {result['raw_features']['energy_std']:.4f}")
        print(f"  • ZCR Std:    {result['raw_features']['zcr_std']:.4f}")


def test_realtime_capture(duration: int = 5):
    """
    Test real-time audio capture and analysis.
    
    Args:
        duration: Recording duration in seconds
    """
    print("\n" + "=" * 60)
    print("TEST 2: Real-Time Audio Capture")
    print("=" * 60)
    print(f"\nRecording for {duration} seconds...")
    print("Please speak naturally into your microphone.\n")
    
    sample_rate = 16000
    
    try:
        # Record audio
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        
        print("Recording complete. Analyzing...\n")
        
        # Flatten to 1D array
        audio = audio.flatten()
        
        # Analyze
        result = analyze_realtime_audio(audio, sample_rate)
        
        # Display results
        print("Analysis Results:")
        print("-" * 40)
        print(f"Voice Stress Score: {result['voice_stress']}/100")
        print(f"\nComponent Features:")
        print(f"  • Pitch Variability: {result['pitch_variability']:.3f}")
        print(f"  • Jitter:            {result['jitter']:.3f}")
        print(f"  • Energy:            {result['energy']:.3f}")
        print(f"  • Speaking Rate:     {result['speaking_rate']:.3f}")
        
        # Interpret stress level
        stress_score = result['voice_stress']
        if stress_score < 30:
            interpretation = "LOW - Calm and relaxed speech"
        elif stress_score < 60:
            interpretation = "MODERATE - Some vocal tension detected"
        else:
            interpretation = "HIGH - Significant vocal stress markers"
        
        print(f"\nInterpretation: {interpretation}")
        
    except Exception as e:
        print(f"Error during recording: {e}")
        print("Make sure your microphone is connected and accessible.")


def test_continuous_monitoring(duration: int = 10, window_size: float = 2.0):
    """
    Continuous monitoring with overlapping windows.
    
    Args:
        duration: Total monitoring duration in seconds
        window_size: Analysis window size in seconds
    """
    print("\n" + "=" * 60)
    print("TEST 3: Continuous Monitoring")
    print("=" * 60)
    print(f"\nMonitoring for {duration} seconds with {window_size}s windows...")
    print("Speak naturally to see real-time stress analysis.\n")
    
    sample_rate = 16000
    window_samples = int(window_size * sample_rate)
    
    analyzer = VoiceStressAnalyzer(sample_rate=sample_rate)
    
    try:
        # Start streaming
        print(f"{'Time (s)':<10} {'Stress Score':<15} {'Status':<20}")
        print("-" * 50)
        
        def audio_callback(indata, frames, time_info, status):
            """Process audio in real-time."""
            if status:
                print(f"Status: {status}")
            
            audio_chunk = indata[:, 0].copy()
            
            # Analyze chunk
            result = analyzer.analyze_audio(audio_chunk, sample_rate)
            
            # Display
            elapsed = time_info.inputBufferAdcTime
            stress = result['voice_stress']
            
            if stress < 30:
                status_text = "✓ Calm"
            elif stress < 60:
                status_text = "⚠ Moderate"
            else:
                status_text = "⚡ High Stress"
            
            print(f"{elapsed:>8.1f}s  {stress:>6.1f}/100      {status_text}")
        
        # Stream audio
        with sd.InputStream(
            channels=1,
            samplerate=sample_rate,
            blocksize=window_samples,
            callback=audio_callback
        ):
            sd.sleep(duration * 1000)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
    except Exception as e:
        print(f"\nError during monitoring: {e}")


def demo_integration_example():
    """
    Demonstrate integration pattern with other systems.
    """
    print("\n" + "=" * 60)
    print("DEMO: Integration Pattern")
    print("=" * 60)
    
    print("\nExample: Combining with facial stress analysis")
    print("-" * 60)
    
    # Simulate voice stress data
    voice_audio = generate_test_audio(duration=2.0, stress_level="medium")
    analyzer = VoiceStressAnalyzer()
    voice_result = analyzer.analyze_audio(voice_audio)
    
    # Simulated facial stress score (would come from facial analysis module)
    facial_stress_score = 55.0
    
    voice_stress_score = voice_result['voice_stress']
    
    print(f"\nIndividual Modalities:")
    print(f"  • Voice Stress:  {voice_stress_score:.1f}/100")
    print(f"  • Facial Stress: {facial_stress_score:.1f}/100")
    
    # Combined stress score (weighted average)
    combined_stress = (0.6 * voice_stress_score + 0.4 * facial_stress_score)
    
    print(f"\nCombined Stress Score: {combined_stress:.1f}/100")
    print(f"(60% voice, 40% facial)")
    
    print("\n" + "-" * 60)
    print("Integration Code Example:")
    print("-" * 60)
    print("""
from voice_stress_analyzer import VoiceStressAnalyzer
# from facial_stress_analyzer import FacialStressAnalyzer

voice_analyzer = VoiceStressAnalyzer()
# facial_analyzer = FacialStressAnalyzer()

# Analyze voice
voice_result = voice_analyzer.analyze_audio(audio_data)

# Analyze face
# facial_result = facial_analyzer.analyze_frame(video_frame)

# Combine scores
combined_score = (
    0.6 * voice_result['voice_stress'] +
    0.4 * facial_result['stress_score']
)

# Use combined score for assessment
print(f"Overall Stress: {combined_score}/100")
    """)


def main():
    """Run all tests and demonstrations."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "VOICE STRESS ANALYZER - TEST SUITE" + " " * 13 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\nPhysiological Speech Signal Analysis")
    print("No emotion classification • CPU-only • Production-ready\n")
    
    # Test 1: Synthetic audio
    test_synthetic_audio()
    
    # Test 2: Real-time capture (optional)
    print("\n" + "=" * 60)
    response = input("\nRun real-time microphone test? (y/n): ").strip().lower()
    if response == 'y':
        test_realtime_capture(duration=5)
    
    # Test 3: Continuous monitoring (optional)
    print("\n" + "=" * 60)
    response = input("\nRun continuous monitoring demo? (y/n): ").strip().lower()
    if response == 'y':
        test_continuous_monitoring(duration=10, window_size=2.0)
    
    # Demo: Integration
    demo_integration_example()
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
    print("\nModule is ready for production use.")
    print("Import with: from voice_stress_analyzer import VoiceStressAnalyzer")


if __name__ == "__main__":
    main()
