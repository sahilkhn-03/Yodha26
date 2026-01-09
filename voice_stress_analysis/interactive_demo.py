"""
Interactive Voice Stress Analysis Demo
Record your voice and get instant stress analysis!
"""

import numpy as np
import sounddevice as sd
from voice_stress_analyzer import VoiceStressAnalyzer
import sys
import time

def record_audio(duration=5, sample_rate=16000):
    """Record audio from microphone."""
    print(f"\n🎤 Recording for {duration} seconds...")
    print("   Speak naturally into your microphone!")
    print("   📢 Starting in: ", end="", flush=True)
    
    for i in range(3, 0, -1):
        print(f"{i}... ", end="", flush=True)
        time.sleep(1)
    print("GO!\n")
    
    try:
        # Record audio
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='float32'
        )
        
        # Show recording progress
        for i in range(duration):
            print(f"🔴 Recording... {i+1}/{duration}s", end="\r", flush=True)
            time.sleep(1)
        
        sd.wait()
        print("\n✅ Recording complete!")
        
        return audio.flatten(), sample_rate
        
    except Exception as e:
        print(f"\n❌ Recording error: {e}")
        print("   Make sure your microphone is connected!")
        return None, None

def display_results(result):
    """Display analysis results in a nice format."""
    print("\n" + "=" * 70)
    print(" " * 20 + "📊 VOICE STRESS ANALYSIS RESULTS")
    print("=" * 70)
    
    stress = result['voice_stress']
    
    # Color-coded stress level
    if stress < 30:
        level = "LOW 😌"
        status = "✅ You sound calm and relaxed"
        bar_color = "🟢"
    elif stress < 60:
        level = "MODERATE 😐"
        status = "⚠️  Some tension detected"
        bar_color = "🟡"
    else:
        level = "HIGH 😰"
        status = "⚡ Significant vocal stress"
        bar_color = "🔴"
    
    # Overall stress score
    print(f"\n🎯 OVERALL STRESS SCORE: {stress}/100")
    print(f"   Level: {level}")
    print(f"   {status}")
    
    # Stress bar visualization
    bar_length = int(stress / 2)  # 50 chars max
    bar = bar_color * bar_length + "⬜" * (50 - bar_length)
    print(f"\n   [{bar}] {stress}%")
    
    # Component breakdown
    print(f"\n📈 COMPONENT FEATURES:")
    print("-" * 70)
    
    features = [
        ("Pitch Variability", result['pitch_variability'], "Voice pitch instability"),
        ("Jitter", result['jitter'], "Micro-tremors in speech"),
        ("Energy", result['energy'], "Speech intensity variation"),
        ("Speaking Rate", result['speaking_rate'], "Speech rhythm irregularity")
    ]
    
    for name, value, description in features:
        percentage = int(value * 100)
        bar = "█" * (percentage // 5) + "░" * (20 - (percentage // 5))
        print(f"  {name:20s}: [{bar}] {value:.3f} - {description}")
    
    # Raw measurements
    print(f"\n🔬 RAW MEASUREMENTS:")
    print("-" * 70)
    print(f"  Pitch Std Dev:  {result['raw_features']['pitch_std_hz']:.2f} Hz")
    print(f"  Jitter:         {result['raw_features']['jitter_hz']:.4f} Hz")
    print(f"  Energy Std:     {result['raw_features']['energy_std']:.4f}")
    print(f"  ZCR Std:        {result['raw_features']['zcr_std']:.4f}")
    
    print("\n" + "=" * 70)

def main():
    """Main interactive demo."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "🎙️  VOICE STRESS ANALYSIS - LIVE DEMO" + " " * 15 + "║")
    print("╚" + "=" * 68 + "╝")
    
    print("\n📌 This tool analyzes vocal stress markers in your speech:")
    print("   • Pitch instability")
    print("   • Voice tremors (jitter)")
    print("   • Energy variations")
    print("   • Speaking rate changes")
    
    print("\n⚠️  Note: Speak naturally! Reading text or forced speech may affect results.")
    
    # Initialize analyzer
    print("\n🔧 Initializing voice stress analyzer...")
    try:
        analyzer = VoiceStressAnalyzer(sample_rate=16000)
        print("✅ Analyzer ready!")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return
    
    session = 1
    
    while True:
        print("\n" + "─" * 70)
        print(f"SESSION {session}")
        print("─" * 70)
        
        # Ask user to record
        print("\n📝 Instructions:")
        print("   1. Press ENTER when ready to record")
        print("   2. Speak for 5 seconds (talk about anything!)")
        print("   3. Get instant stress analysis")
        print("\n   Suggestions:")
        print("   - Talk about your day")
        print("   - Describe what you see around you")
        print("   - Count from 1 to 20")
        print("   - Read a paragraph from a book")
        
        input("\n👉 Press ENTER to start recording (or 'q' + ENTER to quit): ")
        
        # Check for quit
        if input == 'q':
            break
        
        # Record audio
        audio, sr = record_audio(duration=5, sample_rate=16000)
        
        if audio is None:
            print("\n❌ Recording failed. Try again.")
            continue
        
        # Check if audio has content
        if np.max(np.abs(audio)) < 0.001:
            print("\n⚠️  No audio detected! Make sure:")
            print("   - Your microphone is connected")
            print("   - Volume is not muted")
            print("   - You're speaking loud enough")
            retry = input("\n   Try again? (y/n): ")
            if retry.lower() != 'y':
                continue
            else:
                continue
        
        # Analyze
        print("\n🔄 Analyzing your voice...")
        try:
            result = analyzer.analyze_audio(audio, sr)
            
            # Display results
            display_results(result)
            
        except Exception as e:
            print(f"\n❌ Analysis error: {e}")
            import traceback
            traceback.print_exc()
        
        # Ask to continue
        print("\n" + "─" * 70)
        again = input("\n🔁 Record another sample? (y/n): ")
        
        if again.lower() != 'y':
            break
        
        session += 1
    
    print("\n" + "=" * 70)
    print("👋 Thanks for using Voice Stress Analysis!")
    print("=" * 70)
    print("\n💡 Tips for better results:")
    print("   • Record in a quiet environment")
    print("   • Speak naturally (not monotone)")
    print("   • 3-5 seconds of speech is ideal")
    print("   • Avoid background noise")
    print("\n✅ Session complete!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
