import { useEffect, useRef, useState } from 'react';
import { Activity, Heart } from 'lucide-react';

interface ECGData {
  timestamp: string;
  bpm: number;
  systolic: number;
  diastolic: number;
  stress_level: number;
  variability: number;
  prediction?: string;
  confidence?: number;
  stress_score?: number;
}

export function ECGMonitor() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const ecgBufferRef = useRef<number[]>([]);
  const [currentBPM, setCurrentBPM] = useState<number>(72);
  const [bloodPressure, setBloodPressure] = useState({ systolic: 120, diastolic: 80 });
  const [mlPrediction, setMlPrediction] = useState<string>('--');
  const [stressScore, setStressScore] = useState<number>(0);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const maxDataPoints = 200;
  const ecgIndexRef = useRef<number>(0);
  const currentBpmRef = useRef<number>(72);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const maxReconnectAttempts = 10;

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket(`ws://${window.location.hostname}:8001/ws/heartbeat`);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        console.log('✅ ECG WebSocket connected');
      };

      ws.onmessage = (event) => {
        try {
          const data: ECGData = JSON.parse(event.data);
          if ((data as any).type === 'connected') return;

        console.log('📡 WebSocket Data:', {
          bpm: data.bpm,
          prediction: data.prediction,
          stress_score: data.stress_score,
          confidence: data.confidence
        });

        setCurrentBPM(data.bpm);
        currentBpmRef.current = data.bpm;
        if (data.systolic !== undefined && data.diastolic !== undefined) {
          setBloodPressure({ systolic: data.systolic, diastolic: data.diastolic });
        }
        
        // Handle prediction data
        if (data.prediction) {
          setMlPrediction(data.prediction);
          console.log('✅ ML Prediction updated:', data.prediction);
        }
        if (data.stress_score !== undefined && data.stress_score !== null) {
          setStressScore(data.stress_score);
          console.log('✅ Stress Score updated:', data.stress_score);
        }
      } catch (e) {
        console.error('❌ Malformed WS message', e);
        console.error('⚠ ECG WebSocket error');
      };
      
      ws.onclose = () => {
        setIsConnected(false);
        console.log('⚠ ECG WebSocket disconnected');
        
        // Automatic reconnection with exponential backoff
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          console.log(`🔄 Reconnecting in ${delay / 1000}s (attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})...`);
          reconnectAttemptsRef.current++;
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, delay);
        } else {
          console.error('❌ Max reconnection attempts reached. Please refresh the page.');
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setIsConnected(false);
    }
  };

  useEffect(() => {
    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Continuous ECG data generation loop
  useEffect(() => {
    const interval = setInterval(() => {
      const point = generateECGPoint(currentBpmRef.current, ecgIndexRef.current);
      ecgIndexRef.current++;
      
      ecgBufferRef.current = [...ecgBufferRef.current, point];
      if (ecgBufferRef.current.length > maxDataPoints) {
        ecgBufferRef.current.shift();
      }
    }, 33); // ~30 FPS for smooth waveform

    return () => clearInterval(interval);
  }, []);

  function generateECGPoint(bpm: number, index: number): number {
    // Calculate samples per beat with dynamic variation
    const baseSamplesPerBeat = Math.max(20, Math.round(60 / Math.max(30, bpm) * 30));
    
    // Enhanced Heart Rate Variability (HRV) - creates non-uniform beat spacing
    // Combines multiple frequencies for realistic variation
    const hrvFast = Math.sin(index * 0.08) * 0.12;  // Fast variation
    const hrvSlow = Math.sin(index * 0.015) * 0.18; // Slow breathing-related variation
    const hrvRandom = (Math.random() - 0.5) * 0.15; // Random beat-to-beat variation
    const totalHRV = hrvFast + hrvSlow + hrvRandom;
    
    // Apply HRV to create non-uniform timing
    const samplesPerBeat = baseSamplesPerBeat * (1 + totalHRV);
    const adjustedPhase = (index % samplesPerBeat) / samplesPerBeat;
    
    // Dynamic amplitude scaling - varies with stress/activity
    const baseScale = 35 * (bpm / 60);
    const amplitudeVariation = Math.sin(index * 0.01) * 0.15 + 1; // ±15% variation
    const scale = baseScale * amplitudeVariation;
    
    // Multi-frequency baseline wander (respiratory + muscle movement)
    const respiratoryDrift = Math.sin(index * 0.018) * 4;
    const muscleNoise = Math.sin(index * 0.041) * 1.5;
    const baselineWander = respiratoryDrift + muscleNoise;
    
    let amplitude = 0;
    
    // Occasional premature beat or irregular rhythm (5% chance)
    const isIrregular = Math.random() < 0.05;
    const irregularityFactor = isIrregular ? 0.7 + Math.random() * 0.4 : 1.0;
    
    // P wave (atrial depolarization) - 0-15% of cycle
    if (adjustedPhase < 0.15) {
      const pPhase = adjustedPhase / 0.15;
      const pVariability = 0.85 + Math.random() * 0.3; // 85-115% amplitude
      amplitude = Math.sin(pPhase * Math.PI) * (scale * 0.25) * pVariability * irregularityFactor;
    }
    // PR segment (isoelectric) - 15-20%
    else if (adjustedPhase < 0.20) {
      amplitude = (Math.random() - 0.5) * 2;
    }
    // Q wave (small negative deflection) - 20-22%
    else if (adjustedPhase < 0.22) {
      const qVariability = 0.9 + Math.random() * 0.2;
      amplitude = -scale * 0.15 * qVariability;
    }
    // R wave (large positive spike) - 22-26%
    else if (adjustedPhase < 0.26) {
      const rPhase = (adjustedPhase - 0.22) / 0.04;
      const rVariability = 0.9 + Math.random() * 0.2; // 90-110% amplitude
      amplitude = scale * 3.5 * Math.sin(rPhase * Math.PI) * rVariability * irregularityFactor;
    }
    // S wave (negative deflection) - 26-30%
    else if (adjustedPhase < 0.30) {
      const sPhase = (adjustedPhase - 0.26) / 0.04;
      const sVariability = 0.85 + Math.random() * 0.3;
      amplitude = -scale * 0.4 * Math.sin(sPhase * Math.PI) * sVariability;
    }
    // ST segment (isoelectric) - 30-45%
    else if (adjustedPhase < 0.45) {
      amplitude = (Math.random() - 0.5) * 2.5;
    }
    // T wave (ventricular repolarization) - 45-65%
    else if (adjustedPhase < 0.65) {
      const tPhase = (adjustedPhase - 0.45) / 0.20;
      const tVariability = 0.8 + Math.random() * 0.4; // 80-120% amplitude
      amplitude = Math.sin(tPhase * Math.PI) * (scale * 0.35) * tVariability * irregularityFactor;
    }
    // Baseline with variable noise
    else {
      amplitude = (Math.random() - 0.5) * 3;
    }
    
    // Enhanced physiological noise - scales with heart rate
    const physiologicalNoise = (Math.random() - 0.5) * (1.5 + bpm / 80);
    
    // Occasional artifacts (movement, electrical interference) - 2% chance
    const artifactNoise = Math.random() < 0.02 ? (Math.random() - 0.5) * 15 : 0;
    
    return amplitude + baselineWander + physiologicalNoise + artifactNoise;
  }

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let raf = 0;
    const draw = () => {
      // Clear canvas
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw grid
      ctx.strokeStyle = '#e5e7eb';
      ctx.lineWidth = 1;
      for (let x = 0; x < canvas.width; x += 20) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }
      for (let y = 0; y < canvas.height; y += 20) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }

      // Draw ECG waveform - SCROLLING from right to left
      if (ecgBufferRef.current.length > 1) {
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 2.5;
        ctx.shadowBlur = 3;
        ctx.shadowColor = '#000000';
        ctx.beginPath();
        
        const xStep = canvas.width / maxDataPoints;
        const yCenter = canvas.height / 2;
        
        // Draw from right to left for scrolling effect
        for (let i = 0; i < ecgBufferRef.current.length; i++) {
          const x = canvas.width - (ecgBufferRef.current.length - i) * xStep;
          const y = yCenter - ecgBufferRef.current[i];
          
          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.stroke();
        ctx.shadowBlur = 0;
      }

      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-red-50 rounded-lg">
            <Activity className="w-6 h-6 text-red-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Live ECG Monitor</h3>
            <p className="text-sm text-gray-500">Real-time electrocardiogram</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-600">{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      <div className="mb-6 bg-gray-50 rounded-xl p-4 border border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-gray-700">ELECTROCARDIOGRAM</span>
          <div className="flex items-center gap-2">
            <Heart className="w-5 h-5 text-red-600" />
            <span className="text-3xl font-bold text-gray-900">{currentBPM}</span>
            <span className="text-sm text-gray-500">BPM</span>
          </div>
        </div>
        <canvas ref={canvasRef} width={800} height={200} className="w-full rounded-lg" />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-xl p-4 text-center border border-red-200">
          <div className="text-3xl font-bold text-gray-900">{currentBPM}</div>
          <div className="text-xs text-gray-600 mt-1">Heart Rate (BPM)</div>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4 text-center border border-purple-200">
          <div className="flex items-baseline justify-center gap-1">
            <span className="text-3xl font-bold text-gray-900">{bloodPressure.systolic}</span>
            <span className="text-2xl text-gray-600">/</span>
            <span className="text-3xl font-bold text-gray-900">{bloodPressure.diastolic}</span>
          </div>
          <div className="text-xs text-gray-600 mt-1">Blood Pressure (mmHg)</div>
        </div>

        <div className={`rounded-xl p-4 text-center border ${
          mlPrediction === 'Stress' ? 'bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200' : 'bg-gradient-to-br from-green-50 to-green-100 border-green-200'
        }`}>
          <div className="text-2xl font-bold text-gray-900">{mlPrediction} ({stressScore.toFixed(3)})</div>
          <div className="text-xs text-gray-600 mt-1">ML Prediction (Stress)</div>
        </div>
      </div>
    </div>
  );
}
