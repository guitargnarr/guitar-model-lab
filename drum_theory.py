#!/usr/bin/env python3
"""
Drum Theory Module - Deterministic drum pattern generation for Guitar Pro

This module handles all music theory and pattern generation for drums.
AI models provide style interpretation, Python handles the actual note generation.

GP7 Drum MIDI Map (General MIDI):
- Kick: 36 (C1)
- Snare: 38 (D1)
- Snare Rim: 37 (C#1)
- Hi-Hat Closed: 42 (F#1)
- Hi-Hat Open: 46 (A#1)
- Hi-Hat Pedal: 44 (G#1)
- Ride: 51 (D#2)
- Ride Bell: 53 (F2)
- Crash 1: 49 (C#2)
- Crash 2: 57 (A2)
- Tom High: 50 (D2)
- Tom Mid: 47 (B1)
- Tom Low: 45 (A1)
- Floor Tom: 43 (G1)
- China: 52 (E2)
- Splash: 55 (G2)
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import random

# GP7 Drum MIDI note numbers
DRUM_MAP = {
    "kick": 36,
    "snare": 38,
    "snare_rim": 37,
    "snare_ghost": 38,  # Same as snare but lower velocity
    "hihat_closed": 42,
    "hihat_open": 46,
    "hihat_pedal": 44,
    "ride": 51,
    "ride_bell": 53,
    "crash1": 49,
    "crash2": 57,
    "tom_high": 50,
    "tom_mid": 47,
    "tom_low": 45,
    "floor_tom": 43,
    "china": 52,
    "splash": 55,
}

# Default velocities
VELOCITIES = {
    "accent": 127,
    "normal": 100,
    "ghost": 50,
    "soft": 70,
}


@dataclass
class DrumHit:
    """Represents a single drum hit."""
    position: int  # 1-16 for 16th notes in a bar
    drum: str      # Key from DRUM_MAP
    velocity: int  # 0-127


@dataclass
class DrumBar:
    """Represents one bar of drums."""
    hits: List[DrumHit]
    time_signature: Tuple[int, int] = (4, 4)


class DrumPatternGenerator:
    """Generates drum patterns based on style parameters."""

    def __init__(self):
        self.patterns = {}
        self._init_patterns()

    def _init_patterns(self):
        """Initialize pattern templates."""
        # Basic rock beat: kick on 1,3 snare on 2,4, 8th hi-hats
        self.patterns["basic_rock"] = {
            "kick": [1, 9],           # Beats 1 and 3
            "snare": [5, 13],         # Beats 2 and 4
            "hihat": [1, 3, 5, 7, 9, 11, 13, 15],  # 8th notes
        }

        # Metal double bass
        self.patterns["metal_double_bass"] = {
            "kick": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],  # 16ths
            "snare": [5, 13],
            "hihat": [1, 3, 5, 7, 9, 11, 13, 15],
        }

        # Blast beat
        self.patterns["blast_beat"] = {
            "kick": [1, 3, 5, 7, 9, 11, 13, 15],      # Every other 16th
            "snare": [2, 4, 6, 8, 10, 12, 14, 16],    # Alternating with kick
            "ride": [1, 3, 5, 7, 9, 11, 13, 15],      # With kicks
        }

        # Half-time groove
        self.patterns["half_time"] = {
            "kick": [1, 11],
            "snare": [9],             # Snare on beat 3 only
            "hihat": [1, 5, 9, 13],   # Quarter notes
        }

        # Djent syncopated
        self.patterns["djent_groove"] = {
            "kick": [1, 4, 7, 10, 13],  # Syncopated
            "snare": [5, 13],
            "snare_ghost": [3, 7, 11, 15],
            "hihat": [1, 3, 5, 7, 9, 11, 13, 15],
            "china": [1],
        }

        # Meshuggah-style polyrhythmic
        self.patterns["polyrhythmic"] = {
            "kick": [1, 4, 7, 11, 14],   # 5 over 4 feel
            "snare": [5, 13],
            "hihat": [1, 3, 5, 7, 9, 11, 13, 15],
            "china": [1, 9],
        }

        # Thrash gallop
        self.patterns["thrash_gallop"] = {
            "kick": [1, 3, 4, 9, 11, 12],  # Gallop pattern
            "snare": [5, 13],
            "hihat": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
        }

        # Groove metal (Lamb of God style)
        self.patterns["groove_metal"] = {
            "kick": [1, 4, 9, 12],
            "snare": [5, 13],
            "snare_ghost": [3, 11],
            "hihat": [1, 3, 5, 7, 9, 11, 13, 15],
            "china": [1],
        }

        # Progressive odd meter (7/8)
        self.patterns["progressive_7_8"] = {
            "kick": [1, 7, 11],
            "snare": [5, 13],
            "hihat": [1, 3, 5, 7, 9, 11, 13],
        }

        # Tool-style tribal
        self.patterns["tribal"] = {
            "kick": [1, 5, 9, 13],
            "snare": [9],
            "tom_low": [3, 7, 11, 15],
            "floor_tom": [1],
            "ride": [1, 5, 9, 13],
        }

        # Swing/shuffle feel
        self.patterns["shuffle"] = {
            "kick": [1, 9],
            "snare": [5, 13],
            "hihat": [1, 4, 5, 8, 9, 12, 13, 16],  # Shuffle triplet feel approximation
        }

        # Punk/fast rock
        self.patterns["punk_fast"] = {
            "kick": [1, 5, 9, 13],
            "snare": [5, 13],
            "hihat": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
        }

    def generate_bar(self, pattern_name: str, velocities: Dict[str, int] = None) -> DrumBar:
        """Generate a single bar from a pattern template."""
        if pattern_name not in self.patterns:
            pattern_name = "basic_rock"

        pattern = self.patterns[pattern_name]
        vel = velocities or VELOCITIES

        hits = []
        for drum, positions in pattern.items():
            midi_drum = drum.replace("_ghost", "")  # Handle ghost note naming
            is_ghost = "ghost" in drum

            for pos in positions:
                velocity = vel.get("ghost", 50) if is_ghost else vel.get("normal", 100)
                hits.append(DrumHit(
                    position=pos,
                    drum=midi_drum if midi_drum in DRUM_MAP else drum,
                    velocity=velocity
                ))

        return DrumBar(hits=hits)

    def generate_pattern(self, pattern_name: str, bars: int = 4,
                         add_crashes: bool = True,
                         add_fills: bool = True) -> List[DrumBar]:
        """Generate multiple bars with optional crashes and fills."""
        result = []

        for i in range(bars):
            bar = self.generate_bar(pattern_name)

            # Add crash on first beat of first bar
            if i == 0 and add_crashes:
                bar.hits.append(DrumHit(position=1, drum="crash1", velocity=120))

            # Add fill on last bar
            if i == bars - 1 and add_fills and bars > 1:
                bar = self._add_fill(bar)

            # Add crash every 4 bars
            if i > 0 and i % 4 == 0 and add_crashes:
                bar.hits.append(DrumHit(position=1, drum="crash1", velocity=120))

            result.append(bar)

        return result

    def _add_fill(self, bar: DrumBar) -> DrumBar:
        """Add a simple tom fill to the last beat of a bar."""
        fill_hits = [
            DrumHit(position=13, drum="tom_high", velocity=110),
            DrumHit(position=14, drum="tom_mid", velocity=105),
            DrumHit(position=15, drum="tom_low", velocity=100),
            DrumHit(position=16, drum="floor_tom", velocity=110),
        ]

        # Remove hi-hat hits from beat 4 area
        bar.hits = [h for h in bar.hits if h.position < 13 or h.drum not in ["hihat_closed", "hihat"]]
        bar.hits.extend(fill_hits)

        return bar


def bars_to_tab(bars: List[DrumBar]) -> str:
    """Convert drum bars to ASCII tab representation."""
    # Drum lines in tab order (top to bottom)
    drum_lines = ["crash1", "ride", "hihat_closed", "snare", "tom_high", "tom_mid", "tom_low", "floor_tom", "kick"]
    drum_labels = ["CC", "RD", "HH", "SD", "T1", "T2", "T3", "FT", "BD"]

    tab_lines = {drum: [] for drum in drum_lines}

    for bar in bars:
        # Initialize bar with dashes
        bar_hits = {drum: ["-"] * 16 for drum in drum_lines}

        for hit in bar.hits:
            drum = hit.drum
            # Map variations to main drums
            if drum == "hihat":
                drum = "hihat_closed"
            if drum == "china":
                drum = "crash1"  # Use crash line for china
            if drum not in drum_lines:
                continue

            pos = hit.position - 1  # Convert to 0-indexed
            if 0 <= pos < 16:
                # Use different symbols for different drums
                if drum == "hihat_closed":
                    symbol = "x"
                elif drum == "snare" and hit.velocity < 70:
                    symbol = "g"  # Ghost note
                elif drum in ["crash1", "crash2", "china", "splash"]:
                    symbol = "X"
                elif drum in ["ride", "ride_bell"]:
                    symbol = "x"
                else:
                    symbol = "o"
                bar_hits[drum][pos] = symbol

        # Add bar separator
        for drum in drum_lines:
            tab_lines[drum].extend(bar_hits[drum])
            tab_lines[drum].append("|")

    # Build output
    output = []
    for drum, label in zip(drum_lines, drum_labels):
        line = "".join(tab_lines[drum])
        if any(c != "-" and c != "|" for c in line):  # Only include lines with hits
            output.append(f"{label}|{line}")

    return "\n".join(output)


# Pattern name mapping from AI suggestions
PATTERN_MAP = {
    "blast beat": "blast_beat",
    "blast": "blast_beat",
    "double bass": "metal_double_bass",
    "double kick": "metal_double_bass",
    "metal": "metal_double_bass",
    "half time": "half_time",
    "halftime": "half_time",
    "djent": "djent_groove",
    "meshuggah": "polyrhythmic",
    "polyrhythmic": "polyrhythmic",
    "poly": "polyrhythmic",
    "thrash": "thrash_gallop",
    "gallop": "thrash_gallop",
    "groove": "groove_metal",
    "lamb of god": "groove_metal",
    "tribal": "tribal",
    "tool": "tribal",
    "shuffle": "shuffle",
    "swing": "shuffle",
    "punk": "punk_fast",
    "fast": "punk_fast",
    "rock": "basic_rock",
    "basic": "basic_rock",
    "progressive": "progressive_7_8",
    "odd": "progressive_7_8",
}


def get_pattern_from_style(style_keywords: str) -> str:
    """Map style keywords to pattern name."""
    style_lower = style_keywords.lower()

    for keyword, pattern in PATTERN_MAP.items():
        if keyword in style_lower:
            return pattern

    return "basic_rock"


def generate_drum_tab(pattern: str = "basic_rock", bars: int = 4,
                       add_crashes: bool = True, add_fills: bool = True) -> str:
    """Main entry point for generating drum tabs."""
    gen = DrumPatternGenerator()
    drum_bars = gen.generate_pattern(pattern, bars, add_crashes, add_fills)
    return bars_to_tab(drum_bars)


if __name__ == "__main__":
    # Test patterns
    patterns = ["basic_rock", "blast_beat", "djent_groove", "groove_metal", "tribal"]

    for p in patterns:
        print(f"\n{'='*60}")
        print(f"Pattern: {p}")
        print("="*60)
        print(generate_drum_tab(p, bars=2))
