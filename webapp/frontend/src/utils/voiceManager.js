import { getVoiceLanguage } from './i18n';

export class VoiceManager {
  constructor() {
    this.isSupported = 'speechSynthesis' in window;
    this.voices = [];
    this.currentUtterance = null;
    this.isPlaying = false;
    this.isPaused = false;
    this.eventListeners = {}; // For event emitter functionality
    
    if (this.isSupported) {
      this.loadVoices();
      // Reload voices when they change (some browsers load them async)
      speechSynthesis.addEventListener('voiceschanged', () => {
        this.loadVoices();
      });
    }
  }

  preprocessTextForSpeech(text, language) {
    // Remove markdown formatting for better speech
    let cleanedText = text
      .replace(/#{1,6}\s/g, '') // Remove headers
      .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold
      .replace(/\*(.*?)\*/g, '$1') // Remove italic
      .replace(/`(.*?)`/g, '$1') // Remove inline code
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Convert links to just text
      .replace(/```[\s\S]*?```/g, '') // Remove code blocks
      .replace(/^\s*[-*+]\s/gm, '') // Remove list bullets
      .replace(/^\s*\d+\.\s/gm, '') // Remove numbered list markers
      .replace(/\n{2,}/g, '. ') // Replace multiple newlines with pause
      .replace(/\n/g, ' ') // Replace single newlines with space
      .trim();

    // Language-specific text processing
    if (language === 'hi' || language === 'te') {
      // For Indian languages, add pauses after sentences
      cleanedText = cleanedText.replace(/([।॥])/g, '$1 ');
    }

    // Split long text into chunks for better speech synthesis
    if (cleanedText.length > 200) {
      const sentences = cleanedText.split(/[.।॥]/);
      cleanedText = sentences.slice(0, 3).join('. '); // Take first few sentences
    }

    return cleanedText;
  }

  getLanguageSpecificParams(language) {
    const params = {
      'hi': { rate: 0.8, pitch: 1.1 }, // Slower, slightly higher pitch for Hindi
      'te': { rate: 0.8, pitch: 1.0 }, // Slower rate for Telugu
      'en': { rate: 1.0, pitch: 1.0 }, // Normal for English
      'hinglish': { rate: 0.9, pitch: 1.0 }, // Slightly slower for mixed language
      'telgish': { rate: 0.9, pitch: 1.0 }
    };
    
    return params[language] || params['en'];
  }

  // Event emitter methods
  on(event, callback) {
    if (!this.eventListeners[event]) {
      this.eventListeners[event] = [];
    }
    this.eventListeners[event].push(callback);
  }

  off(event, callback) {
    if (!this.eventListeners[event]) return;
    this.eventListeners[event] = this.eventListeners[event].filter(cb => cb !== callback);
  }

  emit(event, data) {
    if (!this.eventListeners[event]) return;
    this.eventListeners[event].forEach(callback => callback(data));
  }

  loadVoices() {
    this.voices = speechSynthesis.getVoices();
  }

  getAvailableVoices(language, preferredGender = 'female') {
    if (!this.isSupported) return [];
    
    const voiceLang = getVoiceLanguage(language);
    
    // Find voices for the specified language
    let languageVoices = this.voices.filter(voice => 
      voice.lang.startsWith(voiceLang.substring(0, 2)) // Match language code (e.g., 'hi' for 'hi-IN')
    );
    
    // If no voices found for the language, fallback to English
    if (languageVoices.length === 0) {
      languageVoices = this.voices.filter(voice => 
        voice.lang.startsWith('en')
      );
    }
    
    // Group by gender (rough heuristic based on voice name)
    const femaleVoices = languageVoices.filter(voice => 
      this.isFemaleVoice(voice.name)
    );
    const maleVoices = languageVoices.filter(voice => 
      this.isMaleVoice(voice.name)
    );
    const neutralVoices = languageVoices.filter(voice => 
      !this.isFemaleVoice(voice.name) && !this.isMaleVoice(voice.name)
    );
    
    return {
      female: femaleVoices,
      male: maleVoices,
      neutral: neutralVoices,
      all: languageVoices
    };
  }

  isFemaleVoice(voiceName) {
    const femaleKeywords = [
      'female', 'woman', 'zira', 'helena', 'sabina', 'karen', 'moira',
      'tessa', 'veena', 'raveena', 'kendra', 'joanna', 'salli',
      'neerja', 'aditi', 'priya', 'shruti'
    ];
    return femaleKeywords.some(keyword => 
      voiceName.toLowerCase().includes(keyword)
    );
  }

  isMaleVoice(voiceName) {
    const maleKeywords = [
      'male', 'man', 'david', 'mark', 'richard', 'ryan', 'kevin',
      'matthew', 'justin', 'joey', 'geraint', 'rishi', 'anuj'
    ];
    return maleKeywords.some(keyword => 
      voiceName.toLowerCase().includes(keyword)
    );
  }

  getBestVoice(language, preferredGender = 'female') {
    const availableVoices = this.getAvailableVoices(language, preferredGender);
    
    // Try to get preferred gender first
    if (preferredGender === 'female' && availableVoices.female.length > 0) {
      return availableVoices.female[0];
    }
    if (preferredGender === 'male' && availableVoices.male.length > 0) {
      return availableVoices.male[0];
    }
    
    // Fallback to any available voice
    if (availableVoices.all.length > 0) {
      return availableVoices.all[0];
    }
    
    // Final fallback to default voice
    return this.voices.length > 0 ? this.voices[0] : null;
  }

  speak(text, language, options = {}) {
    if (!this.isSupported) {
      console.warn('Speech synthesis not supported');
      return;
    }

    // Stop any current speech
    this.stop();

    // Clean text for better voice synthesis
    const cleanedText = this.preprocessTextForSpeech(text, language);

    const utterance = new SpeechSynthesisUtterance(cleanedText);
    const voice = this.getBestVoice(language, options.gender || 'female');
    
    if (voice) {
      utterance.voice = voice;
    }
    
    // Adjust speech parameters based on language
    const speechParams = this.getLanguageSpecificParams(language);
    utterance.rate = options.rate || speechParams.rate;
    utterance.pitch = options.pitch || speechParams.pitch;
    utterance.volume = options.volume || 1.0;
    
    // Set language
    utterance.lang = getVoiceLanguage(language);
    
    utterance.onstart = () => {
      this.isPlaying = true;
      this.isPaused = false;
      this.emit('start');
      if (options.onStart) options.onStart();
    };
    
    utterance.onend = () => {
      this.isPlaying = false;
      this.isPaused = false;
      this.currentUtterance = null;
      this.emit('end');
      if (options.onEnd) options.onEnd();
    };
    
    utterance.onerror = (event) => {
      this.isPlaying = false;
      this.isPaused = false;
      this.currentUtterance = null;
      this.emit('error', event);
      if (options.onError) options.onError(event);
    };

    this.currentUtterance = utterance;
    speechSynthesis.speak(utterance);
  }

  pause() {
    if (this.isSupported && this.isPlaying) {
      speechSynthesis.pause();
      this.isPaused = true;
      this.isPlaying = false;
      this.emit('pause');
    }
  }

  resume() {
    if (this.isSupported && this.isPaused) {
      speechSynthesis.resume();
      this.isPaused = false;
      this.isPlaying = true;
      this.emit('resume');
    }
  }

  stop() {
    if (this.isSupported) {
      speechSynthesis.cancel();
      this.isPlaying = false;
      this.isPaused = false;
      this.currentUtterance = null;
      this.emit('stop');
    }
  }

  // Get a list of available voices for debugging
  getVoicesList() {
    return this.voices.map(voice => ({
      name: voice.name,
      lang: voice.lang,
      gender: this.isFemaleVoice(voice.name) ? 'female' : 
              this.isMaleVoice(voice.name) ? 'male' : 'neutral'
    }));
  }
}

export const voiceManager = new VoiceManager();
