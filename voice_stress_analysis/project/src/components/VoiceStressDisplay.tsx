import { Brain, Calculator, Smile, Clock } from 'lucide-react';
import { StressGauge } from './StressGauge';
import { MetricCard } from './MetricCard';
import { VoiceAnalysis } from '../lib/supabase';

interface VoiceStressDisplayProps {
  analysis: VoiceAnalysis;
}

const emotionEmojis: Record<string, string> = {
  'Happy': '😊',
  'Sad': '😢',
  'Angry': '😠',
  'Anxious': '😰',
  'Calm': '😌',
  'Excited': '🤩',
  'Neutral': '😐',
  'Stressed': '😣'
};

export function VoiceStressDisplay({ analysis }: VoiceStressDisplayProps) {
  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          Real-Time Analysis Results
        </h2>

        {/* Main Stress Gauge */}
        <div className="flex justify-center mb-8">
          <StressGauge
            score={analysis.overall_stress_score}
            level={analysis.stress_level}
            size="large"
          />
        </div>

        {/* Score Breakdown - Prominent Display */}
        <div className="mb-6 p-6 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl border-2 border-gray-300">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 text-center">
            Score Breakdown
          </h3>
          <div className="grid grid-cols-3 gap-4">
            {/* ML Score */}
            <div className="bg-white rounded-lg p-4 text-center shadow-sm">
              <div className="flex justify-center mb-2">
                <Brain size={28} className="text-gray-700" />
              </div>
              <div className="text-3xl font-bold text-gray-700 mb-1">
                {analysis.ml_score}
                <span className="text-lg text-gray-500">/100</span>
              </div>
              <div className="text-xs font-semibold text-gray-600 uppercase">ML Score</div>
            </div>

            {/* Mathematical Score */}
            <div className="bg-white rounded-lg p-4 text-center shadow-sm">
              <div className="flex justify-center mb-2">
                <Calculator size={28} className="text-gray-700" />
              </div>
              <div className="text-3xl font-bold text-gray-700 mb-1">
                {analysis.mathematical_score}
                <span className="text-lg text-gray-500">/100</span>
              </div>
              <div className="text-xs font-semibold text-gray-600 uppercase">Mathematical</div>
            </div>

            {/* Weighted Combined Score (70% ML + 30% Math) */}
            <div className="bg-gradient-to-br from-gray-700 to-gray-900 rounded-lg p-4 text-center shadow-md">
              <div className="text-xs font-semibold text-white mb-2 uppercase">Weighted</div>
              <div className="text-4xl font-bold text-white mb-1">
                {analysis.overall_stress_score}
                <span className="text-lg text-white/80">/100</span>
              </div>
              <div className="text-xs font-medium text-white/90">70% ML + 30% Math</div>
            </div>
          </div>
        </div>

        {/* Additional Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <MetricCard
            title="Emotion Detected"
            value={`${emotionEmojis[analysis.emotion_detected] || '😐'} ${analysis.emotion_detected}`}
            icon={Smile}
            color="#4b5563"
          />
          <MetricCard
            title="Recording Duration"
            value={`${analysis.duration}s`}
            icon={Clock}
            color="#4b5563"
          />
        </div>

        <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-800">
            <span className="font-semibold">Analysis Method:</span> Combines ML-based pattern recognition
            with mathematical signal processing for comprehensive stress detection from voice patterns,
            pitch variations, and speech characteristics.
          </p>
        </div>
      </div>
    </div>
  );
}
