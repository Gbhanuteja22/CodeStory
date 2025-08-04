@echo off
echo 🔄 Stopping any existing backend processes...
taskkill /f /im python.exe 2>nul

echo.
echo 🚀 Starting CodeStory Backend Server...
echo.

REM Check if virtual environment exists
if exist .venv\Scripts\activate.bat (
    echo 📁 Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️  No virtual environment found, using system Python
)

echo.
echo 🐍 Python version:
python --version

echo.
echo 📦 Installing/updating dependencies...
pip install -r requirements.txt

echo.
echo 🌐 Starting FastAPI server on http://localhost:8000
echo 💡 Press Ctrl+C to stop the server
echo.

python webapp_server.py

echo.
echo 🛑 Backend server stopped.
pause
