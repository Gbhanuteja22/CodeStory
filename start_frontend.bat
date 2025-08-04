@echo off
echo 🚀 Starting TutorialGen Frontend Development Server...
echo.

cd webapp\frontend

echo 📦 Installing dependencies (if needed)...
if not exist node_modules (
    echo Installing npm packages...
    npm install
) else (
    echo Dependencies already installed.
)

echo.
echo 🌐 Starting React development server...
echo Frontend will be available at: http://localhost:3000
echo Backend should be running at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the development server
echo.

npm start
