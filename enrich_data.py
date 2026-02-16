# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Enrich data.json with English names from bundled data files.

All reference data is loaded from the local data/ directory (no network needed).
To update reference data, run generate_data.py to refresh from upstream sources.

Usage:
    python enrich_data.py [input.json] [output.json]
    
If no arguments provided, reads data.json and writes enriched_data.json

Data sources (bundled in data/):
- uma-tools: skillnames, skill_data, umas (https://github.com/TheCing/uma-tools)
- Generated from UmaTL with Global corrections applied by generate_data.py
"""

import json
import sys
from pathlib import Path

# Fix Unicode output on Windows consoles
if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr:
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_DIR = SCRIPT_DIR / "data"

# Effect type mappings from uma-tools RaceSolver.ts
EFFECT_TYPES = {
    0: "No Effect",
    1: "Speed +",
    2: "Stamina +",
    3: "Power +",
    4: "Guts +",
    5: "Wit +",
    9: "Stamina Recovery",
    10: "Start Delay x",
    14: "Set Start Delay",
    21: "Current Speed +",
    22: "Current Speed + (w/ decel)",
    27: "Target Speed +",
    28: "Lane Move Speed +",
    31: "Acceleration +",
    35: "Change Lane",
    37: "Activate Random Gold",
    42: "Extend Evolved Duration",
}

# Condition term translations for human readability
CONDITION_TERMS = {
    "phase": {"0": "Opening Leg", "1": "Middle Leg", "2": "Final Leg"},
    "distance_rate": "% of race",
    "order": "position",
    "order_rate": "% of field",
    "running_style": {"1": "Front Runner", "2": "Pace Chaser", "3": "Late Surger", "4": "End Closer"},
    "corner": "corner",
    "is_lastspurt": "in last spurt",
    "is_finalcorner": "in final corner",
    "hp_per": "% HP",
    "activate_count_heal": "recovery skills used",
    "ground_type": {"1": "Turf", "2": "Dirt"},
    "distance_type": {"1": "Sprint", "2": "Mile", "3": "Medium", "4": "Long"},
}

# All terminology corrections are now pre-baked into the generated data files.
# Run generate_data.py to refresh from upstream with corrections applied.


def load_json(filename: str) -> dict:
    """Load a JSON file from the data/ directory."""
    path = DATA_DIR / filename
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  [OK] {filename} ({len(data)} entries)")
        return data
    except FileNotFoundError:
        print(f"  [!] Warning: {path} not found — run generate_data.py first")
        return {}
    except json.JSONDecodeError as e:
        print(f"  [!] Warning: Invalid JSON in {path}: {e}")
        return {}


def load_all_data() -> dict:
    """Load all reference data from local data/ directory."""
    if not DATA_DIR.exists():
        print(f"[!] data/ directory not found at {DATA_DIR}")
        print("    Run generate_data.py to create it.")
        return {}

    print("Loading reference data from data/...")
    data = {}

    # uma-tools data
    data["skills_global"] = load_json("skillnames_global.json")
    data["skills_jp"] = load_json("skillnames_jp.json")
    data["skill_data"] = load_json("skill_data.json")
    data["umas_global"] = load_json("umas_global.json")
    data["umas_full"] = load_json("umas_full.json")

    # Generated data (from UmaTL with Global corrections applied)
    data["sparknames"] = load_json("sparknames_global.json")
    data["racenames"] = load_json("racenames_global.json")
    data["outfitnames"] = load_json("outfitnames_global.json")
    data["supportcardnames"] = load_json("supportcardnames_global.json")
    data["racetitles"] = load_json("racetitles_global.json")
    data["nicknames"] = load_json("nicknames_global.json")

    return data


def parse_condition(condition: str) -> str:
    """Parse a skill condition string into human-readable format."""
    if not condition:
        return "Always"
    
    parts = []
    # Split by & (AND conditions)
    for term in condition.split("&"):
        term = term.strip()
        if not term:
            continue
        
        # Parse comparison operators
        for op in [">=", "<=", "==", "!=", ">", "<", "="]:
            if op in term:
                key, value = term.split(op, 1)
                key = key.strip()
                value = value.strip()
                
                # Translate known terms
                if key == "phase":
                    phase_names = CONDITION_TERMS.get("phase", {})
                    value_name = phase_names.get(value, f"Phase {value}")
                    if op in ("==", "="):
                        parts.append(value_name)
                    elif op == ">=":
                        parts.append(f"{value_name}+")
                    else:
                        parts.append(f"phase{op}{value}")
                elif key == "distance_rate":
                    if op == ">=":
                        parts.append(f"After {value}% of race")
                    elif op == "<=":
                        parts.append(f"Before {value}% of race")
                    else:
                        parts.append(f"{value}% of race")
                elif key == "order":
                    if op == "<=":
                        parts.append(f"Top {value}")
                    elif op == ">=":
                        parts.append(f"Position {value}+")
                    else:
                        parts.append(f"Position {value}")
                elif key == "order_rate":
                    if op == "<=":
                        parts.append(f"Top {value}%")
                    elif op == ">=":
                        parts.append(f"Back {100-int(value)}%")
                    else:
                        parts.append(f"{value}% of field")
                elif key == "running_style":
                    styles = CONDITION_TERMS.get("running_style", {})
                    parts.append(styles.get(value, f"Style {value}"))
                elif key == "corner":
                    if value == "0":
                        parts.append("Not in corner")
                    else:
                        parts.append(f"Corner {value}")
                elif key == "is_lastspurt" and value == "1":
                    parts.append("Last Spurt")
                elif key == "is_finalcorner" and value == "1":
                    parts.append("Final Corner")
                elif key == "hp_per":
                    if op == "<=":
                        parts.append(f"HP ≤{value}%")
                    elif op == ">=":
                        parts.append(f"HP ≥{value}%")
                    else:
                        parts.append(f"HP {value}%")
                elif key == "activate_count_heal":
                    parts.append(f"After {value} recovery skill(s)")
                elif key == "ground_type":
                    grounds = CONDITION_TERMS.get("ground_type", {})
                    parts.append(grounds.get(value, f"Ground {value}"))
                elif key == "distance_type":
                    dists = CONDITION_TERMS.get("distance_type", {})
                    parts.append(dists.get(value, f"Distance {value}"))
                elif key.endswith("_random") and value == "1":
                    # Random activation in specific area
                    area = key.replace("_random", "").replace("_", " ").title()
                    parts.append(f"Random in {area}")
                elif key == "always":
                    continue  # Skip "always" condition
                else:
                    # Generic fallback
                    readable_key = key.replace("_", " ").title()
                    parts.append(f"{readable_key} {op} {value}")
                break
        else:
            # No operator found, just add the term
            parts.append(term.replace("_", " ").title())
    
    return " & ".join(parts) if parts else "Always"


def format_effect(effect: dict) -> str:
    """Format a single skill effect into human-readable string."""
    etype = effect.get("type", 0)
    modifier = effect.get("modifier", 0)
    
    type_name = EFFECT_TYPES.get(etype, f"Effect {etype}")
    
    # Format modifier based on effect type
    if etype in (1, 2, 3, 4, 5):  # Stat buffs
        return f"{type_name}{modifier}"
    elif etype == 9:  # Recovery
        return f"Recover {modifier/100:.0f}% Stamina"
    elif etype in (21, 22, 27):  # Speed modifiers (stored as x10000)
        speed_val = modifier / 10000
        return f"{type_name}{speed_val:.2f}m/s"
    elif etype == 31:  # Acceleration (stored as x10000)
        accel_val = modifier / 10000
        return f"{type_name}{accel_val:.4f}"
    elif etype == 10:  # Start delay multiplier
        return f"Start Delay x{modifier}"
    else:
        return f"{type_name} ({modifier})"


def get_skill_type(skill_id: int | str, effects: list) -> str:
    """Determine the skill type/category for color coding.
    
    Types:
    - unique: Character-specific unique skill (10XXXX base outfit, 11XXXX alternate outfit)
    - inherited: Inherited unique from parent (90XXXX base, 91XXXX alternate)
    - gold: Gold rarity skills
    - green: Stat boost skills (effect types 1-5)
    - blue: Debuff skills (negative modifiers)
    - white: Normal skills
    """
    sid = str(skill_id)
    
    # Check for green skills first (stat boosts - effect types 1-5)
    effect_types = [e.get("type", 0) for e in effects]
    if any(t in [1, 2, 3, 4, 5] for t in effect_types):
        return "green"
    
    # Check for blue/debuff skills (negative modifiers)
    if any(e.get("modifier", 0) < 0 for e in effects):
        return "blue"
    
    # Check for unique skills (10XXXX base outfit, 11XXXX alternate outfit)
    if len(sid) == 6 and (sid.startswith("10") or sid.startswith("11")):
        return "unique"
    
    # Check for inherited uniques (90XXXX base, 91XXXX alternate)
    if len(sid) == 6 and (sid.startswith("90") or sid.startswith("91")):
        return "inherited"
    
    # Default based on data rarity will be set later
    return None


def get_skill_details(data: dict, skill_id: int | str) -> dict | None:
    """Get detailed skill information including conditions and effects."""
    skill_data = data.get("skill_data", {})
    skill_entry = skill_data.get(str(skill_id))
    
    if not skill_entry:
        return None
    
    result = {}
    
    # Get rarity from data
    rarity = skill_entry.get("rarity", 0)
    rarity_names = {1: "White", 2: "White", 3: "White", 4: "Gold", 5: "Gold", 6: "Unique"}
    result["rarity"] = rarity_names.get(rarity, f"Rarity {rarity}")
    
    # Process alternatives (different activation conditions for same skill)
    alternatives = skill_entry.get("alternatives", [])
    if alternatives:
        alt = alternatives[0]  # Usually just one
        
        # Condition
        condition = alt.get("condition", "")
        result["condition"] = condition
        result["condition_readable"] = parse_condition(condition)
        
        # Duration (in ms, stored as x1000 of seconds per 1000m)
        base_duration = alt.get("baseDuration", 0)
        if base_duration:
            # Duration scales with race distance: actual = baseDuration * (distance/1000) / 1000
            # For a 2000m race: actual = baseDuration * 2 / 1000
            result["duration_base_ms"] = base_duration
            result["duration_per_1000m"] = f"{base_duration/1000:.1f}s"
        
        # Effects
        effects = alt.get("effects", [])
        result["effects"] = []
        for eff in effects:
            effect_info = {
                "type": eff.get("type", 0),
                "type_name": EFFECT_TYPES.get(eff.get("type", 0), "Unknown"),
                "modifier": eff.get("modifier", 0),
                "readable": format_effect(eff)
            }
            result["effects"].append(effect_info)
        
        # Determine skill type for color coding
        skill_type = get_skill_type(skill_id, effects)
        if skill_type:
            result["skill_type"] = skill_type
        elif result["rarity"] == "Gold":
            result["skill_type"] = "gold"
        elif result["rarity"] == "Unique":
            result["skill_type"] = "unique"
        else:
            result["skill_type"] = "white"
        
        # Create a summary string
        effects_summary = ", ".join(e["readable"] for e in result["effects"])
        result["summary"] = f"{result['condition_readable']} → {effects_summary}"
    
    return result


def get_skill_name(data: dict, skill_id: int | str) -> str | None:
    """Look up skill name from skill ID.
    
    Tries Global names first (official EN), then falls back to JP data (community EN translations).
    """
    skill_id_str = str(skill_id)
    
    # Try Global names first (format: {"id": ["Name"]})
    skills_global = data.get("skills_global", {})
    entry = skills_global.get(skill_id_str)
    if entry and isinstance(entry, list) and len(entry) > 0:
        return entry[0]
    
    # Fall back to JP names (format: {"id": ["JP Name", "EN Name"]})
    skills_jp = data.get("skills_jp", {})
    entry = skills_jp.get(skill_id_str)
    if entry and isinstance(entry, list) and len(entry) > 1:
        return entry[1]  # Second element is EN name
    
    return None


def get_spark_name(data: dict, spark_id: int) -> str | None:
    """Decode spark ID to human-readable name (called "Factors" in JP, "Sparks" in Global).
    
    Spark ID encoding:
    - 1XX-5XX: Stats (Speed, Stamina, Power, Guts, Wit)
    - 11XX-12XX: Ground aptitude (Turf, Dirt)
    - 21XX-24XX: Running style (Front Runner, Pace Chaser, Late Surger, End Closer)
    - 31XX-34XX: Distance (Sprint, Mile, Medium, Long)
    - 100XXXXX: Unique skill sparks (8 digits)
    - 100XXXX: Race sparks (7 digits, XXXX = race program ID)
    - 200XXXX: Skill sparks (7 digits, derived from white skill name)
    - 3000XXX: Scenario sparks
    
    Name sources:
    - Unique sparks → skillnames_global.json (base or alt unique skill)
    - Skill sparks  → skillnames_global.json (white version, rarity=1)
    - Race sparks   → racenames_global.json
    - Everything else → sparknames_global.json (stat, distance, style, scenario, etc.)
    """
    # FIRST: Unique skill sparks (8 digits starting with 10)
    # Format: 10[XXX][V][ZZ] where XXX=char index, V=outfit variant (1=base, 2=alt), ZZ=star level
    # Each outfit has its own unique skill:
    #   V=1 (base): skill prefix 10XXXX (e.g., 100061 "Triumphant Pulse")
    #   V=2 (alt):  skill prefix 11XXXX (e.g., 110061 "Festive Miracle")
    if 10000000 <= spark_id < 20000000:
        spark_str = str(spark_id)
        if len(spark_str) == 8:
            middle = int(spark_str[2:5])
            variant = int(spark_str[5])
            if variant == 2:
                skill_id = 110001 + middle  # Alt outfit unique (11XXXX)
            else:
                skill_id = 100001 + middle  # Base outfit unique (10XXXX)
            skill_name = get_skill_name(data, skill_id)
            if skill_name:
                return skill_name
    
    # SECOND: Skill sparks (200XXXX format, 7 digits)
    # In Global, sparks always display the WHITE skill name.
    # Derive skill group from spark ID, find the white version (rarity=1),
    # and use its Global name from skillnames_global.json.
    if 2000000 <= spark_id < 3000000:
        # spark 200XXYY → skill group base 200XX0
        group_base = (spark_id // 100) * 10
        skill_data = data.get("skill_data", {})
        
        # Find the white skill (rarity=1) in this group
        for digit in range(1, 10):
            candidate_id = group_base + digit
            entry = skill_data.get(str(candidate_id), {})
            if entry.get("rarity") == 1:
                name = get_skill_name(data, candidate_id)
                if name:
                    return name
                break
        
        # Fallback: try any skill in the group from Global skillnames
        for digit in range(1, 10):
            candidate_id = group_base + digit
            name = get_skill_name(data, candidate_id)
            if name:
                return name
    
    # THIRD: Race sparks (100XXXX format, 7 digits)
    if 1000000 <= spark_id < 10000000:
        race_program_id = spark_id // 100
        racenames = data.get("racenames", {})
        text_race_id = 1000 + (race_program_id % 1000)
        race_name = racenames.get(str(text_race_id))
        if race_name:
            return race_name
    
    # FOURTH: Everything else (stats, distance, style, scenario, etc.)
    # These don't map to skill IDs — use sparknames_global.json
    sparknames = data.get("sparknames", {})
    spark_name = sparknames.get(str(spark_id))
    if spark_name:
        return spark_name
    
    return None


# Support card type mapping based on first digit of ID
SUPPORT_CARD_TYPES = {
    '1': 'Speed',
    '2': 'Stamina',
    '3': 'Power',
    '4': 'Guts',
    '5': 'Wit',      # Global uses "Wit" (not Wisdom)
    '6': 'Friend',
    '7': 'Group',
}


def get_race_title_name(data: dict, saddle_id: int) -> str | None:
    """Look up race/title name from saddle ID.
    
    Uses racetitles_global.json (pre-cleaned, newlines already stripped).
    """
    racetitles = data.get("racetitles", {})
    return racetitles.get(str(saddle_id))


def get_nickname_name(data: dict, nickname_id: int) -> str | None:
    """Look up epithet/bonus name from nickname ID.
    
    Uses nicknames_global.json (pre-corrected, merges categories 130 and 151).
    """
    nicknames = data.get("nicknames", {})
    return nicknames.get(str(nickname_id))


def get_race_cloth_name(data: dict, race_cloth_id: int) -> str | None:
    """Look up racing outfit/dress name from race_cloth_id.
    
    Uses outfitnames_global.json.
    """
    outfitnames = data.get("outfitnames", {})
    return outfitnames.get(str(race_cloth_id))


def get_support_card_info(data: dict, support_card_id: int) -> dict:
    """Look up support card info from ID.
    
    Uses supportcardnames_global.json (pre-merged from categories 75/76/77).
    
    Returns dict with:
    - support_card_name_en: Full name like "[Title] Character"
    - support_card_title_en: Just the title like "[Title]"
    - support_card_chara_en: Just the character like "Character"
    - support_card_type: Type like "Speed", "Stamina", etc.
    """
    result = {}
    supportcardnames = data.get("supportcardnames", {})
    sid_str = str(support_card_id)
    
    entry = supportcardnames.get(sid_str, {})
    if "name" in entry:
        result["support_card_name_en"] = entry["name"]
    if "title" in entry:
        result["support_card_title_en"] = entry["title"]
    if "chara" in entry:
        result["support_card_chara_en"] = entry["chara"]
    
    # Type from first digit of ID
    if sid_str:
        stype = SUPPORT_CARD_TYPES.get(sid_str[0])
        if stype:
            result["support_card_type"] = stype
    
    return result


def get_chara_info(data: dict, card_id: int) -> dict:
    """Get character info from card_id.
    
    card_id format: 1XXYYZ where:
    - 1XXY = chara_id (e.g., 1056 for Matikanefukukitaru)
    - Z = outfit variant (01, 02, etc.)
    """
    result = {}
    
    # Extract chara_id from card_id
    chara_id = str(card_id // 100)
    card_id_str = str(card_id)
    
    # Try global data first (has accurate English outfit names)
    umas_global = data.get("umas_global", {})
    if chara_id in umas_global:
        uma = umas_global[chara_id]
        names = uma.get("name", ["", ""])
        result["chara_name_en"] = names[1] if len(names) > 1 and names[1] else names[0]
        
        outfits = uma.get("outfits", {})
        if card_id_str in outfits:
            result["costume_name_en"] = outfits[card_id_str]
            result["card_name_en"] = f"{outfits[card_id_str]} {result['chara_name_en']}"
    
    # Fill in gaps from full data
    if "chara_name_en" not in result:
        umas_full = data.get("umas_full", {})
        if chara_id in umas_full:
            uma = umas_full[chara_id]
            names = uma.get("name", ["", ""])
            result["chara_name_en"] = names[1] if len(names) > 1 and names[1] else names[0]
            
            # Full data has JP outfit names but we can still use them as fallback
            outfits = uma.get("outfits", {})
            if card_id_str in outfits and "costume_name_en" not in result:
                result["costume_name_en"] = outfits[card_id_str]
                result["card_name_en"] = f"{outfits[card_id_str]} {result.get('chara_name_en', '')}"
    
    return result


def enrich_character(char: dict, data: dict) -> dict:
    """Add English names to a single character entry."""
    
    # Card/character info
    card_id = char.get("card_id")
    if card_id:
        info = get_chara_info(data, card_id)
        char.update(info)
    
    # Race cloth/outfit name
    race_cloth_id = char.get("race_cloth_id")
    if race_cloth_id:
        cloth_name = get_race_cloth_name(data, race_cloth_id)
        if cloth_name:
            char["race_cloth_name_en"] = cloth_name
    
    # Enrich skills
    skill_array = char.get("skill_array", [])
    for skill in skill_array:
        skill_id = skill.get("skill_id")
        if skill_id:
            skill_name = get_skill_name(data, skill_id)
            if skill_name:
                skill["skill_name_en"] = skill_name
            
            # Add skill details (condition, effects, duration)
            skill_details = get_skill_details(data, skill_id)
            if skill_details:
                skill["rarity"] = skill_details.get("rarity")
                skill["skill_type"] = skill_details.get("skill_type")
                skill["condition"] = skill_details.get("condition_readable")
                skill["effects"] = skill_details.get("effects", [])
                skill["duration"] = skill_details.get("duration_per_1000m")
                skill["summary"] = skill_details.get("summary")
    
    # Enrich sparks (called "Factors" in JP, "Sparks" in Global)
    factor_id_array = char.get("factor_id_array", [])
    enriched_sparks = []
    for spark_id in factor_id_array:
        spark_entry = {"spark_id": spark_id}
        spark_name = get_spark_name(data, spark_id)
        if spark_name:
            spark_entry["spark_name_en"] = spark_name
        # Extract star level from last 2 digits of spark_id
        star_level = int(str(spark_id)[-2:])
        if 1 <= star_level <= 3:
            spark_entry["stars"] = star_level
        enriched_sparks.append(spark_entry)
    if enriched_sparks:
        char["spark_array_enriched"] = enriched_sparks
    
    # Enrich factor_info_array (keep original key name for compatibility)
    factor_info_array = char.get("factor_info_array", [])
    for factor_info in factor_info_array:
        spark_id = factor_info.get("factor_id")
        if spark_id:
            spark_name = get_spark_name(data, spark_id)
            if spark_name:
                factor_info["spark_name_en"] = spark_name
    
    # Enrich win_saddle_id_array (race wins/trophies)
    win_saddle_array = char.get("win_saddle_id_array", [])
    if win_saddle_array:
        enriched_wins = []
        for saddle_id in win_saddle_array:
            win_entry = {"saddle_id": saddle_id}
            race_name = get_race_title_name(data, saddle_id)
            if race_name:
                win_entry["race_name_en"] = race_name
            enriched_wins.append(win_entry)
        char["win_saddle_array_enriched"] = enriched_wins
    
    # Enrich nickname_id_array (epithets and support bonuses)
    nickname_array = char.get("nickname_id_array", [])
    if nickname_array:
        enriched_nicknames = []
        for nickname_id in nickname_array:
            nick_entry = {"nickname_id": nickname_id}
            nick_name = get_nickname_name(data, nickname_id)
            if nick_name:
                nick_entry["nickname_name_en"] = nick_name
            enriched_nicknames.append(nick_entry)
        char["nickname_array_enriched"] = enriched_nicknames
    
    # Enrich support cards (using supportcardnames_global.json)
    support_list = char.get("support_card_list", [])
    for support in support_list:
        support_id = support.get("support_card_id")
        if support_id:
            support_info = get_support_card_info(data, support_id)
            support.update(support_info)
    
    # Enrich succession (parent) characters
    succession_array = char.get("succession_chara_array", [])
    for parent in succession_array:
        parent_card_id = parent.get("card_id")
        if parent_card_id:
            info = get_chara_info(data, parent_card_id)
            parent.update(info)
            
            # Enrich parent's sparks with names and star levels
            parent_sparks = parent.get("factor_info_array", [])
            for spark in parent_sparks:
                spark_id = spark.get("factor_id")
                if spark_id:
                    spark_name = get_spark_name(data, spark_id)
                    if spark_name:
                        spark["spark_name_en"] = spark_name
                    # Extract star level from last 2 digits
                    star_level = int(str(spark_id)[-2:])
                    if 1 <= star_level <= 3:
                        spark["stars"] = star_level
    
    return char


def enrich_data(input_path: Path, output_path: Path):
    """Main function to enrich the data file."""
    
    # Load input data
    print(f"Loading {input_path}...")
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            characters = json.load(f)
    except FileNotFoundError:
        print(f"[X] Error: {input_path} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[X] Error: Invalid JSON in {input_path}: {e}")
        sys.exit(1)
    
    if not isinstance(characters, list):
        print(f"[X] Error: Expected array of characters, got {type(characters)}")
        sys.exit(1)
    
    print(f"[OK] Loaded {len(characters)} characters\n")
    
    # Load reference data from local data/ directory
    data = load_all_data()
    
    if not data:
        print("\n[!] No reference data available, output will have IDs only")
    
    # Enrich each character
    print("\nEnriching character data...")
    enriched_count = 0
    skill_enriched = 0
    
    for char in characters:
        before_keys = set(char.keys())
        enrich_character(char, data)
        after_keys = set(char.keys())
        if after_keys - before_keys:
            enriched_count += 1
        if any(s.get("skill_name_en") for s in char.get("skill_array", [])):
            skill_enriched += 1
    
    print(f"  [OK] {enriched_count}/{len(characters)} characters with name data")
    print(f"  [OK] {skill_enriched}/{len(characters)} characters with skill names")
    
    # Save output
    print(f"\nSaving to {output_path}...")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(characters, f, indent=2, ensure_ascii=False)
        print(f"[OK] Saved enriched data to {output_path}")
    except PermissionError:
        print(f"[X] Error: Permission denied writing to {output_path}")
        sys.exit(1)
    
    # Show sample (with safe encoding for Windows console)
    if characters and data:
        sample = characters[0]
        
        def safe_print(text: str):
            """Print with fallback for non-ASCII chars on Windows."""
            try:
                print(text)
            except UnicodeEncodeError:
                print(text.encode("ascii", "replace").decode())
        
        print("\n--- Sample enriched character ---")
        safe_print(f"  card_id: {sample.get('card_id')}")
        safe_print(f"  chara_name_en: {sample.get('chara_name_en', 'N/A')}")
        safe_print(f"  costume_name_en: {sample.get('costume_name_en', 'N/A')}")
        safe_print(f"  card_name_en: {sample.get('card_name_en', 'N/A')}")
        
        skills = sample.get("skill_array", [])
        named_skills = [s for s in skills if s.get("skill_name_en")]
        if named_skills:
            safe_print(f"  skills with names: {len(named_skills)}/{len(skills)}")
            for skill in named_skills[:3]:
                safe_print(f"    - {skill.get('skill_name_en')} (Lv.{skill.get('level')})")
    
    print(f"\n[SUCCESS] Done!")
    
    # Run localization validator
    print("\n" + "=" * 50)
    print("Running localization check...")
    print("=" * 50 + "\n")
    
    try:
        from validate_localization import check_enriched_data, print_terminology_reference
        issues = check_enriched_data()
        if issues:
            print(f"[!] Found {len(issues)} localization issue(s) from upstream data:\n")
            for issue in issues[:5]:  # Show first 5
                print(f"  {issue['field']}")
                print(f"    '{issue['found']}' -> should be '{issue['expected']}'")
            if len(issues) > 5:
                print(f"\n  ... and {len(issues) - 5} more. Run 'python validate_localization.py' for full report.")
            print_terminology_reference()
        else:
            print("[OK] No localization issues found!")
    except ImportError:
        print("[!] validate_localization.py not found, skipping check")
    except Exception as e:
        print(f"[!] Localization check failed: {e}")


def main():
    # Parse arguments
    if len(sys.argv) >= 3:
        input_path = Path(sys.argv[1])
        output_path = Path(sys.argv[2])
    elif len(sys.argv) == 2:
        input_path = Path(sys.argv[1])
        output_path = input_path.parent / "enriched_data.json"
    else:
        # Default paths
        if Path("data.json").exists():
            input_path = Path("data.json")
        elif Path("../data.json").exists():
            input_path = Path("../data.json")
        else:
            print("Usage: python enrich_data.py [input.json] [output.json]")
            print("       If no arguments, reads data.json and writes enriched_data.json")
            sys.exit(1)
        output_path = input_path.parent / "enriched_data.json"
    
    enrich_data(input_path, output_path)


if __name__ == "__main__":
    main()
