"""
Getting Started with Voice Stress Detection
============================================

Quick setup guide for running the Voice Stress Detection model.
"""

import sys
import os

def check_dependencies():
    """Check if all required packages are installed"""
    required = {
        'numpy': 'numpy',
        'scipy': 'scipy', 
        'librosa': 'librosa',
        'pyaudio': 'pyaudio',
        'soundfile': 'soundfile',
        'noisereduce': 'noisereduce',
        'sklearn': 'scikit-learn'
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - NOT INSTALLED")
            missing.append(package)
    
    return missing

def main():
    print("="*70)
    print("VOICE STRESS DETECTION - SETUP CHECK")
    print("="*70)
    
    print("\n1. Checking Python version...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("   ⚠ Warning: Python 3.8+ recommended")
    else:
        print("   ✓ Python version OK")
    
    print("\n2. Checking dependencies...")
    missing = check_dependencies()
    
    if missing:
        print(f"\n⚠ Missing packages: {', '.join(missing)}")
        print("\nTo install missing packages:")
        print(f"   pip install {' '.join(missing)}")
        print("\nOr install all at once:")
        print("   pip install -r requirements.txt")
        return False
    else:
        print("\n✓ All dependencies installed!")
    
    print("\n3. Testing model import...")
    try:
        from voice_stress import VoiceStressModel
        print("   ✓ Model imported successfully")
        
        print("\n4. Creating test model...")
        model = VoiceStressModel()
        print("   ✓ Model initialized")
        model.cleanup()
        
        print("\n" + "="*70)
        print("✓ SETUP COMPLETE - Ready to use!")
        print("="*70)
        
        print("\nNext steps:")
        print("1. Run demo:     python demo.py")
        print("2. Run tests:    python test_voice_stress.py")
        print("3. See docs:     README.md")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
