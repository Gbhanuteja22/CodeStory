@echo off
echo 🚀 Setting up Documentation Generator Webapp...
echo.

echo 📦 Installing dependencies...
python -m pip install -r dependencies.txt

echo.
echo ✅ Setup complete!
echo.
echo 🌐 To run the webapp:
echo    python webapp\run_webapp.py
echo.
echo 💻 To use CLI (unchanged):
echo    python codestory.py --repo https://github.com/owner/repo
echo.
pause
