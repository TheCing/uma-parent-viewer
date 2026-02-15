# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Find and run UmaExtractor to export veteran data to this directory.

This script:
1. Searches for UmaExtractor installation on the system
2. Runs the extractor (requires Uma Musume to be on Veteran List page)
3. Outputs data.json to the same directory as this script

Usage:
    python run_extractor.py
"""

import os
import subprocess
import sys
from pathlib import Path

# Fix Unicode output on Windows consoles
if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr:
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Get the directory where this script lives (uma-parent-viewer repo)
SCRIPT_DIR = Path(__file__).parent.resolve()


CACHED_PATH_FILE = SCRIPT_DIR / ".umaextractor_path"


def load_cached_path() -> Path | None:
    """Load previously saved UmaExtractor path."""
    if CACHED_PATH_FILE.exists():
        try:
            saved = CACHED_PATH_FILE.read_text(encoding='utf-8').strip()
            path = Path(saved)
            if path.exists():
                return path
        except Exception:
            pass
    return None


def save_cached_path(path: Path):
    """Save found UmaExtractor path for next time."""
    try:
        CACHED_PATH_FILE.write_text(str(path), encoding='utf-8')
    except Exception:
        pass


def check_folder_for_extractor(base_path: Path) -> Path | None:
    """Check a single folder for UmaExtractor exe or script."""
    if not base_path.exists():
        return None
    
    # Check standard layout: base/py/dist/UmaExtractor.exe
    exe_path = base_path / "py" / "dist" / "UmaExtractor.exe"
    if exe_path.exists():
        return exe_path
    
    # Check root (exe placed directly in folder)
    exe_path = base_path / "UmaExtractor.exe"
    if exe_path.exists():
        return exe_path
    
    # Check for Python script as fallback
    script_path = base_path / "py" / "extract_umas.py"
    if script_path.exists():
        return script_path
    
    return None


def recursive_search(search_dir: Path, max_depth: int = 4) -> Path | None:
    """Recursively search a directory for UmaExtractor.exe up to max_depth levels."""
    if not search_dir.exists() or not search_dir.is_dir():
        return None
    
    try:
        for entry in search_dir.iterdir():
            if entry.is_file() and entry.name.lower() == 'umaextractor.exe':
                return entry
        
        if max_depth > 0:
            for entry in search_dir.iterdir():
                if entry.is_dir() and not entry.name.startswith('.'):
                    result = recursive_search(entry, max_depth - 1)
                    if result:
                        return result
    except PermissionError:
        pass
    
    return None


def find_umaextractor() -> Path | None:
    """Search for UmaExtractor installation in common locations."""
    
    # 1. Check cached path first (from previous run or launcher locate)
    cached = load_cached_path()
    if cached:
        print(f"  [cached] {cached}")
        return cached
    
    # 2. Fast path: check known exact locations
    home = Path.home()
    known_paths = [
        SCRIPT_DIR.parent / "UmaExtractor",
        home / "Downloads" / "UmaExtractor",
        home / "Desktop" / "UmaExtractor",
        home / "Documents" / "UmaExtractor",
        home / "Dev" / "UmaExtractor",
        Path("C:/Program Files/UmaExtractor"),
        Path("C:/Program Files (x86)/UmaExtractor"),
        Path("C:/UmaExtractor"),
        Path("D:/UmaExtractor"),
    ]
    
    for base_path in known_paths:
        result = check_folder_for_extractor(base_path)
        if result:
            save_cached_path(result)
            return result
    
    # 3. Deep search: recursively scan common directories for nested extracts
    print("  Not in standard locations, scanning folders (this may take a moment)...")
    deep_search_dirs = [
        SCRIPT_DIR.parent,
        home / "Downloads",
        home / "Desktop",
        home / "Documents",
    ]
    
    # Also search OneDrive paths if present
    onedrive = home / "OneDrive"
    if onedrive.exists():
        deep_search_dirs.append(onedrive / "Desktop")
        deep_search_dirs.append(onedrive / "Documents")
        deep_search_dirs.append(onedrive / "Downloads")
        # Scan top-level OneDrive for any Desktop-like folders (handles localized names)
        try:
            for entry in onedrive.iterdir():
                if entry.is_dir() and entry not in deep_search_dirs:
                    deep_search_dirs.append(entry)
        except PermissionError:
            pass
    
    for search_dir in deep_search_dirs:
        result = recursive_search(search_dir, max_depth=4)
        if result:
            save_cached_path(result)
            return result
    
    return None


def run_extractor(extractor_path: Path, auto_confirm: bool = False) -> bool:
    """Run UmaExtractor and output data.json to the script directory."""
    
    print(f"Found UmaExtractor: {extractor_path}")
    print(f"Output directory: {SCRIPT_DIR}\n")
    
    # Check if game is likely running
    print("=" * 50)
    print("IMPORTANT: Before continuing, make sure:")
    print("  1. Uma Musume Pretty Derby is RUNNING")
    print("  2. You are on the VETERAN LIST page (Enhance -> List)")
    print("  3. The page has FULLY LOADED")
    print("=" * 50)
    
    if not auto_confirm:
        response = input("\nReady to extract? [Y/n]: ").strip().lower()
        if response and response not in ('y', 'yes'):
            print("Extraction cancelled.")
            return False
    else:
        print("\n[Auto-confirm enabled, starting extraction...]")
    
    print()
    
    # Determine how to run the extractor
    if extractor_path.suffix.lower() == '.exe':
        # Run the exe from our directory so data.json is created here
        print(f"Running {extractor_path.name}...")
        print("(This may take up to 60 seconds)\n")
        
        # Set PYTHONIOENCODING in case the exe is a PyInstaller bundle
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8:replace'
        
        try:
            result = subprocess.run(
                [str(extractor_path)],
                cwd=str(SCRIPT_DIR),
                capture_output=False,  # Let output stream to console
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
            )
            
            # Check if data.json was created
            data_json = SCRIPT_DIR / "data.json"
            if data_json.exists():
                size_mb = data_json.stat().st_size / (1024 * 1024)
                print(f"\n[SUCCESS] Created {data_json}")
                print(f"          Size: {size_mb:.2f} MB")
                return True
            else:
                print("\n[ERROR] data.json was not created")
                print("        Check the error messages above")
                return False
                
        except FileNotFoundError:
            print(f"[ERROR] Could not find executable: {extractor_path}")
            return False
        except PermissionError:
            print("[ERROR] Permission denied. Try running as Administrator.")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to run extractor: {e}")
            return False
    
    elif extractor_path.suffix.lower() == '.py':
        # Run the Python script
        print(f"Running {extractor_path.name} via Python...")
        print("(This requires 'frida' and 'msgpack' packages)")
        print("(This may take up to 60 seconds)\n")
        
        # Set PYTHONIOENCODING to force UTF-8 output from UmaExtractor
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8:replace'
        
        try:
            result = subprocess.run(
                [sys.executable, str(extractor_path)],
                cwd=str(SCRIPT_DIR),
                capture_output=False,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
            )
            
            data_json = SCRIPT_DIR / "data.json"
            if data_json.exists():
                size_mb = data_json.stat().st_size / (1024 * 1024)
                print(f"\n[SUCCESS] Created {data_json}")
                print(f"          Size: {size_mb:.2f} MB")
                return True
            else:
                print("\n[ERROR] data.json was not created")
                return False
                
        except Exception as e:
            print(f"[ERROR] Failed to run extractor: {e}")
            return False
    
    else:
        print(f"[ERROR] Unknown extractor type: {extractor_path}")
        return False


def main():
    print("=== Uma Parent Viewer - Data Extractor Launcher ===\n")
    
    # Parse arguments
    auto_confirm = "--yes" in sys.argv or "-y" in sys.argv
    
    # Find UmaExtractor
    print("Searching for UmaExtractor installation...")
    extractor_path = find_umaextractor()
    
    if not extractor_path:
        print("\n[ERROR] UmaExtractor.exe not found!")
        print("\nSearched recursively in:")
        print(f"  - {SCRIPT_DIR.parent}")
        print(f"  - {Path.home() / 'Downloads'}")
        print(f"  - {Path.home() / 'Desktop'}")
        print(f"  - {Path.home() / 'Documents'}")
        print(f"  - OneDrive folders (if present)")
        print("\nHow to fix:")
        print("  1. Use the 'Locate' button in the launcher to browse to UmaExtractor.exe")
        print("  2. Or place the UmaExtractor folder next to this one")
        print(f"     (put it at: {SCRIPT_DIR.parent / 'UmaExtractor'})")
        print("  3. Download UmaExtractor: https://github.com/xancia/UmaExtractor/releases")
        sys.exit(1)
    
    # Run the extractor
    success = run_extractor(extractor_path, auto_confirm=auto_confirm)
    
    if success:
        print("\n" + "=" * 50)
        print("Next step: Run the enrichment script:")
        print(f"  python enrich_data.py")
        print("=" * 50)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
