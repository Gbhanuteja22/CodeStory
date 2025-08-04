# TutorialGen Frontend

A multilingual React-based frontend for the AI-Powered Tutorial Generator.

## Features

- **Multi-page Flow**: Landing → File Selection → Generation → Tutorial Reader
- **Multilingual Support**: English, Hindi, Telugu, Hinglish, Telgish
- **Voice Reader**: Web Speech API integration (English voice)
- **Responsive Design**: Works on desktop and mobile
- **Real-time Progress**: Live updates during tutorial generation

## Quick Start

1. **Install Dependencies**:
   ```bash
   cd webapp/frontend
   npm install
   ```

2. **Start Development Server**:
   ```bash
   npm start
   ```

3. **Access the App**:
   Open http://localhost:3000 in your browser

## Project Structure

```
webapp/frontend/
├── src/
│   ├── components/          # Reusable components
│   │   └── LanguageSelector.js
│   ├── pages/              # Main pages
│   │   ├── LandingPage.js
│   │   ├── FileSelectorPage.js
│   │   ├── GeneratingPage.js
│   │   └── TutorialReaderPage.js
│   ├── utils/              # Utilities
│   │   ├── api.js          # API calls
│   │   └── i18n.js         # Internationalization
│   ├── App.js              # Main app component
│   ├── index.js            # Entry point
│   └── index.css           # Global styles
├── public/
│   └── index.html          # HTML template
└── package.json            # Dependencies
```

## Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests

## Technology Stack

- **React** 18 - UI framework
- **React Router** - Client-side routing
- **React i18next** - Internationalization
- **TailwindCSS** - Styling framework
- **Lucide React** - Icon library
- **React Markdown** - Markdown rendering

## API Integration

The frontend communicates with the backend API at `http://localhost:8000`:

- `POST /generate` - Start tutorial generation
- `GET /status/{taskId}` - Check generation progress
- `GET /output/{taskId}` - Get generated files

## Multilingual Support

Translations are stored in `webapp/locales/`:
- `en.json` - English (default)
- `hi.json` - Hindi
- `te.json` - Telugu
- `hinglish.json` - Hinglish (Hindi + English mix)
- `telgish.json` - Telgish (Telugu + English mix)

## Voice Features

- **Text-to-Speech**: Reads tutorial content aloud using Web Speech API
- **Play/Pause Controls**: Standard audio controls
- **English Voice Only**: Optimized for technical content
- **Auto-stop**: Stops when switching between chapters

## Browser Support

- Chrome/Edge 88+
- Firefox 85+
- Safari 14+
- Mobile browsers with modern Web APIs
