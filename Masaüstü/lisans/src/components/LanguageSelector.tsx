import { Globe } from 'lucide-react';
import { languages, Language } from '../translations';

interface LanguageSelectorProps {
  currentLanguage: Language;
  onLanguageChange: (lang: Language) => void;
}

export function LanguageSelector({ currentLanguage, onLanguageChange }: LanguageSelectorProps) {
  return (
    <div className="relative group">
      <button className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-all backdrop-blur-sm border border-white/20">
        <Globe className="w-5 h-5 text-white" />
        <span className="text-sm font-medium text-white">
          {languages.find(l => l.code === currentLanguage)?.name}
        </span>
      </button>

      <div className="absolute top-full right-0 mt-2 w-64 bg-gray-900 rounded-xl shadow-2xl border border-gray-700 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 max-h-[400px] overflow-y-auto">
        <div className="p-2">
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => onLanguageChange(lang.code)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all ${
                currentLanguage === lang.code
                  ? 'bg-blue-600 text-white'
                  : 'hover:bg-gray-800 text-gray-200'
              }`}
            >
              <span className="text-xl">{lang.flag}</span>
              <span className="text-sm font-medium">{lang.name}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
