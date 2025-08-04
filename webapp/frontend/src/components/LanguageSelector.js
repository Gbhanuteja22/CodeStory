import React from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronDown, Volume2, VolumeX } from 'lucide-react';
import { voiceManager } from '../utils/voiceManager';
import { getBackendLanguage } from '../utils/i18n';

const languages = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'hi', name: 'हिंदी', flag: '🇮🇳' },
  { code: 'te', name: 'తెలుగు', flag: '🇮🇳' },
  { code: 'hinglish', name: 'Hinglish', flag: '🇮🇳' },
  { code: 'telgish', name: 'Telgish', flag: '🇮🇳' }
];

const LanguageSelector = ({ onLanguageChange, showVoiceOptions = false }) => {
  const { i18n, t } = useTranslation();
  const [isOpen, setIsOpen] = React.useState(false);
  const [showVoicePrefs, setShowVoicePrefs] = React.useState(false);
  const [voiceGender, setVoiceGender] = React.useState(() => 
    localStorage.getItem('voiceGender') || 'female'
  );

  const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[0];

  const handleLanguageChange = async (langCode) => {
    const oldLanguage = i18n.language;
    
    // Change UI language
    await i18n.changeLanguage(langCode);
    setIsOpen(false);
    
    // Store the backend language mapping
    const backendLanguage = getBackendLanguage(langCode);
    localStorage.setItem('selectedLanguage', backendLanguage);
    
    // If tutorial is already generated and language changed, trigger regeneration
    const taskId = localStorage.getItem('taskId');
    const currentTutorialLanguage = localStorage.getItem('tutorialLanguage');
    
    if (taskId && currentTutorialLanguage && currentTutorialLanguage !== backendLanguage) {
      if (onLanguageChange) {
        onLanguageChange(langCode, backendLanguage);
      }
    }
    
    // Test voice for the new language
    if (showVoiceOptions && voiceManager.isSupported) {
      const testText = langCode === 'en' ? 'Language changed to English' :
                      langCode === 'hi' ? 'भाषा बदल गई' :
                      langCode === 'te' ? 'భాష మార్చబడింది' :
                      langCode === 'hinglish' ? 'Language change हो गई' :
                      langCode === 'telgish' ? 'Language change అయ్యింది' :
                      'Language changed';
      
      // Quick voice test (optional)
      setTimeout(() => {
        voiceManager.speak(testText, langCode, { 
          gender: voiceGender,
          onError: () => console.log('Voice not available for', langCode)
        });
      }, 500);
    }
  };

  const handleVoiceGenderChange = (gender) => {
    setVoiceGender(gender);
    localStorage.setItem('voiceGender', gender);
    setShowVoicePrefs(false);
  };

  const testVoice = () => {
    const testTexts = {
      en: 'This is a voice test in English',
      hi: 'यह हिंदी में आवाज़ का परीक्षण है',
      te: 'ఇది తెలుగులో వాయిస్ టెస్ట్',
      hinglish: 'This is एक voice test में Hinglish',
      telgish: 'This is ఒక voice test లో Telgish'
    };
    
    const text = testTexts[i18n.language] || testTexts.en;
    voiceManager.speak(text, i18n.language, { gender: voiceGender });
  };

  React.useEffect(() => {
    const handleClickOutside = (event) => {
      if (!event.target.closest('.language-selector')) {
        setIsOpen(false);
        setShowVoicePrefs(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative language-selector">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        aria-label={t('languageSelector')}
      >
        <span>{currentLanguage.flag}</span>
        <span className="hidden sm:inline text-sm font-medium">{currentLanguage.name}</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-white border border-gray-300 rounded-lg shadow-lg z-50">
          {/* Language Options */}
          <div className="py-1">
            {languages.map((language) => (
              <button
                key={language.code}
                onClick={() => handleLanguageChange(language.code)}
                className={`w-full flex items-center gap-3 px-4 py-2 text-left hover:bg-gray-50 transition-colors ${
                  language.code === i18n.language ? 'bg-blue-50 text-blue-600' : 'text-gray-700'
                }`}
              >
                <span>{language.flag}</span>
                <span className="text-sm font-medium">{language.name}</span>
              </button>
            ))}
          </div>
          
          {/* Voice Options */}
          {showVoiceOptions && voiceManager.isSupported && (
            <>
              <div className="border-t border-gray-200 py-2">
                <div className="px-4 py-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Voice Settings</span>
                    <button
                      onClick={testVoice}
                      className="p-1 text-gray-500 hover:text-blue-600 transition-colors"
                      title="Test Voice"
                    >
                      <Volume2 className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <div className="mt-2 space-y-1">
                    <button
                      onClick={() => handleVoiceGenderChange('female')}
                      className={`w-full text-left px-2 py-1 text-sm rounded transition-colors ${
                        voiceGender === 'female' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'
                      }`}
                    >
                      👩 Female Voice
                    </button>
                    <button
                      onClick={() => handleVoiceGenderChange('male')}
                      className={`w-full text-left px-2 py-1 text-sm rounded transition-colors ${
                        voiceGender === 'male' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'
                      }`}
                    >
                      👨 Male Voice
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default LanguageSelector;
