# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
# ]
# ///
"""
One-time data generation script.

Downloads UmaTL text_data_dict.json, applies Global terminology corrections,
and outputs clean local JSON files that replace the UmaTL runtime dependency.

After running, review and correct the generated files as needed.
The enricher will then load from these local files instead of downloading.

Usage:
    python generate_data.py

Output files in data/:
    sparknames_global.json  — Spark display names (replaces category 147)
    racenames_global.json   — Race names (replaces category 36)
    outfitnames_global.json — Outfit names (replaces category 14)
    supportcardnames_global.json — Support card names (replaces categories 75/76/77)
    racetitles_global.json  — Race win/trophy names (replaces category 111)
    nicknames_global.json   — Epithets/nicknames (replaces categories 130/151)
"""

import json
import sys
from pathlib import Path

# Fix Unicode output on Windows consoles
if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr:
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

try:
    import requests
except ImportError:
    import subprocess
    print("Installing required dependency: requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "requests"])
    import requests

TEXT_DATA_URL = "https://raw.githubusercontent.com/UmaTL/hachimi-tl-en/main/localized_data/text_data_dict.json"

DATA_DIR = Path(__file__).parent / "data"

# ---------- Corrections ----------
# These map UmaTL community translations to official Global terms.
# Applied to spark names (category 147) and race names (category 36).

SPARK_NAME_CORRECTIONS = {
    # Running style aptitudes
    "Runner": "Front Runner",
    "Leader": "Pace Chaser",
    "Betweener": "Late Surger",
    "Chaser": "End Closer",

    # Track condition skills
    "Bad Track Condition ○": "Wet Conditions ○",
    "Bad Track Condition ◎": "Wet Conditions ◎",
    "Bad Track Condition ×": "Wet Conditions ×",

    # Running style specific skills
    "Frontrunner": "Early Lead",
    "Runner's Corners ○": "Front Runner Corners ○",
    "Runner's Corners ◎": "Front Runner Corners ◎",
    "Runner's Straights ○": "Front Runner Straightaways ○",
    "Runner's Straights ◎": "Front Runner Straightaways ◎",
    "Runner's Tricks ○": "Front Runner Savvy ○",
    "Runner's Tricks ◎": "Front Runner Savvy ◎",
    "Leader's Corners ○": "Pace Chaser Corners ○",
    "Leader's Corners ◎": "Pace Chaser Corners ◎",
    "Leader's Straights ○": "Pace Chaser Straightaways ○",
    "Leader's Straights ◎": "Pace Chaser Straightaways ◎",
    "Leader's Tricks ○": "Pace Chaser Savvy ○",
    "Leader's Tricks ◎": "Pace Chaser Savvy ◎",
    "Betweener's Corners ○": "Late Surger Corners ○",
    "Betweener's Corners ◎": "Late Surger Corners ◎",
    "Betweener's Straights ○": "Late Surger Straightaways ○",
    "Betweener's Straights ◎": "Late Surger Straightaways ◎",
    "Betweener's Tricks ○": "Late Surger Savvy ○",
    "Betweener's Tricks ◎": "Late Surger Savvy ◎",
    "Chaser's Corners ○": "End Closer Corners ○",
    "Chaser's Corners ◎": "End Closer Corners ◎",
    "Chaser's Straights ○": "End Closer Straightaways ○",
    "Chaser's Straights ◎": "End Closer Straightaways ◎",
    "Chaser's Tricks ○": "End Closer Savvy ○",
    "Chaser's Tricks ◎": "End Closer Savvy ◎",

    # Debuff skills
    "Frantic Runners": "Frenzied Front Runners",
    "Restrained Runners": "Subdued Front Runners",
    "Panicked Runners": "Flustered Front Runners",
    "Faltering Runners": "Hesitant Front Runners",
    "Frantic Leaders": "Frenzied Pace Chasers",
    "Restrained Leaders": "Subdued Pace Chasers",
    "Panicked Leaders": "Flustered Pace Chasers",
    "Faltering Leaders": "Hesitant Pace Chasers",
    "Frantic Betweeners": "Frenzied Late Surgers",
    "Restrained Betweeners": "Subdued Late Surgers",
    "Panicked Betweeners": "Flustered Late Surgers",
    "Faltering Betweeners": "Hesitant Late Surgers",
    "Frantic Chasers": "Frenzied End Closers",
    "Restrained Chasers": "Subdued End Closers",
    "Panicked Chasers": "Flustered End Closers",
    "Faltering Chasers": "Hesitant End Closers",

    # Common skill name differences
    "Position Swiper": "Position Pilfer",
    "100K Horsepower": "1,500,000 CC",
    "1M Horsepower": "15,000,000 CC",
    "Blue Rose Chaser": "Blue Rose Closer",
    "Backup Belly": "Extra Tank",
    "Big Strides": "Furious Feat",
    "Autumn Girl ○": "Fall Runner ○",
    "Autumn Girl ◎": "Fall Runner ◎",
    "Autumn Girl ×": "Fall Runner ×",

    # Spark names where UmaTL diverges from Global
    "Hold Your Tail High": "Tail Held High",

    # Stat name
    "Wisdom": "Wit",
}

NICKNAME_CORRECTIONS = {
    "Int Bonus": "Wit Bonus",
    "Int Cap Up": "Wit Cap Up",
}


def apply_corrections(name: str, corrections: dict) -> str:
    """Apply terminology corrections: exact match first, then partial."""
    if not name:
        return name

    if name in corrections:
        return corrections[name]

    corrected = name
    for wrong, right in corrections.items():
        if wrong in corrected:
            corrected = corrected.replace(wrong, right)
    return corrected


def download_text_data() -> dict:
    """Download UmaTL text_data_dict.json."""
    print(f"Downloading UmaTL text_data_dict.json...")
    response = requests.get(TEXT_DATA_URL, timeout=60)
    response.raise_for_status()
    data = response.json()
    print(f"  [OK] {len(data)} categories")
    return data


def generate_sparknames(text_data: dict) -> dict:
    """Extract category 147 and apply corrections -> sparknames_global.json"""
    cat_147 = text_data.get("147", {})
    result = {}
    corrected_count = 0

    for spark_id, name in cat_147.items():
        corrected = apply_corrections(name, SPARK_NAME_CORRECTIONS)
        if corrected != name:
            corrected_count += 1
        result[spark_id] = corrected

    print(f"  sparknames_global.json: {len(result)} entries, {corrected_count} corrected")
    return result


def generate_racenames(text_data: dict) -> dict:
    """Extract category 36 -> racenames_global.json"""
    cat_36 = text_data.get("36", {})
    result = {}

    for text_id, name in cat_36.items():
        corrected = apply_corrections(name, SPARK_NAME_CORRECTIONS)
        result[text_id] = corrected

    print(f"  racenames_global.json: {len(result)} entries")
    return result


def generate_outfitnames(text_data: dict) -> dict:
    """Extract category 14 -> outfitnames_global.json"""
    cat_14 = text_data.get("14", {})
    print(f"  outfitnames_global.json: {len(cat_14)} entries")
    return dict(cat_14)


def generate_supportcardnames(text_data: dict) -> dict:
    """Extract categories 75/76/77 -> supportcardnames_global.json

    Output format: { "card_id": { "name": "...", "title": "...", "chara": "..." } }
    """
    cat_75 = text_data.get("75", {})
    cat_76 = text_data.get("76", {})
    cat_77 = text_data.get("77", {})

    all_ids = set(cat_75.keys()) | set(cat_76.keys()) | set(cat_77.keys())
    result = {}

    for card_id in sorted(all_ids):
        entry = {}
        if card_id in cat_75:
            entry["name"] = cat_75[card_id]
        if card_id in cat_76:
            entry["title"] = cat_76[card_id]
        if card_id in cat_77:
            entry["chara"] = cat_77[card_id]
        result[card_id] = entry

    print(f"  supportcardnames_global.json: {len(result)} entries")
    return result


def generate_racetitles(text_data: dict) -> dict:
    """Extract category 111 -> racetitles_global.json"""
    cat_111 = text_data.get("111", {})
    result = {}

    for saddle_id, name in cat_111.items():
        cleaned = name.replace('\n', ' ').strip()
        result[saddle_id] = cleaned

    print(f"  racetitles_global.json: {len(result)} entries")
    return result


def generate_nicknames(text_data: dict) -> dict:
    """Extract categories 130/151 -> nicknames_global.json

    Output format: { "nickname_id": "Name" }
    Category 151 has support card bonuses (IDs 1-32).
    Category 130 has earned epithets (IDs 33+).
    """
    cat_130 = text_data.get("130", {})
    cat_151 = text_data.get("151", {})

    result = {}

    # Category 151 first (support card bonuses)
    for nick_id, name in cat_151.items():
        corrected = apply_corrections(name, NICKNAME_CORRECTIONS)
        result[nick_id] = corrected

    # Category 130 (earned epithets) — these override if overlapping
    for nick_id, name in cat_130.items():
        corrected = apply_corrections(name, NICKNAME_CORRECTIONS)
        result[nick_id] = corrected

    print(f"  nicknames_global.json: {len(result)} entries")
    return result


def save_json(data: dict, filename: str):
    """Save JSON to data/ directory."""
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"    -> saved {path}")


def main():
    print("=" * 50)
    print("  Generate Local Data Files")
    print("=" * 50)
    print()

    DATA_DIR.mkdir(exist_ok=True)

    text_data = download_text_data()
    print()
    print("Generating corrected data files...")

    generators = [
        (generate_sparknames, "sparknames_global.json"),
        (generate_racenames, "racenames_global.json"),
        (generate_outfitnames, "outfitnames_global.json"),
        (generate_supportcardnames, "supportcardnames_global.json"),
        (generate_racetitles, "racetitles_global.json"),
        (generate_nicknames, "nicknames_global.json"),
    ]

    for gen_fn, filename in generators:
        data = gen_fn(text_data)
        save_json(data, filename)

    print()
    print("[OK] All data files generated in data/")
    print()
    print("Review the generated files and correct any remaining non-Global terms.")
    print("The enricher will now load from these local files instead of UmaTL.")


if __name__ == "__main__":
    main()
