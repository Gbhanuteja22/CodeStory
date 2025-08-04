import React from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, FileText, Settings, BookOpen } from 'lucide-react';
import LanguageSelector from '../components/LanguageSelector';

const FileSelectorPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [includePatterns, setIncludePatterns] = React.useState('*.py, *.js, *.jsx, *.ts, *.tsx, *.md, *.rst');
  const [excludePatterns, setExcludePatterns] = React.useState('tests/*, node_modules/*, .git/*, dist/*, build/*');
  const [repoUrl, setRepoUrl] = React.useState('');

  React.useEffect(() => {
    const savedRepoUrl = localStorage.getItem('repoUrl');
    if (!savedRepoUrl) {
      navigate('/');
      return;
    }
    setRepoUrl(savedRepoUrl);
  }, [navigate]);

  const handleBack = () => {
    navigate('/');
  };

  const handleNext = () => {
    // Store the patterns for the next step
    localStorage.setItem('includePatterns', includePatterns);
    localStorage.setItem('excludePatterns', excludePatterns);
    navigate('/generating');
  };

  const defaultIncludePatterns = [
    '*.py', '*.js', '*.jsx', '*.ts', '*.tsx', '*.go', '*.java',
    '*.c', '*.cpp', '*.h', '*.md', '*.rst', '*.yaml', '*.yml'
  ];

  const defaultExcludePatterns = [
    'tests/*', 'test/*', 'node_modules/*', '.git/*', '.github/*',
    'dist/*', 'build/*', 'venv/*', '.venv/*', 'assets/*', 'images/*'
  ];

  const addPattern = (pattern, isInclude) => {
    if (isInclude) {
      const current = includePatterns ? includePatterns.split(',').map(p => p.trim()) : [];
      if (!current.includes(pattern)) {
        setIncludePatterns([...current, pattern].join(', '));
      }
    } else {
      const current = excludePatterns ? excludePatterns.split(',').map(p => p.trim()) : [];
      if (!current.includes(pattern)) {
        setExcludePatterns([...current, pattern].join(', '));
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="flex justify-between items-center p-6 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">{t('backToHome')}</span>
          </button>
          <div className="flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-blue-600" />
            <span className="font-semibold text-gray-800">TutorialGen</span>
          </div>
        </div>
        <LanguageSelector />
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8 max-w-4xl">
        {/* Progress Indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-4">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
                ✓
              </div>
              <span className="ml-2 text-sm text-gray-600">Repository</span>
            </div>
            <div className="w-12 h-1 bg-blue-500"></div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
                2
              </div>
              <span className="ml-2 text-sm font-medium text-blue-600">{t('selectFiles')}</span>
            </div>
            <div className="w-12 h-1 bg-gray-300"></div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-gray-300 text-gray-500 rounded-full flex items-center justify-center text-sm font-medium">
                3
              </div>
              <span className="ml-2 text-sm text-gray-500">Generate</span>
            </div>
          </div>
        </div>

        {/* Repository Info */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <FileText className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-800">Repository Selected</h2>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">GitHub Repository:</p>
            <p className="font-mono text-sm text-blue-600 break-all">{repoUrl}</p>
          </div>
        </div>

        {/* File Patterns Configuration */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
          <div className="flex items-center gap-3 mb-6">
            <Settings className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-800">{t('filePatterns')}</h2>
          </div>

          <div className="space-y-6">
            {/* Include Patterns */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                {t('includePatterns')}
              </label>
              <p className="text-sm text-gray-500 mb-3">{t('includePatternsDesc')}</p>
              <textarea
                value={includePatterns}
                onChange={(e) => setIncludePatterns(e.target.value)}
                placeholder={t('placeholderInclude')}
                rows={3}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors font-mono text-sm"
              />
              <div className="mt-3">
                <p className="text-xs text-gray-500 mb-2">Quick add:</p>
                <div className="flex flex-wrap gap-1">
                  {defaultIncludePatterns.map((pattern) => (
                    <button
                      key={pattern}
                      onClick={() => addPattern(pattern, true)}
                      className="text-xs bg-blue-100 hover:bg-blue-200 text-blue-700 px-2 py-1 rounded transition-colors"
                    >
                      {pattern}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Exclude Patterns */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                {t('excludePatterns')}
              </label>
              <p className="text-sm text-gray-500 mb-3">{t('excludePatternsDesc')}</p>
              <textarea
                value={excludePatterns}
                onChange={(e) => setExcludePatterns(e.target.value)}
                placeholder={t('placeholderExclude')}
                rows={3}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors font-mono text-sm"
              />
              <div className="mt-3">
                <p className="text-xs text-gray-500 mb-2">Quick add:</p>
                <div className="flex flex-wrap gap-1">
                  {defaultExcludePatterns.map((pattern) => (
                    <button
                      key={pattern}
                      onClick={() => addPattern(pattern, false)}
                      className="text-xs bg-red-100 hover:bg-red-200 text-red-700 px-2 py-1 rounded transition-colors"
                    >
                      {pattern}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 px-6 py-3 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-all"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>{t('backToHome')}</span>
          </button>

          <button
            onClick={handleNext}
            className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all duration-200 transform hover:scale-[1.02]"
          >
            <span>{t('generateTutorial')}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </main>
    </div>
  );
};

export default FileSelectorPage;
