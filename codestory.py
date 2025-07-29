#!/usr/bin/env python3
"""
CodeStory - AI-Powered Documentation Generator
Simple entry point for generating comprehensive tutorials from codebases.
"""

from tutorial_builder import execute_documentation_generation
import sys

def main():
    try:
        print("🚀 CodeStory - AI Documentation Generator Starting...")
        print("=" * 60)
        
        output_path = execute_documentation_generation()
        
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! CodeStory documentation generation completed!")
        print(f"📁 Your tutorial is ready at: {output_path}")
        print(f"🌐 Open 'index.md' to start exploring your generated tutorial")
        print("=" * 60)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  CodeStory generation cancelled by user.")
        return 1
        
    except Exception as error:
        print(f"\n❌ CodeStory generation failed: {error}")
        print("\nTip: Make sure your GEMINI_API_KEY environment variable is set!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
