"""
Voice Stress Predictor
Combines ML model (74% accuracy) + Mathematical signal processing
Takes user voice input → Returns stress score 0-100
"""
import numpy as np
import librosa
import pickle
import json
from pathlib import Path
import sounddevice as sd

class VoiceStressPredictor:
    def __init__(self):
        self.models_path = Path(__file__).parent / "models"
        self.model = None
        self.scaler = None
        self.config = None
        self.sample_rate = 22050
        
        # Emotion to stress mapping
        self.emotion_stress = {
            'neutral': 10, 'happy': 15, 'encouraging': 18, 'assertive': 35,
            'excited': 50, 'apologetic': 58, 'sad': 68, 'concerned': 72
        }
        
        self._load_model()
    
    def _load_model(self):
        """Load trained model and scaler."""
        try:
            with open(self.models_path / "stress_detector.pkl", 'rb') as f:
                self.model = pickle.load(f)
            with open(self.models_path / "scaler.pkl", 'rb') as f:
                self.scaler = pickle.load(f)
            with open(self.models_path / "config.json", 'r') as f:
                self.config = json.load(f)
            print("✅ Model loaded successfully (74% accuracy)")
        except Exception as e:
            print(f"⚠️ Model not found, using mathematical analysis only: {e}")
            self.model = None
    
    def extract_features(self, audio, sr):
        """Extract same 51 features used in training."""
        try:
            if len(audio) < sr * 0.3:
                return None
            
            audio = librosa.util.normalize(audio)
            feat = []
            
            # MFCC (26 features)
            mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
            feat.extend(np.mean(mfcc, axis=1).tolist())
            feat.extend(np.std(mfcc, axis=1).tolist())
            
            # Spectral (8 features)
            feat.append(float(np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))))
            feat.append(float(np.std(librosa.feature.spectral_centroid(y=audio, sr=sr))))
            feat.append(float(np.mean(librosa.feature.spectral_rolloff(y=audio, sr=sr))))
            feat.append(float(np.std(librosa.feature.spectral_rolloff(y=audio, sr=sr))))
            feat.append(float(np.mean(librosa.feature.spectral_bandwidth(y=audio, sr=sr))))
            feat.append(float(np.std(librosa.feature.spectral_bandwidth(y=audio, sr=sr))))
            feat.append(float(np.mean(librosa.feature.spectral_flatness(y=audio))))
            feat.append(float(np.std(librosa.feature.spectral_flatness(y=audio))))
            
            # Chroma (2 features)
            chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
            feat.append(float(np.mean(chroma)))
            feat.append(float(np.std(chroma)))
            
            # ZCR (2 features)
            zcr = librosa.feature.zero_crossing_rate(audio)
            feat.append(float(np.mean(zcr)))
            feat.append(float(np.std(zcr)))
            
            # Energy (4 features)
            rms = librosa.feature.rms(y=audio)
            feat.append(float(np.mean(rms)))
            feat.append(float(np.std(rms)))
            feat.append(float(np.max(rms)))
            feat.append(float(np.min(rms)))
            
            # Pitch (6 features)
            f0, _, _ = librosa.pyin(audio, fmin=80, fmax=400, sr=sr)
            f0_clean = f0[~np.isnan(f0)]
            if len(f0_clean) > 1:
                feat.append(float(np.mean(f0_clean)))
                feat.append(float(np.std(f0_clean)))
                feat.append(float(np.max(f0_clean)))
                feat.append(float(np.min(f0_clean)))
                feat.append(float(np.ptp(f0_clean)))
                feat.append(float(np.mean(np.abs(np.diff(f0_clean)))))
            else:
                feat.extend([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            
            # Tempo (1 feature)
            tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
            feat.append(float(np.atleast_1d(tempo)[0]))
            
            return np.array(feat, dtype=np.float64)
        except:
            return None
    
    def mathematical_stress_analysis(self, audio, sr):
        """
        Pure mathematical/signal processing stress analysis.
        Based on scientific research on vocal stress markers.
        """
        audio = librosa.util.normalize(audio)
        
        # 1. Pitch Variability (stressed voice = more pitch variation)
        f0, _, _ = librosa.pyin(audio, fmin=80, fmax=400, sr=sr)
        f0_clean = f0[~np.isnan(f0)]
        
        if len(f0_clean) > 10:
            pitch_std = np.std(f0_clean)
            pitch_mean = np.mean(f0_clean)
            pitch_variability = min(100, (pitch_std / max(pitch_mean, 1)) * 500)
        else:
            pitch_variability = 30
        
        # 2. Jitter (pitch perturbation - stress increases jitter)
        if len(f0_clean) > 1:
            jitter = np.mean(np.abs(np.diff(f0_clean))) / max(np.mean(f0_clean), 1) * 100
            jitter_score = min(100, jitter * 50)
        else:
            jitter_score = 20
        
        # 3. Energy Instability (stressed voice = unstable energy)
        rms = librosa.feature.rms(y=audio)[0]
        energy_std = np.std(rms) / max(np.mean(rms), 0.001)
        energy_score = min(100, energy_std * 200)
        
        # 4. Speaking Rate (stress often increases speaking rate)
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        zcr_mean = np.mean(zcr)
        speaking_rate_score = min(100, zcr_mean * 1000)
        
        # 5. Spectral Flux (voice tension shows in spectral changes)
        spectral_flux = np.mean(np.abs(np.diff(librosa.feature.spectral_centroid(y=audio, sr=sr)[0])))
        flux_score = min(100, spectral_flux / 50)
        
        # Weighted combination
        math_stress = (
            pitch_variability * 0.30 +  # 30% weight
            jitter_score * 0.25 +        # 25% weight  
            energy_score * 0.20 +        # 20% weight
            speaking_rate_score * 0.15 + # 15% weight
            flux_score * 0.10            # 10% weight
        )
        
        return min(100, max(0, math_stress))
    
    def predict_from_audio(self, audio, sr=None):
        """
        Predict stress from audio array.
        Combines ML model + mathematical analysis.
        """
        if sr is None:
            sr = self.sample_rate
        
        # Resample if needed
        if sr != self.sample_rate:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=self.sample_rate)
            sr = self.sample_rate
        
        results = {
            'ml_stress': None,
            'math_stress': None,
            'combined_stress': None,
            'emotion': None,
            'stress_level': None
        }
        
        # Mathematical analysis (always available)
        math_stress = self.mathematical_stress_analysis(audio, sr)
        results['math_stress'] = round(math_stress, 1)
        
        # ML model prediction (if available)
        if self.model is not None and self.scaler is not None:
            features = self.extract_features(audio, sr)
            if features is not None:
                features_scaled = self.scaler.transform([features])
                
                # Get probability scores for all emotions
                probs = self.model.predict_proba(features_scaled)[0]
                emotion_id = self.model.predict(features_scaled)[0]
                
                # Map emotion ID to emotion name
                id_to_emotion = {v: k for k, v in self.config['emotion_map'].items()}
                emotion = id_to_emotion.get(emotion_id, 'neutral')
                
                # Calculate weighted stress based on ALL emotion probabilities
                ml_stress = 0
                for emo_id, prob in enumerate(probs):
                    emo_name = id_to_emotion.get(emo_id, 'neutral')
                    emo_stress = self.emotion_stress.get(emo_name, 40)
                    ml_stress += prob * emo_stress
                
                results['emotion'] = emotion
                results['ml_stress'] = round(ml_stress, 1)
        
        # Combined score (70% ML + 30% Math if ML available, else 100% Math)
        if results['ml_stress'] is not None:
            combined = results['ml_stress'] * 0.7 + results['math_stress'] * 0.3
        else:
            combined = results['math_stress']
        
        results['combined_stress'] = round(combined, 1)
        
        # Determine stress level
        if combined < 25:
            results['stress_level'] = "LOW"
        elif combined < 50:
            results['stress_level'] = "MODERATE"
        elif combined < 75:
            results['stress_level'] = "HIGH"
        else:
            results['stress_level'] = "VERY HIGH"
        
        return results
    
    def predict_from_file(self, file_path):
        """Predict stress from audio file."""
        audio, sr = librosa.load(file_path, sr=self.sample_rate, mono=True)
        return self.predict_from_audio(audio, sr)
    
    def record_and_predict(self, duration=5):
        """Record from microphone and predict stress."""
        print(f"\n🎤 Recording for {duration} seconds...")
        print("   Speak naturally about something.\n")
        
        for i in range(3, 0, -1):
            print(f"   Starting in {i}...")
            sd.sleep(1000)
        
        print("   🔴 RECORDING NOW - Speak!")
        
        audio = sd.rec(int(duration * self.sample_rate), 
                       samplerate=self.sample_rate, 
                       channels=1, 
                       dtype='float32')
        sd.wait()
        
        print("   ✅ Recording complete!\n")
        
        audio = audio.flatten()
        return self.predict_from_audio(audio, self.sample_rate)


def main():
    """Interactive demo."""
    print("\n" + "="*60)
    print("   VOICE STRESS DETECTOR")
    print("   ML Model (74%) + Mathematical Analysis")
    print("="*60)
    
    predictor = VoiceStressPredictor()
    
    while True:
        print("\nOptions:")
        print("  1. Record voice (5 seconds)")
        print("  2. Analyze audio file")
        print("  3. Exit")
        
        choice = input("\nChoice (1/2/3): ").strip()
        
        if choice == "1":
            results = predictor.record_and_predict(duration=5)
            
            print("\n" + "="*60)
            print("   STRESS ANALYSIS RESULTS")
            print("="*60)
            
            if results['emotion']:
                print(f"\n   Detected Emotion: {results['emotion'].upper()}")
            
            print(f"\n   📊 Stress Scores:")
            if results['ml_stress']:
                print(f"      ML Model:     {results['ml_stress']}/100")
            print(f"      Mathematical: {results['math_stress']}/100")
            print(f"      Combined:     {results['combined_stress']}/100")
            
            print(f"\n   🎯 Stress Level: {results['stress_level']}")
            
            # Visual bar
            bar_len = int(results['combined_stress'] / 2)
            bar = "█" * bar_len + "░" * (50 - bar_len)
            print(f"\n   [{bar}] {results['combined_stress']}%")
            
        elif choice == "2":
            file_path = input("\nEnter audio file path: ").strip()
            try:
                results = predictor.predict_from_file(file_path)
                
                print("\n" + "="*60)
                print("   STRESS ANALYSIS RESULTS")
                print("="*60)
                
                if results['emotion']:
                    print(f"\n   Detected Emotion: {results['emotion'].upper()}")
                
                print(f"\n   📊 Stress Scores:")
                if results['ml_stress']:
                    print(f"      ML Model:     {results['ml_stress']}/100")
                print(f"      Mathematical: {results['math_stress']}/100")
                print(f"      Combined:     {results['combined_stress']}/100")
                
                print(f"\n   🎯 Stress Level: {results['stress_level']}")
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                
        elif choice == "3":
            print("\n👋 Goodbye!")
            break
        else:
            print("\n⚠️ Invalid choice")


if __name__ == "__main__":
    main()
