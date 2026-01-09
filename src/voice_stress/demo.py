"""
Demo Script for Voice Stress Detection
Demonstrates real-time and file-based voice stress analysis
"""

import numpy as np
import argparse
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice_stress import VoiceStressModel, analyze_voice_stress


def demo_realtime(duration: float = None):
    """
    Demo real-time voice stress detection from microphone
    
    Args:
        duration: Duration in seconds (None = until stopped)
    """
    print("\n" + "="*70)
    print("REAL-TIME VOICE STRESS DETECTION DEMO")
    print("="*70)
    print("\nThis demo will analyze your voice in real-time.")
    print("Speak naturally into your microphone.")
    print("Try different speaking styles to see stress levels change:")
    print("  - Calm, slow speech (low stress)")
    print("  - Fast, tense speech (high stress)")
    print("  - Varying pitch and volume (moderate stress)")
    print("\nPress Ctrl+C to stop the demo.\n")
    
    input("Press Enter to start...")
    
    with VoiceStressModel() as model:
        model.start_realtime_analysis(duration_seconds=duration)
        
        # Print summary
        print("\n" + "="*70)
        print("SESSION SUMMARY")
        print("="*70)
        summary = model.get_stress_summary()
        
        if 'message' not in summary:
            print(f"\nTotal samples: {summary['count']}")
            print(f"Current stress: {summary['current']:.1f}/100")
            print(f"Average stress: {summary['average']:.1f}/100")
            print(f"Min stress: {summary['min']:.1f}/100")
            print(f"Max stress: {summary['max']:.1f}/100")
            print(f"Stress variability (std): {summary['std']:.1f}")
            print(f"High stress events: {summary['high_stress_events']}")
            
            if summary.get('trend'):
                trend = summary['trend']
                print(f"\nOverall trend: {trend['trend']}")
                print(f"Trend slope: {trend['slope']:.2f}")


def demo_file(file_path: str):
    """
    Demo voice stress detection from audio file
    
    Args:
        file_path: Path to audio file
    """
    print("\n" + "="*70)
    print("FILE-BASED VOICE STRESS DETECTION DEMO")
    print("="*70)
    print(f"\nAnalyzing file: {file_path}\n")
    
    # Analyze file
    result = analyze_voice_stress(file_path, input_type='file')
    
    # Print results
    if 'error' in result:
        print(f"Error: {result['error']}")
        return
    
    print(f"\nStress Analysis Results:")
    print(f"{'='*70}")
    print(f"Stress Index: {result['stress_index']:.1f}/100")
    print(f"Stress Level: {result['stress_level']}")
    print(f"High Stress Alert: {'YES ⚠️' if result['is_high_stress'] else 'NO'}")
    
    # Print performance
    perf = result['performance']
    print(f"\nPerformance:")
    print(f"  Inference Time: {perf['inference_time_ms']:.1f}ms")
    print(f"  Target: <{perf['target_latency_ms']}ms")
    print(f"  Meets Target: {'✓ Yes' if perf['meets_target'] else '✗ No'}")
    
    # Print top stress indicators
    if result.get('stress_indicators'):
        print(f"\nStress Indicators Detected:")
        for indicator in result['stress_indicators']:
            print(f"  • {indicator['feature']}: {indicator['value']} "
                  f"(threshold: {indicator['threshold']}, severity: {indicator['severity']})")
    
    # Print top feature contributions
    print(f"\nTop Feature Contributions to Stress Score:")
    contributions = result['feature_contributions']
    sorted_contrib = sorted(contributions.items(), key=lambda x: x[1], reverse=True)[:5]
    for feature, contrib in sorted_contrib:
        print(f"  • {feature}: {contrib:.1f}%")
    
    # Print raw features (sample)
    print(f"\nKey Raw Features:")
    raw_features = result['raw_features']
    key_features = ['pitch_mean', 'jitter', 'speaking_rate', 'rms_mean']
    for feature in key_features:
        if feature in raw_features:
            print(f"  • {feature}: {raw_features[feature]:.2f}")
    
    print(f"\n{'='*70}")


def demo_synthetic():
    """
    Demo with synthetic audio to show different stress levels
    """
    print("\n" + "="*70)
    print("SYNTHETIC AUDIO DEMO")
    print("="*70)
    print("\nGenerating synthetic audio samples with different characteristics...")
    
    from voice_stress import VoiceStressModel
    model = VoiceStressModel()
    
    # Generate different audio patterns
    sample_rate = 22050
    duration = 2.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    test_cases = [
        {
            'name': 'Low Stress (Calm)',
            'audio': 0.3 * np.sin(2 * np.pi * 150 * t)  # Stable, low pitch
        },
        {
            'name': 'Moderate Stress (Variable)',
            'audio': 0.5 * np.sin(2 * np.pi * 200 * t) * (1 + 0.3 * np.sin(2 * np.pi * 3 * t))
        },
        {
            'name': 'High Stress (Tense)',
            'audio': 0.7 * np.sin(2 * np.pi * 250 * t + 10 * np.sin(2 * np.pi * 15 * t))
        }
    ]
    
    print()
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print("-" * 70)
        
        result = model.process_audio(test['audio'], preprocess=False)
        
        print(f"Stress Index: {result['stress_index']:.1f}/100")
        print(f"Stress Level: {result['stress_level']}")
        
        # Visual meter
        bar_length = 40
        filled = int((result['stress_index'] / 100) * bar_length)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"[{bar}] {result['stress_index']:.1f}%")
    
    model.cleanup()
    print(f"\n{'='*70}")


def main():
    """Main demo function"""
    parser = argparse.ArgumentParser(
        description='Voice Stress Detection Demo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Real-time demo (microphone)
  python demo.py --realtime
  
  # Real-time demo for 30 seconds
  python demo.py --realtime --duration 30
  
  # Analyze audio file
  python demo.py --file path/to/audio.wav
  
  # Synthetic audio demo
  python demo.py --synthetic
        """
    )
    
    parser.add_argument('--realtime', action='store_true',
                       help='Run real-time demo with microphone')
    parser.add_argument('--file', type=str,
                       help='Path to audio file to analyze')
    parser.add_argument('--duration', type=float,
                       help='Duration for real-time demo (seconds)')
    parser.add_argument('--synthetic', action='store_true',
                       help='Run synthetic audio demo')
    
    args = parser.parse_args()
    
    # Run appropriate demo
    if args.realtime:
        demo_realtime(duration=args.duration)
    elif args.file:
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
        demo_file(args.file)
    elif args.synthetic:
        demo_synthetic()
    else:
        # Default: show all demos
        print("\nVoice Stress Detection - Demo Menu")
        print("="*70)
        print("\n1. Real-time demo (microphone)")
        print("2. Synthetic audio demo")
        print("3. File analysis (specify path)")
        print("4. Exit")
        
        choice = input("\nSelect demo (1-4): ").strip()
        
        if choice == '1':
            demo_realtime()
        elif choice == '2':
            demo_synthetic()
        elif choice == '3':
            file_path = input("Enter audio file path: ").strip()
            if os.path.exists(file_path):
                demo_file(file_path)
            else:
                print(f"Error: File not found: {file_path}")
        elif choice == '4':
            print("Goodbye!")
        else:
            print("Invalid choice")


if __name__ == '__main__':
    main()
