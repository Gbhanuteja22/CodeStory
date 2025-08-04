@echo off
echo 🚀 Starting Documentation Generator Webapp...
echo.

echo 📦 Checking dependencies...
E:/CodeStory/.venv/Scripts/python.exe -c "import fastapi, uvicorn; print('✅ Dependencies OK')" 2>nul
if errorlevel 1 (
    echo ❌ Missing dependencies. Installing...
    E:/CodeStory/.venv/Scripts/python.exe -m pip install fastapi uvicorn[standard] pydantic python-multipart
    echo.
)

echo 🌐 Starting server...
echo 📖 Web interface will be at: http://localhost:8000
echo 🔧 API docs will be at: http://localhost:8000/docs
echo ⚡ Your CLI still works: python codestory.py --repo https://github.com/owner/repo
echo.
echo Press Ctrl+C to stop the server
echo.

E:/CodeStory/.venv/Scripts/python.exe webapp_server.py
