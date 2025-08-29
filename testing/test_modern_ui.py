#!/usr/bin/env python3
"""
Test script to showcase the modern UI
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add current directory to path to import exam_helper
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_modern_ui():
    """Test the modern UI without full functionality"""
    print("🎨 Testing Modern UI...")
    print("=" * 50)
    
    try:
        from exam_helper import ExamHelper
        
        print("✅ Creating modern UI...")
        app = ExamHelper()
        
        print("✅ Modern UI loaded successfully!")
        print("\n🎨 Modern UI Features:")
        print("- Dark theme with modern colors")
        print("- Rounded corners and flat design")
        print("- Color-coded buttons and status indicators")
        print("- Modern typography (Segoe UI)")
        print("- Improved spacing and layout")
        print("- Interactive hover effects")
        print("- Professional appearance")
        
        print("\n🚀 Starting modern UI...")
        app.run()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required modules are installed")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_color_palette():
    """Show the modern color palette"""
    print("\n🎨 Modern Color Palette:")
    print("-" * 30)
    colors = {
        'bg_primary': '#1a1a1a',      # Main background
        'bg_secondary': '#2d2d2d',    # Secondary background  
        'bg_tertiary': '#3d3d3d',     # Tertiary background
        'accent': '#4a9eff',          # Blue accent
        'accent_hover': '#6bb6ff',    # Lighter blue
        'success': '#00d4aa',         # Green for success
        'warning': '#ffb347',         # Orange for warning
        'error': '#ff6b6b',           # Red for error
        'text_primary': '#ffffff',    # Primary text
        'text_secondary': '#b0b0b0',  # Secondary text
        'border': '#404040'           # Border color
    }
    
    for name, color in colors.items():
        print(f"{name:15} : {color}")

def main():
    print("Modern UI Test for Exam Helper")
    print("=" * 50)
    
    show_color_palette()
    
    print("\n" + "=" * 50)
    input("Press Enter to launch the modern UI...")
    
    test_modern_ui()

if __name__ == "__main__":
    main()