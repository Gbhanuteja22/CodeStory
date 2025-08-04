@echo off
echo 🚀 Starting CodeStory Backend Server...
echo.

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
    echo 📁 Activating virtual environment...
    call .venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo ⚠️  No virtual environment found, using system Python
)

echo.
echo 🐍 Using Python: 
python -c "import sys; print(sys.executable)"

echo.
echo 🔍 Testing FastAPI import...
python -c "import fastapi; print('✅ FastAPI available')" 2>nul || (
    echo ❌ FastAPI not found, installing dependencies...
    python -m pip install fastapi uvicorn[standard] pydantic python-multipart
)

echo.
echo 🌐 Starting server on http://localhost:8000
echo 💡 Press Ctrl+C to stop the server
echo.

python webapp_server.py

echo.
echo 🛑 Server stopped.
pause
