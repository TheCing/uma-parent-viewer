#!/usr/bin/env python3
"""
Encoding Diagnostic Tool for Uma Parent Viewer
Run this script to diagnose Unicode/encoding issues on Windows.
"""

import os
import sys
import locale

def main():
    print("=" * 60)
    print("  UMA PARENT VIEWER - ENCODING DIAGNOSTIC")
    print("=" * 60)
    print()
    
    # 1. Python version
    print("[Python Info]")
    print(f"  Version: {sys.version}")
    print(f"  Executable: {sys.executable}")
    print()
    
    # 2. User paths
    print("[User Paths]")
    home = os.path.expanduser("~")
    print(f"  Home directory: {home}")
    print(f"  Current directory: {os.getcwd()}")
    print(f"  Script location: {os.path.dirname(os.path.abspath(__file__))}")
    
    # Check for non-ASCII characters in paths
    has_non_ascii = False
    for path in [home, os.getcwd()]:
        try:
            path.encode('ascii')
        except UnicodeEncodeError:
            has_non_ascii = True
            print(f"  ** Non-ASCII characters detected in: {path}")
    
    if not has_non_ascii:
        print("  (All paths are ASCII-safe)")
    print()
    
    # 3. Console encoding
    print("[Console Encoding]")
    print(f"  stdout encoding: {sys.stdout.encoding}")
    print(f"  stderr encoding: {sys.stderr.encoding}")
    print(f"  stdin encoding: {sys.stdin.encoding}")
    print(f"  Filesystem encoding: {sys.getfilesystemencoding()}")
    print(f"  Default encoding: {sys.getdefaultencoding()}")
    print()
    
    # 4. Locale info
    print("[Locale Info]")
    print(f"  Preferred encoding: {locale.getpreferredencoding()}")
    try:
        print(f"  Current locale: {locale.getlocale()}")
    except:
        print("  Current locale: (unable to determine)")
    print()
    
    # 5. Environment variables
    print("[Relevant Environment Variables]")
    env_vars = ['PYTHONIOENCODING', 'LANG', 'LC_ALL', 'LC_CTYPE', 'PYTHONUTF8']
    for var in env_vars:
        value = os.environ.get(var, '(not set)')
        print(f"  {var}: {value}")
    print()
    
    # 6. Windows-specific info
    if sys.platform == 'win32':
        print("[Windows Code Pages]")
        try:
            import subprocess
            result = subprocess.run(['chcp'], shell=True, capture_output=True, text=True)
            print(f"  Console code page: {result.stdout.strip()}")
        except:
            print("  Console code page: (unable to determine)")
        
        # Check Windows version
        try:
            import platform
            print(f"  Windows version: {platform.platform()}")
        except:
            pass
        print()
    
    # 7. Test Unicode output
    print("[Unicode Output Test]")
    test_strings = [
        ("ASCII", "Hello World"),
        ("Japanese", "こんにちは"),
        ("Chinese", "你好世界"),
        ("Korean", "안녕하세요"),
        ("Emoji", "🐴✨"),
    ]
    
    for name, text in test_strings:
        try:
            print(f"  {name}: {text}")
        except UnicodeEncodeError as e:
            print(f"  {name}: FAILED - {e}")
    print()
    
    # 8. Recommendations
    print("[Recommendations]")
    issues_found = False
    
    if sys.stdout.encoding.lower() not in ['utf-8', 'utf8']:
        issues_found = True
        print("  ! stdout is not UTF-8. This can cause encoding errors.")
        print("    Fix: Set environment variable PYTHONIOENCODING=utf-8")
    
    if has_non_ascii:
        issues_found = True
        print("  ! Your user path contains non-ASCII characters.")
        print("    This is usually fine, but some tools may have issues.")
        print("    The Uma Parent Viewer has been updated to handle this.")
    
    if os.environ.get('PYTHONIOENCODING') is None:
        issues_found = True
        print("  ! PYTHONIOENCODING is not set.")
        print("    Consider adding: PYTHONIOENCODING=utf-8:replace")
    
    if not issues_found:
        print("  No obvious encoding issues detected!")
    
    print()
    print("=" * 60)
    print("  Copy this output and share it for troubleshooting.")
    print("=" * 60)
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    # Try to fix encoding for this diagnostic script
    if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except:
            pass
    if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
        try:
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except:
            pass
    
    main()
