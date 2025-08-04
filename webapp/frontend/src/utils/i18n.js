import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translation files
import en from '../locales/en.json';
import hi from '../locales/hi.json';
import te from '../locales/te.json';
import hinglish from '../locales/hinglish.json';
import telgish from '../locales/telgish.json';

const resources = {
  en: { translation: en },
  hi: { translation: hi },
  te: { translation: te },
  hinglish: { translation: hinglish },
  telgish: { translation: telgish }
};

// Language mapping for backend API
export const getBackendLanguage = (frontendLang) => {
  const mapping = {
    'en': 'english',
    'hi': 'hindi',
    'te': 'telugu',
    'hinglish': 'hinglish',
    'telgish': 'telgish'
  };
  return mapping[frontendLang] || 'english';
};

// Voice language mapping for Web Speech API
export const getVoiceLanguage = (frontendLang) => {
  const mapping = {
    'en': 'en-US',
    'hi': 'hi-IN',
    'te': 'te-IN',
    'hinglish': 'en-IN', // Use Indian English for Hinglish
    'telgish': 'en-IN'   // Use Indian English for Telgish
  };
  return mapping[frontendLang] || 'en-US';
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    debug: false,
    
    interpolation: {
      escapeValue: false
    },
    
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
      lookupLocalStorage: 'i18nextLng', // Ensure localStorage key is consistent
      checkWhitelist: true,
      convertDetectedLanguage: (lng) => {
        // Ensure we return a supported language
        const supportedLngs = ['en', 'hi', 'te', 'hinglish', 'telgish'];
        return supportedLngs.includes(lng) ? lng : 'en';
      }
    },
    
    // Add whitelist to validate languages
    supportedLngs: ['en', 'hi', 'te', 'hinglish', 'telgish'],
    nonExplicitSupportedLngs: true
  });

export default i18n;
