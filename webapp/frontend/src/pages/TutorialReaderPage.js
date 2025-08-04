import React from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, BookOpen, Download, Play, Pause, 
  Volume2, VolumeX, Menu, X, ChevronRight 
} from 'lucide-react';
import LanguageSelector from '../components/LanguageSelector';
import MarkdownRenderer from '../components/MarkdownRenderer';
import ThemeToggle from '../components/ThemeToggle';
import { api } from '../utils/api';
import { voiceManager } from '../utils/voiceManager';
import { getVoiceLanguage } from '../utils/i18n';
import { translator } from '../utils/translator';

const TutorialReaderPage = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [tutorialFiles, setTutorialFiles] = React.useState([]);
  const [originalFiles, setOriginalFiles] = React.useState([]); // Store original English content
  const [currentFile, setCurrentFile] = React.useState(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState('');
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const [translationError, setTranslationError] = React.useState('');
  const [isTranslating, setIsTranslating] = React.useState(false);
  
  // Voice functionality
  const [isPlaying, setIsPlaying] = React.useState(false);
  const [isPaused, setIsPaused] = React.useState(false);
  const [voiceEnabled, setVoiceEnabled] = React.useState(true);

  React.useEffect(() => {
    const taskId = localStorage.getItem('taskId');
    if (!taskId) {
      navigate('/');
      return;
    }

    loadTutorialFiles(taskId);
  }, [navigate]);

  const loadTutorialFiles = async (taskId) => {
    try {
      setIsLoading(true);
      const response = await api.getOutputFiles(taskId);
      
      if (response.files && response.files.length > 0) {
        // Clean up file names and sort files so index.md comes first
        const cleanedFiles = response.files.map(file => ({
          ...file,
          filename: file.filename
            .replace(/__+/g, '_') // Replace multiple underscores with single
            .replace(/_+\./g, '.') // Remove trailing underscores before extension
            .replace(/(_+)$/, '') // Remove trailing underscores
        }));
        
        const sortedFiles = cleanedFiles.sort((a, b) => {
          if (a.filename === 'index.md') return -1;
          if (b.filename === 'index.md') return 1;
          return a.filename.localeCompare(b.filename);
        });
        
        // Store original files for translation reference
        setOriginalFiles(sortedFiles);
        setTutorialFiles(sortedFiles);
        setCurrentFile(sortedFiles[0]);
        
        // Translate content if language is not English
        if (i18n.language !== 'en') {
          await translateAllFiles(sortedFiles);
        }
      } else {
        setError('No tutorial files found');
      }
    } catch (err) {
      setError('Failed to load tutorial files');
    } finally {
      setIsLoading(false);
    }
  };

  const translateAllFiles = async (files) => {
    if (i18n.language === 'en') return;
    
    console.log(`Translating files to ${i18n.language}...`); // Debug log
    setIsTranslating(true);
    setTranslationError('');
    
    try {
      const translatedFiles = await Promise.all(
        files.map(async (file) => {
          try {
            const translatedContent = await translator.translateMarkdown(
              file.content, 
              i18n.language
            );
            return { ...file, content: translatedContent };
          } catch (error) {
            console.warn(`Translation failed for ${file.filename}:`, error);
            return file; // Return original file if translation fails
          }
        })
      );
      
      setTutorialFiles(translatedFiles);
      console.log(`Translation completed for ${translatedFiles.length} files to ${i18n.language}`); // Debug log
      
      // Update current file if it was translated
      if (currentFile) {
        const translatedCurrentFile = translatedFiles.find(f => f.filename === currentFile.filename);
        if (translatedCurrentFile) {
          setCurrentFile(translatedCurrentFile);
          console.log(`Current file updated to translated version`); // Debug log
        }
      }
    } catch (error) {
      setTranslationError(`Translation unavailable in ${translator.getLanguageName(i18n.language)}`);
      console.error('Translation error:', error);
    } finally {
      setIsTranslating(false);
    }
  };

  // Handle language changes
  React.useEffect(() => {
    if (originalFiles.length > 0) {
      if (i18n.language === 'en') {
        // Restore original English content
        setTutorialFiles(originalFiles);
        const originalCurrentFile = originalFiles.find(f => f.filename === currentFile?.filename);
        if (originalCurrentFile) {
          setCurrentFile(originalCurrentFile);
        }
        setTranslationError('');
      } else {
        // Translate to new language - always retranslate to ensure content is updated
        translateAllFiles(originalFiles);
      }
    }
  }, [i18n.language, originalFiles.length]); // Add originalFiles.length as dependency

  // Voice functionality
  React.useEffect(() => {
    const checkVoiceSupport = () => {
      if (!('speechSynthesis' in window)) {
        setVoiceEnabled(false);
      }
    };
    
    checkVoiceSupport();
    
    // Cleanup on unmount
    return () => {
      voiceManager.stop();
    };
  }, []);

  // Listen for voice events
  React.useEffect(() => {
    const handleVoiceStart = () => {
      setIsPlaying(true);
      setIsPaused(false);
    };

    const handleVoiceEnd = () => {
      setIsPlaying(false);
      setIsPaused(false);
    };

    const handleVoicePause = () => {
      setIsPlaying(false);
      setIsPaused(true);
    };

    const handleVoiceResume = () => {
      setIsPlaying(true);
      setIsPaused(false);
    };

    voiceManager.on('start', handleVoiceStart);
    voiceManager.on('end', handleVoiceEnd);
    voiceManager.on('pause', handleVoicePause);
    voiceManager.on('resume', handleVoiceResume);

    return () => {
      voiceManager.off('start', handleVoiceStart);
      voiceManager.off('end', handleVoiceEnd);
      voiceManager.off('pause', handleVoicePause);
      voiceManager.off('resume', handleVoiceResume);
    };
  }, []);

  const extractTextFromMarkdown = (markdown) => {
    // Enhanced text extraction for voice synthesis
    return markdown
      .replace(/#{1,6}\s/g, '') // Remove headers
      .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold
      .replace(/\*(.*?)\*/g, '$1') // Remove italic
      .replace(/\[(.*?)\]\(.*?\)/g, '$1') // Remove links, keep text
      .replace(/```[\s\S]*?```/g, 'Code example.') // Replace code blocks
      .replace(/`(.*?)`/g, '$1') // Remove inline code backticks
      .replace(/^\s*[-*+]\s+/gm, '') // Remove list markers
      .replace(/^\s*\d+\.\s+/gm, '') // Remove numbered list markers
      .replace(/\n\s*\n/g, '\n') // Remove extra line breaks
      .trim();
  };

  const handlePlay = async () => {
    if (!voiceEnabled || !currentFile) return;

    if (isPaused) {
      voiceManager.resume();
      return;
    }

    const text = extractTextFromMarkdown(currentFile.content);
    const voiceLanguage = getVoiceLanguage(i18n.language);
    
    try {
      voiceManager.speak(text, voiceLanguage);
    } catch (error) {
      console.error('Voice synthesis failed:', error);
    }
  };

  const handlePause = () => {
    voiceManager.pause();
  };

  const handleStop = () => {
    voiceManager.stop();
  };

  const handleFileSelect = (file) => {
    if (isPlaying || isPaused) {
      handleStop();
    }
    setCurrentFile(file);
    setSidebarOpen(false);
  };

  const handleDownloadPDF = async () => {
    if (!currentFile) {
      alert('No tutorial content available for PDF generation.');
      return;
    }
    
    try {
      // Show loading state
      const originalButtonText = 'Download PDF';
      
      const response = await fetch('http://localhost:8000/generate-pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: currentFile.content,
          filename: currentFile.filename.replace('.md', ''),
          title: `Tutorial - ${currentFile.filename.replace('.md', '').replace(/_/g, ' ')}`
        }),
      });

      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
      }

      // Get the HTML content
      const htmlContent = await response.text();
      
      // Create a new window and write the HTML content
      const printWindow = window.open('', '_blank', 'width=800,height=600');
      if (!printWindow) {
        throw new Error('Popup blocked. Please allow popups for this site to download PDF.');
      }
      
      printWindow.document.write(htmlContent);
      printWindow.document.close();
      
      // The HTML page includes a print button that users can click to save as PDF
      
    } catch (error) {
      console.error('PDF generation failed:', error);
      alert(`Failed to generate PDF: ${error.message}`);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <BookOpen className="w-8 h-8 text-blue-600 mx-auto mb-4 animate-pulse" />
          <p className="text-gray-600">Loading tutorial...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            {t('backToHome')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            {sidebarOpen ? <X className="w-5 h-5 text-gray-700 dark:text-gray-300" /> : <Menu className="w-5 h-5 text-gray-700 dark:text-gray-300" />}
          </button>
          <div className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
               onClick={() => navigate('/')}>
            <BookOpen className="w-6 h-6 text-blue-600" />
            <span className="font-semibold text-gray-800 dark:text-gray-200 hidden sm:inline">TutorialGen</span>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-400 dark:text-gray-500 hidden sm:inline" />
          <span className="text-sm text-gray-600 dark:text-gray-400 hidden sm:inline truncate max-w-xs">
            {currentFile?.filename}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Voice Controls */}
          {voiceEnabled && (
            <div className="flex items-center gap-1 border border-gray-300 dark:border-gray-600 rounded-lg p-1">
              {!isPlaying && !isPaused && (
                <button
                  onClick={handlePlay}
                  className="p-2 hover:bg-gray-100 rounded-md transition-colors"
                  title={t('play')}
                >
                  <Play className="w-4 h-4 text-gray-700" />
                </button>
              )}
              {isPlaying && (
                <button
                  onClick={handlePause}
                  className="p-2 hover:bg-gray-100 rounded-md transition-colors"
                  title={t('pause')}
                >
                  <Pause className="w-4 h-4 text-gray-700" />
                </button>
              )}
              {isPaused && (
                <button
                  onClick={handlePlay}
                  className="p-2 hover:bg-gray-100 rounded-md transition-colors"
                  title={t('play')}
                >
                  <Play className="w-4 h-4 text-gray-700" />
                </button>
              )}
              {(isPlaying || isPaused) && (
                <button
                  onClick={handleStop}
                  className="p-2 hover:bg-gray-100 rounded-md transition-colors"
                  title="Stop"
                >
                  <VolumeX className="w-4 h-4 text-gray-700" />
                </button>
              )}
              {!isPlaying && !isPaused && (
                <Volume2 className="w-4 h-4 text-gray-400 p-2 box-content" />
              )}
            </div>
          )}

          {/* Action Buttons */}
          <button
            onClick={handleDownloadPDF}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title={t('downloadPdf')}
          >
            <Download className="w-4 h-4 text-gray-700 dark:text-gray-300" />
          </button>
          <LanguageSelector />
          <ThemeToggle className="ml-2" />
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className={`
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0 lg:static fixed inset-y-0 left-0 z-30
          w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col transition-transform duration-200 ease-in-out
        `}>
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="font-semibold text-gray-800 dark:text-gray-200">{t('tutorialNavigation')}</h2>
          </div>
          <nav className="flex-1 overflow-y-auto p-4">
            <ul className="space-y-2">
              {tutorialFiles.map((file, index) => (
                <li key={index}>
                  <button
                    onClick={() => handleFileSelect(file)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      currentFile?.filename === file.filename
                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-700'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    <div className="font-medium text-sm mb-1">
                      {file.filename.replace(/\.md$/, '').replace(/_/g, ' ')}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {file.content.length} characters
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          </nav>
        </aside>

        {/* Overlay for mobile */}
        {sidebarOpen && (
          <div
            className="lg:hidden fixed inset-0 z-20 bg-black bg-opacity-50"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900">
          {/* Translation Status/Error */}
          {(isTranslating || translationError) && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 p-4 mx-6 mt-4">
              {isTranslating && (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500 mr-2"></div>
                  <p className="text-blue-700 dark:text-blue-300">Translating content...</p>
                </div>
              )}
              {translationError && (
                <p className="text-orange-700 dark:text-orange-300">{translationError}</p>
              )}
            </div>
          )}
          
          {currentFile && (
            <article className="max-w-4xl mx-auto p-6 lg:p-8">
              <MarkdownRenderer content={currentFile.content} />
            </article>
          )}
        </main>
      </div>
    </div>
  );
};

export default TutorialReaderPage;
