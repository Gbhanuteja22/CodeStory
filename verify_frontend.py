#!/usr/bin/env python3
"""
Frontend Verification Test
Checks if all frontend files are in place and properly configured.
"""

import os
import json
from pathlib import Path

def check_file_exists(path, description):
    """Check if a file exists and print status"""
    if os.path.exists(path):
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description}: MISSING - {path}")
        return False

def check_frontend_structure():
    """Verify the complete frontend structure"""
    print("🔍 Checking Frontend Structure...\n")
    
    base_path = "webapp/frontend"
    checks = [
        # Core files
        (f"{base_path}/package.json", "Package.json"),
        (f"{base_path}/tailwind.config.js", "TailwindCSS Config"),
        (f"{base_path}/postcss.config.js", "PostCSS Config"),
        (f"{base_path}/public/index.html", "HTML Template"),
        
        # React app files
        (f"{base_path}/src/App.js", "Main App Component"),
        (f"{base_path}/src/index.js", "React Entry Point"),
        (f"{base_path}/src/index.css", "CSS Styles"),
        
        # Components
        (f"{base_path}/src/components/LanguageSelector.js", "Language Selector"),
        
        # Pages
        (f"{base_path}/src/pages/LandingPage.js", "Landing Page"),
        (f"{base_path}/src/pages/FileSelectorPage.js", "File Selector Page"),
        (f"{base_path}/src/pages/GeneratingPage.js", "Generating Page"),
        (f"{base_path}/src/pages/TutorialReaderPage.js", "Tutorial Reader Page"),
        
        # Utils
        (f"{base_path}/src/utils/api.js", "API Utilities"),
        (f"{base_path}/src/utils/i18n.js", "i18n Configuration"),
        
        # Translations
        (f"{base_path}/src/locales/en.json", "English Translations"),
        (f"{base_path}/src/locales/hi.json", "Hindi Translations"),
        (f"{base_path}/src/locales/te.json", "Telugu Translations"),
        (f"{base_path}/src/locales/hinglish.json", "Hinglish Translations"),
        (f"{base_path}/src/locales/telgish.json", "Telgish Translations"),
    ]
    
    all_good = True
    for path, description in checks:
        if not check_file_exists(path, description):
            all_good = False
    
    print(f"\n{'🎉 Frontend Structure: COMPLETE!' if all_good else '❌ Frontend Structure: INCOMPLETE'}")
    return all_good

def check_translations():
    """Verify translation files have required keys"""
    print("\n🌍 Checking Translations...\n")
    
    required_keys = [
        "generateTutorial", "pasteGithubLink", "downloadPdf",
        "includePatterns", "excludePatterns", "selectFilesToInclude",
        "generatingTutorial", "tutorialReady", "shareTutorial", "play", "pause"
    ]
    
    languages = ['en', 'hi', 'te', 'hinglish', 'telgish']
    all_good = True
    
    for lang in languages:
        try:
            with open(f"webapp/frontend/src/locales/{lang}.json", 'r', encoding='utf-8') as f:
                translations = json.load(f)
                
            missing_keys = [key for key in required_keys if key not in translations]
            
            if not missing_keys:
                print(f"✅ {lang.capitalize()} translations: Complete")
            else:
                print(f"❌ {lang.capitalize()} translations: Missing {missing_keys}")
                all_good = False
                
        except FileNotFoundError:
            print(f"❌ {lang.capitalize()} translations: File not found")
            all_good = False
        except json.JSONDecodeError:
            print(f"❌ {lang.capitalize()} translations: Invalid JSON")
            all_good = False
    
    print(f"\n{'🎉 Translations: COMPLETE!' if all_good else '❌ Translations: INCOMPLETE'}")
    return all_good

def main():
    """Run all checks"""
    print("🚀 Frontend Verification Test\n")
    print("=" * 50)
    
    structure_ok = check_frontend_structure()
    translations_ok = check_translations()
    
    print("\n" + "=" * 50)
    if structure_ok and translations_ok:
        print("🎊 FRONTEND IS FULLY IMPLEMENTED AND READY!")
        print("\n👉 To start the frontend:")
        print("   cd webapp/frontend")
        print("   npm install  # First time only")
        print("   npm start    # Starts on localhost:3000")
    else:
        print("❌ FRONTEND NEEDS FIXES")
        
    print("\n💡 Backend should be running on localhost:8000")
    print("💡 Use: python webapp_server.py")

if __name__ == "__main__":
    main()
