import { useEffect, useRef } from 'react';
import { drawFaceMesh } from '../lib/faceMesh';

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
        console.log('🎥 Requesting camera access...');
        
        // Request camera access FIRST
        stream = await navigator.mediaDevices.getUserMedia({ 
          video: { 
            facingMode: 'user',
            width: { ideal: 640 },
            height: { ideal: 480 }
          }, 
          audio: false 
        });
        
        console.log('✅ Camera access granted');
        
        // Wait for React to render the video element
        await new Promise(resolve => setTimeout(resolve, 100));
        
        if (!videoRef.current) {
          console.error('❌ Video element not found in DOM');
          if (stream) {
            stream.getTracks().forEach(t => t.stop());
          }
          return;
        }
        
        console.log('📹 Attaching stream to video element...');
        console.log('📹 Attaching stream to video element...');
        videoRef.current.srcObject = stream;
        
        // Wait for video metadata to load
        await new Promise((resolve, reject) => {
          if (!videoRef.current) {
            reject(new Error('Video ref lost'));
            return;
          }
          videoRef.current.onloadedmetadata = resolve;
          videoRef.current.onerror = reject;
        });
        
        await videoRef.current.play();
        running = true;
        console.log('✅ Camera started successfully! Video dimensions:', 
          videoRef.current.videoWidth, 'x', videoRef.current.videoHeight);
        console.log('🔌 Backend will process face detection');
        
        // Store landmarks and optional feature estimates received from backend
        let currentLandmarks: Array<{ x: number; y: number; z: number }> | null = null;
        let currentFeatures: { avg_eye_aspect_ratio?: number; avg_eyebrow_tension?: number; jaw_drop?: number } | null = null;
        
        // Draw loop: show raw video with subtle face mesh overlay
        const drawLoop = () => {
          if (!running || !videoRef.current || !overlayCanvasRef.current) return;
          const ctx = overlayCanvasRef.current.getContext('2d');
          if (ctx && videoRef.current.videoWidth > 0) {
            overlayCanvasRef.current.width = videoRef.current.videoWidth;
            overlayCanvasRef.current.height = videoRef.current.videoHeight;
            
            // Draw raw video as base
            ctx.drawImage(videoRef.current, 0, 0);
            
            // Draw subtle face mesh overlay (with optional feature labels)
            if (currentLandmarks && currentLandmarks.length > 0) {
              drawFaceMesh(
                ctx,
                currentLandmarks,
                overlayCanvasRef.current.width,
                overlayCanvasRef.current.height,
                currentFeatures || undefined
              );
            }
          }
          animationFrameRef.current = requestAnimationFrame(drawLoop);
        };
        drawLoop();
        
        // Setup WebSocket for ML-based stress prediction (XGBoost - 77.3% accuracy)
        const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
        const wsProtocol = backendUrl.startsWith('https') ? 'wss' : 'ws';
        const wsUrl = backendUrl.replace(/^https?/, wsProtocol);
        const ws = new WebSocket(`${wsUrl}/ws/ml-stress-analysis`);
        ws.onopen = () => {
          console.log('✅ Connected to ML stress analysis (XGBoost - 77.3% accuracy)');
          console.log('🎥 Starting frame capture...');
          startFrameCapture();
        };
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.error) {
              console.error('ML stress analysis error:', data.error);
              return;
            }
            
            if (!data.success) {
              // No face detected - clear visualization
              console.log('⚠️ No face detected');
              currentLandmarks = null;
              currentFeatures = null;
              prevMetricsRef.current = null;
              onMetricsUpdate?.({
                eye_openness: 0,
                brow_tension: 0,
                jaw_tension: 0,
                facial_asymmetry: 0,
                head_motion: 0,
                facial_stress_score: 0,
              });
              return;
            }
            
            // Store landmarks from backend for visualization
            if (data.landmarks && data.landmarks.length > 0) {
              currentLandmarks = data.landmarks;
              console.log('📍 Received', currentLandmarks.length, 'landmarks from backend');
            } else {
              currentLandmarks = null;
            }

            // Store raw features for overlay labels (if present)
            if (data.features) {
              currentFeatures = {
                avg_eye_aspect_ratio: data.features.avg_eye_aspect_ratio,
                avg_eyebrow_tension: data.features.avg_eyebrow_tension,
                jaw_drop: data.features.jaw_drop,
              };
            } else {
              currentFeatures = null;
            }

            // Convert ML features to UI metrics - INTUITIVE SCALING
            const features = data.features || {};
            
            // Eye Aspect Ratio: LITERAL eye openness (high % = wide open, low % = closed)
            // Typical range: 0.15 (closed) to 0.40 (wide open)
            const earNormalized = Math.max(0, Math.min(1, (features.avg_eye_aspect_ratio - 0.15) / 0.25));
            const eyeOpenness = earNormalized * 100; // DIRECT: open eyes = high %, closed = low %
            
            // Brow tension: amplified for visibility
            const browTension = Math.min(100, Math.max(0, features.avg_eyebrow_tension * 500));
            
            // Jaw tension: amplified
            const jawTension = Math.min(100, Math.max(0, features.jaw_drop * 300));
            
            // Facial asymmetry: amplified
            const facialAsymmetry = Math.min(100, Math.max(0, Math.abs(features.left_ear - features.right_ear) * 2000));
            
            // Head motion: amplified significantly
            const headMotion = Math.min(100, Math.max(0, Math.abs(features.left_eyebrow_tension - features.right_eyebrow_tension) * 1000));
            
            const mlMetrics = {
              eye_openness: eyeOpenness,
              brow_tension: browTension,
              jaw_tension: jawTension,
              facial_asymmetry: facialAsymmetry,
              head_motion: headMotion,
              facial_stress_score: Math.min(100, Math.max(0, data.stress_score)),
            };
            
            console.log(`🧠 ML: ${data.stress_score.toFixed(1)}/100 (${data.stress_level})`);
            console.log(`📊 Metrics: Eye=${mlMetrics.eye_openness.toFixed(0)}% Brow=${mlMetrics.brow_tension.toFixed(0)}% Jaw=${mlMetrics.jaw_tension.toFixed(0)}% Motion=${mlMetrics.head_motion.toFixed(0)}%`);
            
            // Send directly without smoothing
            onMetricsUpdate?.(mlMetrics);
          } catch (e) {
            console.error('Error parsing ML stress data:', e);
          }
        };
        ws.onerror = () => {
          console.error('WebSocket connection error');
        };
        wsRef.current = ws;
      } catch (err) {
        console.error('❌ Camera initialization failed:', err);
        if (err instanceof Error) {
          console.error('Error details:', err.message);
        }
        // Clean up stream if it was created
        if (stream) {
          stream.getTracks().forEach(t => t.stop());
          stream = null;
        }
        alert(`Camera failed to start: ${err instanceof Error ? err.message : 'Unknown error'}. Please check browser permissions.`);
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
      if (stream) {
        stream.getTracks().forEach((t) => t.stop());
        stream = null;
      }
      
      // Clear metrics when camera is turned off
      prevMetricsRef.current = null;
      onMetricsUpdate?.({
        eye_openness: 0,
        brow_tension: 0,
        jaw_tension: 0,
        facial_asymmetry: 0,
        head_motion: 0,
        facial_stress_score: 0,
      });
    }

    if (isCameraEnabled) {
      startCamera();
    }

    return () => {
      stopCamera();
    };
    // Only respond to isCameraEnabled changes
  }, [isCameraEnabled]);

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
            {/* Video element must be rendered (not hidden) for stream to work properly */}
            <video 
              ref={videoRef} 
              className="absolute inset-0 w-full h-full object-cover opacity-0 pointer-events-none" 
              muted 
              playsInline 
              autoPlay
            />
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
