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
  const [ecgData, setEcgData] = useState<number[]>([]);
  const [currentBPM, setCurrentBPM] = useState<number>(0);
  const [bloodPressure, setBloodPressure] = useState({ systolic: 0, diastolic: 0 });
  const [mlPrediction, setMlPrediction] = useState<string>('--');
  const [stressScore, setStressScore] = useState<number>(0);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const maxDataPoints = 120;

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket('ws://localhost:8001/ws/heartbeat');
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      console.log('ECG WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data: ECGData = JSON.parse(event.data);
      if (data.type === 'connected') return;

      // Update metrics
      setCurrentBPM(data.bpm);
      setBloodPressure({ systolic: data.systolic, diastolic: data.diastolic });
      setMlPrediction(data.prediction || '--');
      setStressScore(data.stress_score || 0);

      // Generate ECG waveform point
      const ecgPoint = generateECGPoint(data.bpm, ecgData.length);
      setEcgData((prev) => {
        const updated = [...prev, ecgPoint];
        return updated.slice(-maxDataPoints);
      });
    };

    ws.onerror = () => {
      setIsConnected(false);
      console.error('ECG WebSocket error');
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('ECG WebSocket closed');
    };

    return () => {
      ws.close();
    };
  }, []);

  // Generate ECG waveform
  function generateECGPoint(bpm: number, index: number): number {
    const samplesPerBeat = 25;
    const beatProgress = (index % samplesPerBeat) / samplesPerBeat;
    const amplitudeScale = 0.5 + bpm / 60;

    let amplitude = 0;
    if (beatProgress < 0.1) {
      amplitude = Math.sin(beatProgress * 10 * Math.PI) * 35 * amplitudeScale;
    } else if (beatProgress < 0.3) {
      if (beatProgress < 0.2) {
        amplitude = -50 * amplitudeScale;
      } else if (beatProgress < 0.25) {
        amplitude = 150 * amplitudeScale;
      } else {
        amplitude = -45 * amplitudeScale;
      }
    } else if (beatProgress < 0.5) {
      amplitude = Math.sin((beatProgress - 0.3) * 5 * Math.PI) * 40 * amplitudeScale;
    }

    const noiseLevel = 3 + bpm / 50;
    return amplitude + (Math.random() * 2 - 1) * noiseLevel;
  }

  // Draw ECG canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const draw = () => {
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

      // Draw waveform
      if (ecgData.length > 1) {
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = 2;
        ctx.beginPath();

        const xStep = canvas.width / maxDataPoints;
        const yCenter = canvas.height / 2;

        for (let i = 0; i < ecgData.length; i++) {
          const x = i * xStep;
          const y = yCenter - ecgData[i];

          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.stroke();
      }
    };

    const animationId = requestAnimationFrame(function animate() {
      draw();
      requestAnimationFrame(animate);
    });

    return () => cancelAnimationFrame(animationId);
  }, [ecgData]);

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-red-50 rounded-lg">
            <Activity className="w-6 h-6 text-red-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Live ECG Monitor</h3>
            <p className="text-sm text-gray-500">Real-time electrocardiogram with ML prediction</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-600">{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      {/* ECG Waveform */}
      <div className="mb-6 bg-gray-50 rounded-xl p-4 border border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-gray-700">ELECTROCARDIOGRAM</span>
          <div className="flex items-center gap-2">
            <Heart className="w-5 h-5 text-red-600" />
            <span className="text-3xl font-bold text-gray-900">{currentBPM}</span>
            <span className="text-sm text-gray-500">BPM</span>
          </div>
        </div>
        <canvas
          ref={canvasRef}
          width={800}
          height={200}
          className="w-full rounded-lg"
        />
      </div>

      {/* Metrics Grid */}
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
          mlPrediction === 'Stress' 
            ? 'bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200' 
            : 'bg-gradient-to-br from-green-50 to-green-100 border-green-200'
        }`}>
          <div className="text-2xl font-bold text-gray-900">
            {mlPrediction} ({stressScore.toFixed(3)})
          </div>
          <div className="text-xs text-gray-600 mt-1">ML Prediction (Stress)</div>
        </div>
      </div>
    </div>
  );
}
