#!/usr/bin/env python3

from tutorial_builder import execute_documentation_generation
import sys

def main():
    try:
        print("🔄 Starting AI-powered documentation generation...")
        output_path = execute_documentation_generation()
        print(f"\n✅ Documentation generation completed successfully!")
        print(f"📁 Output location: {output_path}")
        print(f"🌐 Open index.md to start exploring the generated tutorial.")
        return 0
    except KeyboardInterrupt:
        print(f"\n⚠️  Documentation generation cancelled by user.")
        return 1
    except Exception as error:
        print(f"\n❌ Documentation generation failed: {error}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
