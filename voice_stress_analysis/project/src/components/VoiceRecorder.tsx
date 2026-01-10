import { useState, useRef, useEffect } from 'react';
import { Mic, Loader2, Activity } from 'lucide-react';
import { AudioWaveform } from './AudioWaveform';
import { VoiceStressDisplay } from './VoiceStressDisplay';
import { analyzeVoiceStressWithAPI } from '../utils/voiceAnalysis';
import { supabase, VoiceAnalysis } from '../lib/supabase';

export function VoiceRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [analysis, setAnalysis] = useState<VoiceAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [micAvailable, setMicAvailable] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rawAudioDataRef = useRef<Float32Array[]>([]);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const timerRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const analysisIntervalRef = useRef<number | null>(null);
  const previousEnergyRef = useRef<number>(0);
  const previousPitchRef = useRef<number>(0);

  // Auto-start recording when component mounts
  useEffect(() => {
    startContinuousRecording();

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (analysisIntervalRef.current) {
        clearInterval(analysisIntervalRef.current);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  const startContinuousRecording = async () => {
    try {
      setError(null);
      
      // Check if browser supports getUserMedia
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Your browser does not support microphone access. Please use Chrome, Firefox, or Edge.');
      }
      
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      streamRef.current = stream;
      setMicAvailable(true);

      // Don't specify sample rate - let it use browser default to avoid sample-rate mismatch
      const audioContext = new AudioContext();
      audioContextRef.current = audioContext;

      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 2048;
      analyserRef.current = analyser;

      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);

      // Create script processor for raw audio capture
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;
      rawAudioDataRef.current = [];

      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        const audioData = new Float32Array(inputData);
        rawAudioDataRef.current.push(audioData);
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      setIsRecording(true);
      setRecordingTime(0);

      // Timer for continuous recording duration
      timerRef.current = window.setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

      // Wait 4 seconds before starting analysis (let audio accumulate)
      setTimeout(() => {
        // First analysis after 4 seconds
        performAnalysis();
        
        // Then auto-analyze every 5 seconds
        analysisIntervalRef.current = window.setInterval(() => {
          performAnalysis();
        }, 5000);
      }, 4000);

    } catch (err: any) {
      setMicAvailable(false);
      
      // Better error messages based on error type
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError('❌ Microphone access denied. Please click the 🔒 icon in your browser address bar and allow microphone access, then refresh.');
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setError('❌ No microphone found. Please connect a microphone and refresh the page.');
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        setError('❌ Microphone is being used by another application. Please close other apps using the microphone and refresh.');
      } else if (err.message) {
        setError(`❌ ${err.message}`);
      } else {
        setError('❌ Microphone not available. Please check your browser permissions and refresh the page.');
      }
      
      console.error('Error accessing microphone:', err);
    }
  };

  const resampleAudio = (audioData: Float32Array, fromRate: number, toRate: number): Float32Array => {
    if (fromRate === toRate) return audioData;
    
    const ratio = fromRate / toRate;
    const newLength = Math.round(audioData.length / ratio);
    const result = new Float32Array(newLength);
    
    for (let i = 0; i < newLength; i++) {
      const sourceIndex = i * ratio;
      const index = Math.floor(sourceIndex);
      const fraction = sourceIndex - index;
      
      if (index + 1 < audioData.length) {
        // Linear interpolation
        result[i] = audioData[index] * (1 - fraction) + audioData[index + 1] * fraction;
      } else {
        result[i] = audioData[index];
      }
    }
    
    return result;
  };

  const performAnalysis = async () => {
    if (rawAudioDataRef.current.length === 0 || isAnalyzing) {
      console.log('⏭️ Skipping analysis - no data or already analyzing');
      return;
    }

    setIsAnalyzing(true);

    try {
      // Combine all raw audio data
      const totalLength = rawAudioDataRef.current.reduce((sum, arr) => sum + arr.length, 0);
      
      // Get actual sample rate
      const actualSampleRate = audioContextRef.current?.sampleRate || 48000;
      const duration = totalLength / actualSampleRate;
      
      // Need at least 1 second
      if (duration < 1.0) {
        console.log(`⏭️ Skipping - audio too short: ${duration.toFixed(2)}s`);
        setIsAnalyzing(false);
        return;
      }
      
      // Use only the most recent 3 seconds for analysis (for more responsive updates)
      const samplesToUse = Math.min(totalLength, actualSampleRate * 3);
      const startIndex = totalLength - samplesToUse;
      
      const combinedData = new Float32Array(totalLength);
      let offset = 0;
      for (const chunk of rawAudioDataRef.current) {
        combinedData.set(chunk, offset);
        offset += chunk.length;
      }
      
      // Extract recent audio
      const recentAudio = combinedData.slice(startIndex);
      const actualDuration = recentAudio.length / actualSampleRate;
      
      console.log(`📊 Using last ${actualDuration.toFixed(2)}s of audio (${recentAudio.length} samples at ${actualSampleRate} Hz)`);
      
      // Resample to 16000 Hz for model
      const resampledData = resampleAudio(recentAudio, actualSampleRate, 16000);
      console.log(`🔄 Resampled to ${resampledData.length} samples at 16000 Hz`);
      
      // Convert to WAV blob
      const wavBlob = createWavBlob(resampledData, 16000);
      console.log(`💾 Created WAV: ${wavBlob.size} bytes`);
      
      // Call the API
      const analysisResult = await analyzeVoiceStressWithAPI(wavBlob);
      console.log('📊 Raw Analysis Result:', analysisResult);

      // Detect sudden voice changes (stress indicator)
      const currentEnergy = analysisResult.audio_features?.rms_energy || 0;
      const energyChange = previousEnergyRef.current > 0 
        ? Math.abs(currentEnergy - previousEnergyRef.current) / previousEnergyRef.current 
        : 0;
      
      previousEnergyRef.current = currentEnergy;

      // Boost for sudden changes (>30% energy change = stress)
      const suddenChangeBoost = energyChange > 0.3 ? 15 : 0;
      console.log(`⚡ Energy change: ${(energyChange * 100).toFixed(1)}%, boost: +${suddenChangeBoost}`);

      // Fine-tune to 45-65 range for better display
      const rawScore = analysisResult.overall_stress_score;
      const normalizedScore = Math.round(45 + (rawScore / 100) * 20 + suddenChangeBoost);
      const finalScore = Math.min(65, Math.max(45, normalizedScore));
      
      // Apply same normalization to individual scores
      const mlScore = Math.round(45 + (analysisResult.ml_score / 100) * 20);
      const mathScore = Math.round(45 + (analysisResult.mathematical_score / 100) * 20);

      console.log(`📈 Score adjustment: ${rawScore} → ${finalScore} (45-65 range)`);

      // Update UI immediately with adjusted scores
      const newAnalysis = {
        ...analysisResult,
        overall_stress_score: finalScore,
        ml_score: Math.min(65, Math.max(45, mlScore)),
        mathematical_score: Math.min(65, Math.max(45, mathScore)),
        id: Date.now().toString(),
        created_at: new Date().toISOString()
      } as VoiceAnalysis;
      
      console.log('✅ Setting analysis state:', newAnalysis);
      setAnalysis(newAnalysis);

      // Save to Supabase in background
      supabase
        .from('voice_analyses')
        .insert([analysisResult])
        .select()
        .maybeSingle()
        .then(({ error }) => {
          if (error) {
            console.error('Error saving analysis:', error);
          }
        })
        .catch((err) => {
          console.error('Error saving to database:', err);
        });

      // Clear old audio - keep only last 5 seconds for next analysis
      const samplesToKeep = actualSampleRate * 5;
      if (totalLength > samplesToKeep) {
        const samplesPerChunk = rawAudioDataRef.current[0]?.length || 4096;
        const chunksToKeep = Math.ceil(samplesToKeep / samplesPerChunk);
        rawAudioDataRef.current = rawAudioDataRef.current.slice(-chunksToKeep);
        console.log(`🗑️ Cleared old audio, keeping last 5 seconds`);
      }
    } catch (error) {
      console.error('❌ Analysis error:', error);
      // Silent fail - just clear analyzing state and keep previous analysis
    } finally {
      // ALWAYS clear analyzing state, even on error
      setIsAnalyzing(false);
    }
  };

  const createWavBlob = (audioData: Float32Array, sampleRate: number): Blob => {
    const numChannels = 1;
    const bitDepth = 16;
    
    // Convert float32 to int16
    const samples = new Int16Array(audioData.length);
    for (let i = 0; i < audioData.length; i++) {
      const s = Math.max(-1, Math.min(1, audioData[i]));
      samples[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    
    const dataLength = samples.length * 2;
    const buffer = new ArrayBuffer(44 + dataLength);
    const view = new DataView(buffer);
    
    // Write WAV header
    const writeString = (offset: number, string: string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };
    
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + dataLength, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM
    view.setUint16(22, numChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * numChannels * (bitDepth / 8), true);
    view.setUint16(32, numChannels * (bitDepth / 8), true);
    view.setUint16(34, bitDepth, true);
    writeString(36, 'data');
    view.setUint32(40, dataLength, true);
    
    // Write audio data
    for (let i = 0; i < samples.length; i++) {
      view.setInt16(44 + i * 2, samples[i], true);
    }
    
    return new Blob([buffer], { type: 'audio/wav' });
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="w-full space-y-8">
      {/* Main Recording Card */}
      <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
        <div className="flex items-center justify-center mb-6">
          <div className={`
            flex items-center space-x-3 px-6 py-3 rounded-full
            ${micAvailable ? 'bg-gray-200' : 'bg-gray-100'}
          `}>
            <Mic className={`
              ${micAvailable ? 'text-gray-700 animate-pulse' : 'text-gray-400'}
            `} size={24} />
            <span className={`font-semibold ${micAvailable ? 'text-gray-800' : 'text-gray-600'}`}>
              {micAvailable ? 'Live Monitoring Active' : 'Microphone Not Available'}
            </span>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        <div className="flex flex-col items-center space-y-6">
          {/* Always show waveform when recording */}
          {isRecording && (
            <>
              <div className="w-full">
                <AudioWaveform
                  analyser={analyserRef.current}
                  isRecording={isRecording}
                />
              </div>

              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Activity className="w-5 h-5 text-gray-600 animate-pulse" />
                  <span className="text-lg font-semibold text-gray-700">
                    Monitoring: {formatTime(recordingTime)}
                  </span>
                </div>
                {isAnalyzing && (
                  <div className="flex items-center space-x-2 px-4 py-2 bg-gray-100 rounded-lg">
                    <Loader2 className="w-4 h-4 text-gray-700 animate-spin" />
                    <span className="text-sm text-gray-800 font-medium">Analyzing...</span>
                  </div>
                )}
              </div>
            </>
          )}

          {!isRecording && !micAvailable && (
            <div className="text-center space-y-4 py-8">
              <div className="w-20 h-20 mx-auto bg-gray-100 rounded-full flex items-center justify-center">
                <Mic size={40} className="text-gray-400" />
              </div>
              <p className="text-gray-600 font-medium">
                Waiting for microphone access...
              </p>
              <p className="text-sm text-gray-500">
                Please grant microphone permission to start live voice monitoring
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Analysis Results */}
      {analysis && (
        <div className="space-y-4">
          <VoiceStressDisplay analysis={analysis} />

          <div className="text-center text-sm text-gray-500">
            Continuous monitoring updates every 5 seconds
          </div>
        </div>
      )}
    </div>
  );
}
