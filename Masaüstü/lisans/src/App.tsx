import { useState } from 'react';
import { Bot, ShieldCheck } from 'lucide-react';
import { LanguageSelector } from './components/LanguageSelector';
import { LicenseForm } from './components/LicenseForm';
import { AdminPanel } from './components/AdminPanel';
import { Language } from './translations';

function App() {
  const [language, setLanguage] = useState<Language>('en');
  const [showAdmin, setShowAdmin] = useState(false);

  if (showAdmin) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
        <div className="fixed top-6 left-6 z-50">
          <button
            onClick={() => setShowAdmin(false)}
            className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-all backdrop-blur-sm border border-white/20 text-white"
          >
            <Bot className="w-5 h-5" />
            <span className="text-sm font-medium">Back to Home</span>
          </button>
        </div>
        <AdminPanel language={language} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 relative overflow-hidden">
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4wMyI+PHBhdGggZD0iTTM2IDM0djItaDJ2LTJoLTJ6bTAtNHYyaDJ2LTJoLTJ6bTAtNHYyaDJ2LTJoLTJ6bTAtNHYyaDJ2LTJoLTJ6bTAtNHYyaDJ2LTJoLTJ6bTAtNHYyaDJ2LTJoLTJ6bTAtNHYyaDJ2LTJoLTJ6bTAtNHYyaDJ2LTJoLTJ6bTAtNHYyaDJ2LTJoLTJ6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-30"></div>

      <nav className="relative z-10 flex items-center justify-between px-6 py-6">
        <a 
          href="https://planc.space" 
          target="_blank" 
          rel="noopener noreferrer"
          className="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer"
        >
          <img
            src="https://pbs.twimg.com/profile_images/1973360241547837441/zmewfn7J_400x400.jpg"
            alt="PlanC Logo"
            className="w-12 h-12 rounded-full border-2 border-blue-500 shadow-lg"
          />
          <div>
            <h1 className="text-xl font-bold text-white">PlanC Trade Bot</h1>
            <p className="text-xs text-gray-400">Professional Trading Automation</p>
          </div>
        </a>

        <div className="flex items-center gap-4">
          <button
            onClick={() => setShowAdmin(true)}
            className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-all backdrop-blur-sm border border-white/20"
            title="Admin Panel"
          >
            <ShieldCheck className="w-5 h-5 text-blue-400" />
          </button>
          <LanguageSelector currentLanguage={language} onLanguageChange={setLanguage} />
        </div>
      </nav>

      <main className="relative z-10 container mx-auto px-6 py-12">
        <a 
          href="https://planc.space" 
          target="_blank" 
          rel="noopener noreferrer"
          className="block text-center mb-16 hover:opacity-90 transition-opacity cursor-pointer"
        >
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-700 rounded-2xl mb-6 shadow-2xl">
            <Bot className="w-12 h-12 text-white" />
          </div>
          <h2 className="text-5xl md:text-6xl font-bold text-white mb-4 tracking-tight">
            PlanC Trade Bot
          </h2>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Professional Trading Automation with Advanced AI Technology
          </p>
        </a>

        <LicenseForm language={language} />

        <div className="mt-16 text-center">
          <div className="inline-flex items-center gap-2 px-6 py-3 bg-white/5 backdrop-blur-sm border border-white/10 rounded-full">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-300">Secure & Automated License Management</span>
          </div>
        </div>
      </main>

      <footer className="relative z-10 border-t border-gray-800 mt-20">
        <div className="container mx-auto px-6 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm">
              <Bot className="w-4 h-4" />
              <span>PlanC Trade Bot 2025</span>
            </div>
            <div className="text-gray-500 text-xs">
              Powered by PLANC SPACE
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
