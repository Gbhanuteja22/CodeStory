import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { I18nextProvider } from 'react-i18next';
import i18n from './utils/i18n';
import { ThemeProvider } from './contexts/ThemeContext';

// Pages
import LandingPage from './pages/LandingPage';
import FileSelectorPage from './pages/FileSelectorPage';
import GeneratingPage from './pages/GeneratingPage';
import TutorialReaderPage from './pages/TutorialReaderPage';

// Styles
import './index.css';

function App() {
  return (
    <ThemeProvider>
      <I18nextProvider i18n={i18n}>
        <Router>
          <div className="App">
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/file-selector" element={<FileSelectorPage />} />
              <Route path="/generating" element={<GeneratingPage />} />
              <Route path="/tutorial" element={<TutorialReaderPage />} />
            </Routes>
          </div>
        </Router>
      </I18nextProvider>
    </ThemeProvider>
  );
}

export default App;
