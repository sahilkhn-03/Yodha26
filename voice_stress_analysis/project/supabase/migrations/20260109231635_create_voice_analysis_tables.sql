/*
  # Voice Stress Analysis Database Schema

  1. New Tables
    - `voice_analyses`
      - `id` (uuid, primary key) - Unique identifier for each analysis
      - `created_at` (timestamptz) - Timestamp when analysis was created
      - `duration` (integer) - Recording duration in seconds
      - `overall_stress_score` (integer) - Overall stress score (0-100)
      - `stress_level` (text) - Categorical stress level (Low/Moderate/High)
      - `emotion_detected` (text) - Primary emotion detected
      - `ml_score` (integer) - ML-based stress score
      - `mathematical_score` (integer) - Mathematical analysis score
      - `audio_features` (jsonb) - Additional audio features and metadata
  
  2. Security
    - Enable RLS on `voice_analyses` table
    - Add policy for anyone to insert their own analyses
    - Add policy for anyone to read all analyses (for demo purposes)
*/

CREATE TABLE IF NOT EXISTS voice_analyses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz DEFAULT now(),
  duration integer NOT NULL DEFAULT 0,
  overall_stress_score integer NOT NULL DEFAULT 0,
  stress_level text NOT NULL DEFAULT 'Low',
  emotion_detected text NOT NULL DEFAULT 'Neutral',
  ml_score integer NOT NULL DEFAULT 0,
  mathematical_score integer NOT NULL DEFAULT 0,
  audio_features jsonb DEFAULT '{}'::jsonb
);

ALTER TABLE voice_analyses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can insert voice analyses"
  ON voice_analyses
  FOR INSERT
  TO anon
  WITH CHECK (true);

CREATE POLICY "Anyone can read voice analyses"
  ON voice_analyses
  FOR SELECT
  TO anon
  USING (true);