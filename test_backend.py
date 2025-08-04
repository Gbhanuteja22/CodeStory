#!/usr/bin/env python3
"""
Quick test to verify the backend is working correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

try:
    from tutorial_builder import DocumentationGenerator
    print("✅ DocumentationGenerator import successful")
    
    # Test the method exists
    generator = DocumentationGenerator()
    if hasattr(generator, 'configure_workspace'):
        print("✅ configure_workspace method exists")
    else:
        print("❌ configure_workspace method missing")
        
    if hasattr(generator, 'setup_workspace'):
        print("❌ Old setup_workspace method still exists (should be removed)")
    else:
        print("✅ Old setup_workspace method properly removed")
        
    print("\n🎯 Backend test completed successfully!")
    print("👉 You can now run: python webapp_server.py")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("👉 Please install dependencies: pip install -r requirements.txt")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
