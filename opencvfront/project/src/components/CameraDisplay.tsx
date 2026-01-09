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
  const overlayCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const sendIntervalRef = useRef<number | null>(null);
  const animationFrameRef = useRef<number | null>(null);
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
      try {
        // Wait for React to render the video element
        await new Promise(resolve => requestAnimationFrame(resolve));
        await new Promise(resolve => requestAnimationFrame(resolve));
        
        if (!videoRef.current) {
          console.error('Video element not found in DOM');
          return;
        }
        
        console.log('Starting camera...');
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
        
        if (!videoRef.current) {
          console.error('Video ref lost during getUserMedia');
          return;
        }
        
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        running = true;
        
        // Draw loop: show raw video until backend sends annotated frames
        let lastAnnotatedFrame: HTMLImageElement | null = null;
        const drawLoop = () => {
          if (!running || !videoRef.current || !overlayCanvasRef.current) return;
          const ctx = overlayCanvasRef.current.getContext('2d');
          if (ctx && videoRef.current.videoWidth > 0) {
            overlayCanvasRef.current.width = videoRef.current.videoWidth;
            overlayCanvasRef.current.height = videoRef.current.videoHeight;
            
            // Draw raw video as base
            ctx.drawImage(videoRef.current, 0, 0);
            
            // If we have annotated frame from backend, draw it on top
            if (lastAnnotatedFrame) {
              ctx.drawImage(lastAnnotatedFrame, 0, 0, overlayCanvasRef.current.width, overlayCanvasRef.current.height);
            }
          }
          animationFrameRef.current = requestAnimationFrame(drawLoop);
        };
        drawLoop();
        
        // Setup WebSocket for real facial analysis
        const ws = new WebSocket('ws://localhost:8000/face-analysis');
        ws.onopen = () => {
          console.log('✅ Connected to facial stress analysis');
          console.log('🎥 Starting frame capture...');
          startFrameCapture();
        };
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.error) {
              console.error('Face analysis error:', data.error);
              return;
            }
            
            // Apply light smoothing (EMA)
            const alpha = 0.3;
            const prev = prevMetricsRef.current;
            const smoothed = {
              eye_openness: prev ? alpha * data.eye_openness + (1 - alpha) * prev.eye_openness : data.eye_openness,
              brow_tension: prev ? alpha * data.brow_tension + (1 - alpha) * prev.brow_tension : data.brow_tension,
              jaw_tension: prev ? alpha * data.jaw_tension + (1 - alpha) * prev.jaw_tension : data.jaw_tension,
              facial_asymmetry: prev ? alpha * data.facial_asymmetry + (1 - alpha) * prev.facial_asymmetry : data.facial_asymmetry,
              head_motion: prev ? alpha * data.head_motion + (1 - alpha) * prev.head_motion : data.head_motion,
              facial_stress_score: prev ? alpha * data.facial_stress_score + (1 - alpha) * prev.facial_stress_score : data.facial_stress_score,
            };
            prevMetricsRef.current = smoothed;
            onMetricsUpdate?.(smoothed);
            
            // Update annotated frame with mesh overlay
            if (data.frame_overlay) {
              const img = new Image();
              img.onload = () => {
                lastAnnotatedFrame = img;
              };
              img.src = data.frame_overlay;
            }
          } catch (e) {
            console.error('Error parsing face analysis data:', e);
          }
        };
        ws.onerror = () => {
          console.error('WebSocket connection error');
        };
        wsRef.current = ws;
      } catch (err) {
        console.error('Camera start error', err);
      }
    }

    function startFrameCapture() {
      // Send frames to backend for facial analysis
      console.log('📸 startFrameCapture called');
      const canvas = canvasRef.current || document.createElement('canvas');
      canvasRef.current = canvas;
      
      let framesSent = 0;
      sendIntervalRef.current = window.setInterval(() => {
        if (!running) {
          console.log('❌ Not running');
          return;
        }
        if (!wsRef.current) {
          console.log('❌ No WebSocket ref');
          return;
        }
        if (wsRef.current.readyState !== WebSocket.OPEN) {
          console.log('❌ WebSocket not open, state:', wsRef.current.readyState);
          return;
        }
        if (!videoRef.current || videoRef.current.videoWidth === 0) {
          console.log('❌ No video or video not ready');
          return;
        }
        
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        
        ctx.drawImage(videoRef.current, 0, 0);
        const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
        
        try {
          wsRef.current.send(JSON.stringify({
            frame: dataUrl,
            timestamp: Date.now(),
          }));
          framesSent++;
          if (framesSent === 1 || framesSent % 10 === 0) {
            console.log(`📤 Sent frame #${framesSent} (${dataUrl.length} bytes)`);
          }
        } catch (e) {
          console.error('Error sending frame:', e);
        }
      }, 200); // Reduced frequency to 200ms (~5 FPS) for smoother performance
    }

    function stopCamera() {
      running = false;
      if (animationFrameRef.current !== null) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
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
  }, [isCameraEnabled]);  // Removed onMetricsUpdate from dependencies

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
            <video ref={videoRef} className="hidden" muted playsInline />
            <canvas 
              ref={overlayCanvasRef} 
              className="absolute inset-0 w-full h-full object-cover"
            />
            {/* Hidden canvas for frame capture */}
            <canvas ref={canvasRef} className="hidden" />
          </>
        )}
      </div>
    </section>
  );
}
