import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export interface VoiceAnalysis {
  id?: string;
  created_at?: string;
  duration: number;
  overall_stress_score: number;
  stress_level: 'Low' | 'Moderate' | 'High';
  emotion_detected: string;
  ml_score: number;
  mathematical_score: number;
  audio_features?: Record<string, unknown>;
}
