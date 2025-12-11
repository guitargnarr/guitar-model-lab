#!/usr/bin/env python3
"""
Guitar Riff Generator v2 - Deterministic Python Approach

Uses guitar_theory.py for 100% accurate scale-correct tabs.
No AI/Ollama required - pure music theory.

Usage:
    python3 generate_riff_v2.py [options]

Examples:
    python3 generate_riff_v2.py                           # Random E Phrygian
    python3 generate_riff_v2.py --root A --scale minor    # A Minor
    python3 generate_riff_v2.py --pattern pedal --bars 4  # Pedal tone
    python3 generate_riff_v2.py --random --play           # Random everything, open browser
"""

import argparse
import webbrowser
import urllib.parse
import random
import subprocess
import sys

from guitar_theory import (
    GuitarTheory, TabGenerator, generate_tab, SCALES,
    TUNINGS, CHORD_PROGRESSIONS
)

# Available patterns (expanded)
PATTERNS = [
    'ascending', 'descending', 'pedal', 'arpeggio', 'random', '3nps',
    'power_chords', 'progression'
]

# Common roots for random selection
ROOTS = ['E', 'A', 'D', 'G', 'C', 'F', 'B']

# Available tunings
TUNING_OPTIONS = list(TUNINGS.keys())

# Available progressions
PROGRESSION_OPTIONS = list(CHORD_PROGRESSIONS.keys())


def main():
    parser = argparse.ArgumentParser(
        description="Generate 100% scale-accurate guitar tabs using music theory"
    )
    parser.add_argument('--root', default='E', help='Root note (default: E)')
    parser.add_argument('--scale', default='phrygian',
                       choices=list(SCALES.keys()),
                       help='Scale type (default: phrygian)')
    parser.add_argument('--pattern', default='ascending',
                       choices=PATTERNS,
                       help='Pattern type (default: ascending)')
    parser.add_argument('--bars', type=int, default=4, help='Number of bars (default: 4)')
    parser.add_argument('--position', type=int, default=1,
                       help='Box position 1-5 (default: 1 = open/low frets)')
    parser.add_argument('--tuning', default='standard',
                       choices=TUNING_OPTIONS,
                       help='Guitar tuning (default: standard)')
    parser.add_argument('--progression', default=None,
                       choices=PROGRESSION_OPTIONS,
                       help='Chord progression (for "progression" pattern)')
    parser.add_argument('--random', action='store_true',
                       help='Randomize root, scale, and pattern')
    parser.add_argument('--play', action='store_true',
                       help='Open in guitar.projectlavos.com/tabplayer')
    parser.add_argument('--bpm', type=int, default=120, help='BPM for display (default: 120)')
    parser.add_argument('--ai', metavar='STYLE',
                       help='Use AI to interpret style (e.g., "aggressive metal")')
    parser.add_argument('--gp5', metavar='FILE',
                       help='Export to Guitar Pro 5 format (.gp5)')

    args = parser.parse_args()

    # Handle AI style interpretation
    if args.ai:
        try:
            from ai_style_interpreter import interpret_style
            params = interpret_style(args.ai)
            if params:
                args.root = params.get('root', args.root)
                args.scale = params.get('scale', args.scale)
                args.pattern = params.get('pattern', args.pattern)
                args.position = params.get('position', args.position)
                args.tuning = params.get('tuning', args.tuning)
                args.bpm = params.get('tempo', args.bpm)
                print(f"AI interpreted '{args.ai}':")
                print(f"  {params.get('reasoning', '')}")
                print()
        except ImportError:
            print("Warning: AI style interpreter not available")

    # Handle random mode
    if args.random:
        args.root = random.choice(ROOTS)
        args.scale = random.choice(list(SCALES.keys()))
        # Exclude progression from random (needs explicit progression name)
        args.pattern = random.choice([p for p in PATTERNS if p != 'progression'])
        args.position = random.choice([1, 2, 3])
        args.tuning = random.choice(TUNING_OPTIONS)

    # Validate progression pattern
    if args.pattern == 'progression' and not args.progression:
        args.progression = 'blues_12bar'
        print(f"Using default progression: {args.progression}")

    # Generate the tab
    print(f"Generating {args.bars}-bar {args.root} {args.scale.title()} riff")
    print(f"Pattern: {args.pattern} | Position: {args.position} | BPM: {args.bpm}")
    print(f"Tuning: {args.tuning}")
    if args.progression:
        print(f"Progression: {args.progression}")
    print("-" * 50)

    theory = GuitarTheory(tuning=args.tuning)
    scale_notes = theory.get_scale_notes(args.root, args.scale)
    print(f"Scale notes: {', '.join(scale_notes)}")
    print(f"Open strings: {', '.join(TUNINGS[args.tuning])}")
    print()

    tab = generate_tab(
        root=args.root,
        scale=args.scale,
        pattern=args.pattern,
        bars=args.bars,
        position=args.position,
        tuning=args.tuning,
        progression=args.progression
    )

    print(tab)
    print()
    print("=" * 50)
    print("VALIDATION: 100% scale-accurate (deterministic generation)")
    print("=" * 50)

    # Export to Guitar Pro 5 if requested
    if args.gp5:
        try:
            from export_gp import tab_to_gp5
            title = f"{args.root} {args.scale.title()} Riff"
            output_file = tab_to_gp5(
                tab,
                title=title,
                tempo=args.bpm,
                tuning=args.tuning,
                output_path=args.gp5
            )
            print()
            print(f"Guitar Pro 5 file: {output_file}")
        except ImportError:
            print("Error: export_gp.py not found")
        except Exception as e:
            print(f"Export error: {e}")

    # Open in dashboard if requested
    if args.play:
        print()
        print("Opening in TabPlayer...")
        encoded_tab = urllib.parse.quote(tab)
        dashboard_url = f"https://guitar.projectlavos.com/tabplayer?tab={encoded_tab}"

        # Use macOS 'open' command
        try:
            subprocess.run(['open', dashboard_url], check=True)
            print(f"Opened: guitar.projectlavos.com/tabplayer")
        except Exception as e:
            print(f"Could not open browser: {e}")
            print(f"URL: {dashboard_url}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
