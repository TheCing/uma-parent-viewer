"""
Tests for the enrichment pipeline — validates spark name resolution,
skill classification, and Global terminology correctness.

Covers past regression cases:
- Unique sparks must always resolve to the base (white/unevolved) unique skill name
- Alt outfit unique sparks must NOT use the alt outfit's evolved name
- Skill sparks must use spark display names, not skill names
- Running style / debuff corrections are baked into the data
- Nickname/epithet corrections are baked into the data

Run:
    python -m pytest test_enricher.py -v
    (or just: python test_enricher.py)
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from enrich_data import (
    get_spark_name,
    get_skill_name,
    get_skill_type,
    get_nickname_name,
    get_race_cloth_name,
    load_all_data,
)

DATA_DIR = Path(__file__).parent / "data"


def _load_ref_data() -> dict:
    """Load reference data once for all tests (suppresses print output)."""
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        data = load_all_data()
    finally:
        sys.stdout = old_stdout
    return data


# Load once at module level so tests are fast
REF = _load_ref_data()


# ---------------------------------------------------------------------------
# Unique spark resolution
# ---------------------------------------------------------------------------

class TestUniqueSparks(unittest.TestCase):
    """Unique sparks (10XXXXXXXX format) must always resolve to the
    base (white/unevolved) unique skill, regardless of outfit variant."""

    def test_oguri_cap_base_unique(self):
        """Oguri Cap [Starlight Beat] unique spark → Triumphant Pulse."""
        # Spark 10060101: Oguri Cap (char index 060), base outfit (V=1), 1-star
        self.assertEqual(get_spark_name(REF, 10060101), "Triumphant Pulse")

    def test_oguri_cap_alt_unique(self):
        """Oguri Cap [Ashen Miracle] unique spark → Festive Miracle (alt unique)."""
        # Spark 10060201: Oguri Cap (char index 060), alt outfit (V=2), 1-star
        self.assertEqual(get_spark_name(REF, 10060201), "Festive Miracle")

    def test_maruzensky_base_unique(self):
        """Maruzensky [Formula R] unique spark → Red Shift/LP1211-M."""
        self.assertEqual(get_spark_name(REF, 10040101), "Red Shift/LP1211-M")

    def test_maruzensky_alt_unique(self):
        """Maruzensky [Hot Summer Night] unique spark → A Kiss for Courage (alt unique)."""
        self.assertEqual(get_spark_name(REF, 10040201), "A Kiss for Courage")

    def test_special_week_unique(self):
        """Special Week unique spark → Shooting Star."""
        self.assertEqual(get_spark_name(REF, 10010101), "Shooting Star")

    def test_unique_spark_star_levels(self):
        """All star levels (1-3) of a unique spark return the same name."""
        for stars in (1, 2, 3):
            spark_id = 10060100 + stars  # Oguri Cap base, star 1/2/3
            name = get_spark_name(REF, spark_id)
            self.assertEqual(name, "Triumphant Pulse",
                             f"Star level {stars} gave '{name}'")


# ---------------------------------------------------------------------------
# Skill spark resolution — must use spark display names, not skill names
# ---------------------------------------------------------------------------

class TestSkillSparks(unittest.TestCase):
    """Skill sparks (200XXXX format) must display the WHITE skill name
    from skillnames_global.json (rarity=1 in skill_data.json).
    They must NOT use UmaTL spark names or gold skill names."""

    def test_corner_recovery(self):
        """Spark 2003501 → 'Corner Recovery ○' (white skill name).
        Must NOT be 'Swinging Maestro' (gold) or UmaTL spark name."""
        self.assertEqual(get_spark_name(REF, 2003501), "Corner Recovery ○")

    def test_nimble_navigator(self):
        """Spark 2004901 → 'Nimble Navigator' (white skill name).
        Must NOT be 'No Stopping Me!' (gold) or 'Slight Detour' (UmaTL)."""
        self.assertEqual(get_spark_name(REF, 2004901), "Nimble Navigator")

    def test_slick_surge(self):
        """Spark 2006001 → 'Slick Surge' (white skill name).
        Must NOT be 'On Your Left!' (gold) or 'Between the Lines' (UmaTL)."""
        self.assertEqual(get_spark_name(REF, 2006001), "Slick Surge")

    def test_skill_spark_star_levels(self):
        """All star levels of a skill spark return the same name."""
        for stars in (1, 2, 3):
            spark_id = 2004900 + stars
            self.assertEqual(get_spark_name(REF, spark_id), "Nimble Navigator",
                             f"Star level {stars} mismatch")

    def test_tail_held_high(self):
        """Spark 2016101 → 'Tail Held High' (white skill name from Global).
        Must NOT be 'Hold Your Tail High' (UmaTL community translation)."""
        self.assertEqual(get_spark_name(REF, 2016101), "Tail Held High")

    def test_position_pilfer(self):
        """Spark 2005901 → 'Position Pilfer' (white skill name from Global)."""
        self.assertEqual(get_spark_name(REF, 2005901), "Position Pilfer")


# ---------------------------------------------------------------------------
# Running style / terminology corrections baked into sparknames data
# ---------------------------------------------------------------------------

class TestGlobalTerminology(unittest.TestCase):
    """Verify that generated data files use official Global terms,
    not UmaTL community translations."""

    def test_no_betweener_in_sparknames(self):
        """No spark name should contain 'Betweener' (should be 'Late Surger')."""
        sparknames = REF.get("sparknames", {})
        bad = [v for v in sparknames.values() if "Betweener" in v]
        self.assertEqual(bad, [], f"Found non-Global terms: {bad[:5]}")

    def test_no_runner_as_running_style_in_sparknames(self):
        """No spark name should be exactly 'Runner' (should be 'Front Runner').
        Note: 'Runner' can appear as part of other names like 'Fall Runner'."""
        sparknames = REF.get("sparknames", {})
        bad = [v for v in sparknames.values() if v == "Runner"]
        self.assertEqual(bad, [], f"Found non-Global terms: {bad[:5]}")

    def test_no_leader_as_running_style_in_sparknames(self):
        """No spark name should be exactly 'Leader' (should be 'Pace Chaser')."""
        sparknames = REF.get("sparknames", {})
        bad = [v for v in sparknames.values() if v == "Leader"]
        self.assertEqual(bad, [], f"Found non-Global terms: {bad[:5]}")

    def test_no_chaser_as_running_style_in_sparknames(self):
        """No spark name should be exactly 'Chaser' (should be 'End Closer')."""
        sparknames = REF.get("sparknames", {})
        bad = [v for v in sparknames.values() if v == "Chaser"]
        self.assertEqual(bad, [], f"Found non-Global terms: {bad[:5]}")

    def test_no_bad_track_condition(self):
        """No spark name should contain 'Bad Track Condition' (should be 'Wet Conditions')."""
        sparknames = REF.get("sparknames", {})
        bad = [v for v in sparknames.values() if "Bad Track Condition" in v]
        self.assertEqual(bad, [], f"Found non-Global terms: {bad[:5]}")

    def test_no_wisdom_in_sparknames(self):
        """No spark name should contain 'Wisdom' (should be 'Wit')."""
        sparknames = REF.get("sparknames", {})
        bad = [v for v in sparknames.values() if "Wisdom" in v]
        self.assertEqual(bad, [], f"Found non-Global terms: {bad[:5]}")

    def test_wet_conditions_exists(self):
        """Verify 'Wet Conditions ○' is present (the corrected form)."""
        sparknames = REF.get("sparknames", {})
        has_wet = any("Wet Conditions" in v for v in sparknames.values())
        self.assertTrue(has_wet, "No 'Wet Conditions' spark found")

    def test_front_runner_exists(self):
        """Verify 'Front Runner' running style is present."""
        sparknames = REF.get("sparknames", {})
        has_fr = any(v == "Front Runner" for v in sparknames.values())
        self.assertTrue(has_fr, "No 'Front Runner' spark found")


# ---------------------------------------------------------------------------
# Skill classification
# ---------------------------------------------------------------------------

class TestSkillClassification(unittest.TestCase):
    """Skill type classification must correctly identify unique skills
    for both base outfits (10XXXX) and alternate outfits (11XXXX)."""

    def test_base_unique_classified(self):
        """100061 (Oguri Cap base unique) → 'unique'."""
        self.assertEqual(get_skill_type(100061, []), "unique")

    def test_alt_unique_classified(self):
        """110061 (Oguri Cap alt unique) → 'unique'."""
        self.assertEqual(get_skill_type(110061, []), "unique")

    def test_inherited_base_classified(self):
        """900061 (inherited base unique) → 'inherited'."""
        self.assertEqual(get_skill_type(900061, []), "inherited")

    def test_inherited_alt_classified(self):
        """910061 (inherited alt unique) → 'inherited'."""
        self.assertEqual(get_skill_type(910061, []), "inherited")

    def test_normal_skill_not_unique(self):
        """200601 (a regular skill) → not classified as unique."""
        result = get_skill_type(200601, [])
        self.assertNotIn(result, ("unique", "inherited"))


# ---------------------------------------------------------------------------
# Outfit names
# ---------------------------------------------------------------------------

class TestOutfitNames(unittest.TestCase):
    """Outfit name lookup from outfitnames_global.json."""

    def test_outfit_name_exists(self):
        """A known outfit ID returns a name."""
        name = get_race_cloth_name(REF, 901006)
        self.assertIsNotNone(name)
        self.assertIn("Oguri Cap", name)


# ---------------------------------------------------------------------------
# Nickname corrections
# ---------------------------------------------------------------------------

class TestNicknames(unittest.TestCase):
    """Nickname/epithet lookup from nicknames_global.json."""

    def test_nickname_returns_value(self):
        """Known nickname IDs return a string."""
        name = get_nickname_name(REF, 1)
        self.assertIsNotNone(name)

    def test_no_int_bonus_in_nicknames(self):
        """No nickname should say 'Int Bonus' (should be 'Wit Bonus')."""
        nicknames = REF.get("nicknames", {})
        bad = [v for v in nicknames.values() if "Int Bonus" in v or "Int Cap Up" in v]
        self.assertEqual(bad, [], f"Found non-Global terms: {bad}")


# ---------------------------------------------------------------------------
# Data integrity
# ---------------------------------------------------------------------------

class TestDataIntegrity(unittest.TestCase):
    """Verify all bundled data files loaded successfully."""

    def test_all_data_loaded(self):
        """All 11 expected data keys should be present and non-empty."""
        expected = [
            "skills_global", "skills_jp", "skill_data",
            "umas_global", "umas_full",
            "sparknames", "racenames", "outfitnames",
            "supportcardnames", "racetitles", "nicknames",
        ]
        for key in expected:
            with self.subTest(key=key):
                self.assertIn(key, REF, f"Missing data key: {key}")
                self.assertTrue(len(REF[key]) > 0, f"Empty data: {key}")

    def test_sparknames_has_entries(self):
        """sparknames_global.json should have 2000+ entries."""
        self.assertGreater(len(REF.get("sparknames", {})), 2000)

    def test_skillnames_global_has_entries(self):
        """skillnames_global.json should have 600+ entries."""
        self.assertGreater(len(REF.get("skills_global", {})), 600)


if __name__ == "__main__":
    unittest.main(verbosity=2)
