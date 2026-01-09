import React, { useEffect, useRef } from 'react';

interface CameraDisplayProps {
  isCameraEnabled: boolean;
  onCameraToggle: () => void;
  onMetricsUpdate?: (metrics: {
    eye_openness: number;
    brow_tension: number;
    jaw_tension: number;
    facial_asymmetry: number;
    head_motion: number;
    facial_stress_score: number;
  }) => void;
}

export function CameraDisplay({ isCameraEnabled, onCameraToggle, onMetricsUpdate }: CameraDisplayProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const sendIntervalRef = useRef<number | null>(null);
  const [overlaySrc, setOverlaySrc] = React.useState<string | null>(null);
  const prevMetricsRef = useRef<{
    eye_openness: number;
    brow_tension: number;
    jaw_tension: number;
    facial_asymmetry: number;
    head_motion: number;
    facial_stress_score: number;
  } | null>(null);

  // Initialize camera and WebSocket when camera turns on
  useEffect(() => {
    let stream: MediaStream | null = null;
    let running = false;

    async function startCamera() {
      if (!videoRef.current) return;
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        // Setup WebSocket
        const ws = new WebSocket('ws://localhost:8000/ws/face-analysis');
        ws.onopen = () => {
          // Start sending frames at ~10 FPS
          running = true;
          startFrameLoop();
        };
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            // Backend returns metrics; apply light smoothing (EMA)
            const alpha = 0.3;
            const prev = prevMetricsRef.current;
            const smoothed = {
              eye_openness: prev ? alpha * data.eye_openness + (1 - alpha) * prev.eye_openness : data.eye_openness,
              brow_tension: prev ? alpha * data.brow_tension + (1 - alpha) * prev.brow_tension : data.brow_tension,
              jaw_tension: prev ? alpha * data.jaw_tension + (1 - alpha) * prev.jaw_tension : data.jaw_tension,
              facial_asymmetry: prev ? alpha * (data.facial_stress_score * 0.1) + (1 - alpha) * prev.facial_asymmetry : data.facial_stress_score * 0.1,
              head_motion: prev ? alpha * data.head_motion + (1 - alpha) * prev.head_motion : data.head_motion,
              facial_stress_score: prev ? alpha * data.facial_stress_score + (1 - alpha) * prev.facial_stress_score : data.facial_stress_score,
            };
            prevMetricsRef.current = smoothed;
            onMetricsUpdate?.(smoothed);
            if (data.frame_overlay && typeof data.frame_overlay === 'string') {
              setOverlaySrc(data.frame_overlay);
            }
          } catch (e) {
            // Ignore malformed messages
          }
        };
        ws.onerror = () => {
          // Fail softly; don't block UI
        };
        wsRef.current = ws;
      } catch (err) {
        console.error('Camera start error', err);
      }
    }

    function startFrameLoop() {
      if (!videoRef.current) return;
      const canvas = canvasRef.current || document.createElement('canvas');
      canvas.width = videoRef.current.videoWidth || 640;
      canvas.height = videoRef.current.videoHeight || 480;
      const ctx = canvas.getContext('2d');
      canvasRef.current = canvas;
      // Send every ~100ms
      sendIntervalRef.current = window.setInterval(() => {
        if (!running || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        if (!videoRef.current || !ctx) return;
        ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
        const payload = {
          frame: dataUrl,
          timestamp: Date.now(),
        };
        try {
          wsRef.current.send(JSON.stringify(payload));
        } catch (e) {
          // Ignore send errors
        }
      }, 100);
    }

    function stopCamera() {
      running = false;
      if (sendIntervalRef.current !== null) {
        clearInterval(sendIntervalRef.current);
        sendIntervalRef.current = null;
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        try { wsRef.current.close(); } catch {}
      }
      setOverlaySrc(null);
      if (stream) {
        stream.getTracks().forEach((t) => t.stop());
        stream = null;
      }
    }

    if (isCameraEnabled) {
      startCamera();
    }

    return () => {
      stopCamera();
    };
    // Only respond to isCameraEnabled changes
  }, [isCameraEnabled, onMetricsUpdate]);

  return (
    <section className="relative rounded-2xl border border-gray-300 bg-gray-200 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-300 bg-gray-100">
        <h2 className="text-sm font-medium text-gray-700">Camera</h2>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onCameraToggle}
            className={`text-xs px-3 py-1 rounded-md border transition-colors ${
              isCameraEnabled
                ? 'bg-gray-800 text-white border-gray-800'
                : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
            }`}
          >
            Camera: {isCameraEnabled ? 'On' : 'Off'}
          </button>
        </div>
      </div>

      {/* Square camera area */}
      <div className="relative w-full max-w-md mx-auto aspect-square">
        {/* Placeholder camera surface */}
        {!isCameraEnabled && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-sm text-gray-600">Camera off</span>
          </div>
        )}
        {isCameraEnabled && (
          <>
            <video ref={videoRef} className="absolute inset-0 w-full h-full object-cover" muted playsInline />
            {overlaySrc && (
              <img src={overlaySrc} alt="mesh overlay" className="absolute inset-0 w-full h-full object-cover" />
            )}
            {/* Offscreen canvas used for frame capture */}
            <canvas ref={canvasRef} className="hidden" />
          </>
        )}
      </div>
    </section>
  );
}
