import { useEffect, useRef } from 'react';

interface AudioWaveformProps {
  analyser: AnalyserNode | null;
  isRecording: boolean;
}

export function AudioWaveform({ analyser, isRecording }: AudioWaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();

  useEffect(() => {
    if (!analyser || !isRecording || !canvasRef.current) {
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      if (!isRecording) return;

      animationRef.current = requestAnimationFrame(draw);
      analyser.getByteTimeDomainData(dataArray);

      // Gradient background
      const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
      gradient.addColorStop(0, '#f9fafb');
      gradient.addColorStop(1, '#f3f4f6');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Waveform with gradient
      const waveGradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
      waveGradient.addColorStop(0, '#6b7280');
      waveGradient.addColorStop(0.5, '#4b5563');
      waveGradient.addColorStop(1, '#374151');

      ctx.lineWidth = 3;
      ctx.strokeStyle = waveGradient;
      ctx.shadowBlur = 8;
      ctx.shadowColor = '#9ca3af';
      ctx.beginPath();

      const sliceWidth = canvas.width / bufferLength;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * canvas.height) / 2;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }

        x += sliceWidth;
      }

      ctx.lineTo(canvas.width, canvas.height / 2);
      ctx.stroke();

      // Reset shadow for next frame
      ctx.shadowBlur = 0;
    };

    draw();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [analyser, isRecording]);

  return (
    <div className="w-full bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl overflow-hidden border-2 border-blue-200 shadow-inner">
      <canvas
        ref={canvasRef}
        width={800}
        height={150}
        className="w-full h-40"
      />
    </div>
  );
}
