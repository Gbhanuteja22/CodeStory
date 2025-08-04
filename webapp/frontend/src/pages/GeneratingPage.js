import React from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, CheckCircle, XCircle, BookOpen, Github } from 'lucide-react';
import LanguageSelector from '../components/LanguageSelector';
import { api } from '../utils/api';
import { getBackendLanguage } from '../utils/i18n';

const GeneratingPage = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [taskId, setTaskId] = React.useState(null);
  const [status, setStatus] = React.useState(null);
  const [error, setError] = React.useState('');
  const [isStarting, setIsStarting] = React.useState(true);

  React.useEffect(() => {
    const repoUrl = localStorage.getItem('repoUrl');
    const includePatterns = localStorage.getItem('includePatterns');
    const excludePatterns = localStorage.getItem('excludePatterns');

    if (!repoUrl) {
      navigate('/');
      return;
    }

    startGeneration(repoUrl, includePatterns, excludePatterns);
  }, [navigate]);

  const startGeneration = async (repoUrl, includePatterns, excludePatterns) => {
    try {
      setIsStarting(true);
      
      // Get the backend language format for the current UI language
      const backendLanguage = getBackendLanguage(i18n.language);
      
      const response = await api.generateTutorial({
        repo_url: repoUrl,
        include_patterns: includePatterns ? includePatterns.split(',').map(p => p.trim()).filter(p => p) : [],
        exclude_patterns: excludePatterns ? excludePatterns.split(',').map(p => p.trim()).filter(p => p) : [],
        language: backendLanguage, // Use mapped language for content translation
        max_abstractions: 10,
        use_cache: true
      });

      if (response.task_id) {
        setTaskId(response.task_id);
        localStorage.setItem('taskId', response.task_id);
        setIsStarting(false);
      } else {
        throw new Error('Failed to start generation');
      }
    } catch (err) {
      setError(err.message || 'Failed to start tutorial generation');
      setIsStarting(false);
    }
  };

  React.useEffect(() => {
    if (!taskId) return;

    const pollStatus = async () => {
      try {
        const statusData = await api.getTaskStatus(taskId);
        setStatus(statusData);

        if (statusData.status === 'completed') {
          // Navigate to tutorial reader after a brief delay
          setTimeout(() => {
            navigate('/tutorial');
          }, 2000);
        } else if (statusData.status === 'failed') {
          setError(statusData.error || 'Tutorial generation failed');
        }
      } catch (err) {
        console.error('Error polling status:', err);
      }
    };

    // Poll immediately and then every 2 seconds
    pollStatus();
    const interval = setInterval(pollStatus, 2000);

    return () => clearInterval(interval);
  }, [taskId, navigate]);

  const handleBack = () => {
    navigate('/file-selector');
  };

  const getProgressColor = () => {
    if (error || status?.status === 'failed') return 'bg-red-500';
    if (status?.status === 'completed') return 'bg-green-500';
    return 'bg-blue-500';
  };

  const getStatusIcon = () => {
    if (error || status?.status === 'failed') {
      return <XCircle className="w-6 h-6 text-red-500" />;
    }
    if (status?.status === 'completed') {
      return <CheckCircle className="w-6 h-6 text-green-500" />;
    }
    return <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />;
  };

  const getStatusMessage = () => {
    if (error) return error;
    if (isStarting) return 'Starting tutorial generation...';
    if (status?.status === 'completed') return t('tutorialReady');
    if (status?.status === 'failed') return status.error || 'Generation failed';
    return status?.message || t('generatingTutorial');
  };

  const progress = status?.progress || (isStarting ? 5 : 0);

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
            <span className="text-sm">Back</span>
          </button>
          <div className="flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-blue-600" />
            <span className="font-semibold text-gray-800">TutorialGen</span>
          </div>
        </div>
        <LanguageSelector />
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8 max-w-2xl">
        {/* Progress Indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-4">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
                ✓
              </div>
              <span className="ml-2 text-sm text-gray-600">Repository</span>
            </div>
            <div className="w-12 h-1 bg-green-500"></div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
                ✓
              </div>
              <span className="ml-2 text-sm text-gray-600">Files</span>
            </div>
            <div className="w-12 h-1 bg-blue-500"></div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
                3
              </div>
              <span className="ml-2 text-sm font-medium text-blue-600">Generate</span>
            </div>
          </div>
        </div>

        {/* Generation Status */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8 text-center">
          <div className="mb-6">
            {getStatusIcon()}
          </div>

          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            {t('generationProgress')}
          </h2>

          <p className="text-gray-600 mb-8">
            {t('pleaseWait')}
          </p>

          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-3 mb-4 overflow-hidden">
            <div
              className={`h-3 rounded-full transition-all duration-500 ease-out ${getProgressColor()}`}
              style={{ width: `${Math.min(progress, 100)}%` }}
            />
          </div>

          <div className="text-sm text-gray-500 mb-6">
            {progress}% Complete
          </div>

          {/* Status Message */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <p className="text-sm font-medium text-gray-800">
              {getStatusMessage()}
            </p>
          </div>

          {/* Repository Info */}
          <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
            <Github className="w-4 h-4" />
            <span className="font-mono">{localStorage.getItem('repoUrl')}</span>
          </div>

          {/* Success Actions */}
          {status?.status === 'completed' && (
            <div className="mt-6">
              <p className="text-green-600 font-medium mb-4">
                Tutorial generated successfully! Redirecting...
              </p>
              <button
                onClick={() => navigate('/tutorial')}
                className="bg-gradient-to-r from-green-600 to-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:from-green-700 hover:to-blue-700 transition-all"
              >
                View Tutorial Now
              </button>
            </div>
          )}

          {/* Error Actions */}
          {(error || status?.status === 'failed') && (
            <div className="mt-6">
              <button
                onClick={() => navigate('/file-selector')}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-all"
              >
                Try Again
              </button>
            </div>
          )}
        </div>

        {/* Fun Facts */}
        {!error && status?.status !== 'failed' && status?.status !== 'completed' && (
          <div className="mt-8 bg-blue-50 rounded-lg p-6">
            <h3 className="font-semibold text-blue-800 mb-3">Did you know?</h3>
            <p className="text-sm text-blue-700">
              Our AI analyzes your code structure, identifies key concepts, and creates a logical learning path 
              that's perfect for beginners. This process typically takes 2-5 minutes depending on your repository size.
            </p>
          </div>
        )}
      </main>
    </div>
  );
};

export default GeneratingPage;
