"""
Tests for guitar_theory module
"""
import pytest
from guitar_theory import generate_tab, SCALES, TUNINGS


class TestScales:
    """Test scale definitions"""

    def test_phrygian_intervals(self):
        """Phrygian should have flat 2nd (semitone from root)"""
        assert "phrygian" in SCALES
        phrygian = SCALES["phrygian"]
        # Phrygian intervals: 1, b2, b3, 4, 5, b6, b7
        # As semitones from root: 0, 1, 3, 5, 7, 8, 10
        assert phrygian[1] == 1  # flat 2nd is 1 semitone

    def test_major_intervals(self):
        """Major scale should have correct intervals"""
        assert "major" in SCALES
        major = SCALES["major"]
        # Major intervals: 0, 2, 4, 5, 7, 9, 11
        assert major[0] == 0
        assert major[1] == 2
        assert major[2] == 4

    def test_pentatonic_minor_has_5_notes(self):
        """Pentatonic scales should have 5 notes"""
        assert "pentatonic_minor" in SCALES
        assert len(SCALES["pentatonic_minor"]) == 5


class TestTunings:
    """Test tuning definitions"""

    def test_standard_tuning(self):
        """Standard tuning should be EADGBE"""
        assert "standard" in TUNINGS
        standard = TUNINGS["standard"]
        # Standard tuning in MIDI notes (low to high): E2, A2, D3, G3, B3, E4
        assert len(standard) == 6

    def test_drop_d_tuning(self):
        """Drop D should have low string dropped to D"""
        assert "drop_d" in TUNINGS
        drop_d = TUNINGS["drop_d"]
        # Drop D has low string as D instead of E
        assert drop_d[0] == "D"
        # Other strings remain the same as standard
        assert drop_d[1:] == TUNINGS["standard"][1:]


class TestTabGeneration:
    """Test tab generation function"""

    def test_generate_tab_returns_string(self):
        tab = generate_tab(root="E", scale="phrygian", pattern="ascending")
        assert isinstance(tab, str)
        assert len(tab) > 0

    def test_generate_tab_contains_six_strings(self):
        tab = generate_tab(root="E", scale="phrygian", pattern="ascending")
        lines = [l for l in tab.split('\n') if l.strip()]
        # Should have 6 string lines
        string_lines = [l for l in lines if '|' in l]
        assert len(string_lines) >= 6

    def test_generate_tab_different_patterns(self):
        """Different patterns should produce different tabs"""
        ascending = generate_tab(root="E", scale="phrygian", pattern="ascending")
        descending = generate_tab(root="E", scale="phrygian", pattern="descending")
        assert ascending != descending

    def test_generate_tab_different_scales(self):
        """Different scales should produce different notes"""
        phrygian = generate_tab(root="E", scale="phrygian", pattern="ascending")
        major = generate_tab(root="E", scale="major", pattern="ascending")
        assert phrygian != major

    def test_generate_tab_different_roots(self):
        """Different root notes should produce different tabs"""
        e_tab = generate_tab(root="E", scale="phrygian", pattern="ascending")
        a_tab = generate_tab(root="A", scale="phrygian", pattern="ascending")
        assert e_tab != a_tab

    def test_generate_pedal_pattern(self):
        """Pedal pattern should work"""
        tab = generate_tab(root="E", scale="phrygian", pattern="pedal")
        assert isinstance(tab, str)
        assert len(tab) > 0

    def test_generate_arpeggio_pattern(self):
        """Arpeggio pattern should work"""
        tab = generate_tab(root="E", scale="minor", pattern="arpeggio")
        assert isinstance(tab, str)
        assert len(tab) > 0
