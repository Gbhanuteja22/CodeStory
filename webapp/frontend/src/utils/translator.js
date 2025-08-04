/**
 * Translation utility using Google Translate API or fallback methods
 */

class Translator {
  constructor() {
    this.cache = new Map();
    this.isTranslating = false;
  }

  /**
   * Translate text to target language
   * @param {string} text - Text to translate
   * @param {string} targetLang - Target language code (hi, te, etc.)
   * @param {string} sourceLang - Source language code (default: 'en')
   * @returns {Promise<string>} Translated text
   */
  async translateText(text, targetLang, sourceLang = 'en') {
    // Return original text if same language or English
    if (targetLang === 'en' || targetLang === sourceLang) {
      return text;
    }

    // Check cache first
    const cacheKey = `${sourceLang}-${targetLang}-${text.substring(0, 50)}`;
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }

    try {
      // Try Google Translate API first (requires API key)
      const translated = await this.tryGoogleTranslate(text, targetLang, sourceLang);
      if (translated) {
        this.cache.set(cacheKey, translated);
        return translated;
      }
    } catch (error) {
      console.warn('Google Translate failed:', error);
    }

    try {
      // Fallback to LibreTranslate or other free API
      const translated = await this.tryLibreTranslate(text, targetLang, sourceLang);
      if (translated) {
        this.cache.set(cacheKey, translated);
        return translated;
      }
    } catch (error) {
      console.warn('LibreTranslate failed:', error);
    }

    // If all translation methods fail, return original text
    throw new Error(`Translation unavailable in ${this.getLanguageName(targetLang)}`);
  }

  async tryGoogleTranslate(text, targetLang, sourceLang) {
    // Note: This requires a Google Translate API key
    // For demo purposes, we'll use a mock translation
    return this.mockTranslate(text, targetLang);
  }

  async tryLibreTranslate(text, targetLang, sourceLang) {
    try {
      const response = await fetch('https://translate.argosopentech.com/translate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          q: text,
          source: sourceLang,
          target: this.getLibreTranslateCode(targetLang),
          format: 'text'
        })
      });

      if (response.ok) {
        const data = await response.json();
        return data.translatedText;
      }
    } catch (error) {
      console.error('LibreTranslate error:', error);
    }
    return null;
  }

  mockTranslate(text, targetLang) {
    // Mock translation for demonstration
    // In a real app, this would call actual translation API
    const translations = {
      hi: {
        'Tutorial': 'ट्यूटोरियल',
        'Introduction': 'परिचय',
        'Getting Started': 'शुरुआत करना',
        'Code': 'कोड',
        'Example': 'उदाहरण',
        'Chapter': 'अध्याय'
      },
      te: {
        'Tutorial': 'ట్యుటోరియల్',
        'Introduction': 'పరిచయం',
        'Getting Started': 'ప్రారంభించడం',
        'Code': 'కోడ్',
        'Example': 'ఉదాహరణ',
        'Chapter': 'అధ్యాయం'
      }
    };

    // Simple word replacement for demo
    if (translations[targetLang]) {
      let translatedText = text;
      Object.entries(translations[targetLang]).forEach(([english, translated]) => {
        translatedText = translatedText.replace(new RegExp(english, 'gi'), translated);
      });
      return translatedText;
    }

    return text; // Return original if no translation available
  }

  getLibreTranslateCode(frontendLang) {
    const mapping = {
      'hi': 'hi',
      'te': 'te',
      'hinglish': 'hi', // Use Hindi for Hinglish
      'telgish': 'te'   // Use Telugu for Telgish
    };
    return mapping[frontendLang] || 'en';
  }

  getLanguageName(langCode) {
    const names = {
      'hi': 'Hindi',
      'te': 'Telugu',
      'hinglish': 'Hinglish',
      'telgish': 'Telgish',
      'en': 'English'
    };
    return names[langCode] || langCode;
  }

  /**
   * Translate entire markdown content
   * @param {string} markdown - Markdown content
   * @param {string} targetLang - Target language
   * @returns {Promise<string>} Translated markdown
   */
  async translateMarkdown(markdown, targetLang) {
    if (targetLang === 'en') {
      return markdown;
    }

    try {
      // Split content into translatable chunks (excluding code blocks)
      const chunks = this.splitMarkdownForTranslation(markdown);
      const translatedChunks = [];

      for (const chunk of chunks) {
        if (chunk.type === 'code') {
          // Don't translate code blocks
          translatedChunks.push(chunk.content);
        } else {
          // Translate text content
          const translated = await this.translateText(chunk.content, targetLang);
          translatedChunks.push(translated);
        }
      }

      return translatedChunks.join('');
    } catch (error) {
      throw error;
    }
  }

  splitMarkdownForTranslation(markdown) {
    const chunks = [];
    const lines = markdown.split('\n');
    let currentChunk = '';
    let inCodeBlock = false;

    for (const line of lines) {
      if (line.trim().startsWith('```')) {
        if (currentChunk) {
          chunks.push({ type: 'text', content: currentChunk });
          currentChunk = '';
        }
        inCodeBlock = !inCodeBlock;
        currentChunk += line + '\n';
        if (!inCodeBlock) {
          chunks.push({ type: 'code', content: currentChunk });
          currentChunk = '';
        }
      } else {
        currentChunk += line + '\n';
      }
    }

    if (currentChunk) {
      chunks.push({ type: inCodeBlock ? 'code' : 'text', content: currentChunk });
    }

    return chunks;
  }
}

export const translator = new Translator();
