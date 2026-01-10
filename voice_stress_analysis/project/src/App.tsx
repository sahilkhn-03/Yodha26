import { Activity } from 'lucide-react';
import { VoiceRecorder } from './components/VoiceRecorder';

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-100 to-gray-200">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-gradient-to-br from-gray-700 to-gray-900 p-4 rounded-2xl shadow-xl">
              <Activity size={40} className="text-white" />
            </div>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-gray-700 to-gray-900 bg-clip-text text-transparent mb-3">
            Live Voice Stress Monitor
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Real-time AI-powered voice analysis with continuous monitoring. 
            Automatically detects stress levels and emotions using advanced ML and mathematical models.
          </p>
          <div className="mt-4 flex items-center justify-center space-x-2 text-sm text-gray-500">
            <div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse"></div>
            <span>Always-on monitoring • Updates every 5 seconds</span>
          </div>
        </header>

        <main className="max-w-5xl mx-auto">
          <VoiceRecorder />
        </main>

        <footer className="text-center mt-16 pb-8">
          <p className="text-sm text-gray-500">
            Powered by Web Audio API • Advanced Signal Processing • Real-time ML Analysis
          </p>
        </footer>
      </div>
    </div>
  );
}

export default App;
