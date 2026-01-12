#!/usr/bin/env python3
"""
Guitar Riff Generator - Full Pipeline
Generates validated E Phrygian riffs using AI + Python hybrid approach.

Usage:
    python3 generate_riff.py [scale] [--random] [--play] [--bars N]

Examples:
    python3 generate_riff.py                    # 4-bar E Phrygian
    python3 generate_riff.py "A Minor" --bars 8 # 8-bar A Minor
    python3 generate_riff.py --random --play    # Random scale, open dashboard
"""

import subprocess
import sys
import argparse
import webbrowser
import urllib.parse
from validate_tab import validate_tab_output, correct_tab_output

# Model to use
MODEL = "master_guitar_instructor"

# Available scales for random mode
SCALES = [
    "E Phrygian",
    "E Minor",
    "A Minor",
    "E Dorian",
    "G Major",
    "D Minor",
    "B Locrian",
]

def generate_tab(scale: str, bars: int = 4, bpm: int = 140) -> str:
    """Generate tab using Ollama model."""
    prompt = f"Give me a {bars}-bar {scale} riff in standard tuning at {bpm} BPM. Use ASCII tablature format."

    print(f"Generating {bars}-bar {scale} riff at {bpm} BPM...")
    print(f"Model: {MODEL}")
    print("-" * 50)

    result = subprocess.run(
        ["ollama", "run", MODEL, prompt],
        capture_output=True,
        text=True,
        timeout=120
    )

    return result.stdout

def main():
    parser = argparse.ArgumentParser(description="Generate validated guitar riffs")
    parser.add_argument("scale", nargs="?", default="E Phrygian", help="Scale/mode to use")
    parser.add_argument("--random", action="store_true", help="Use random scale")
    parser.add_argument("--play", action="store_true", help="Open in guitar dashboard")
    parser.add_argument("--bars", type=int, default=4, help="Number of bars (default: 4)")
    parser.add_argument("--bpm", type=int, default=140, help="Tempo in BPM (default: 140)")
    parser.add_argument("--correct", action="store_true", default=True, help="Auto-correct invalid frets")

    args = parser.parse_args()

    # Handle random mode
    if args.random:
        import random
        args.scale = random.choice(SCALES)
        print(f"Random scale selected: {args.scale}")

    # Generate tab
    raw_output = generate_tab(args.scale, args.bars, args.bpm)
    print(raw_output)

    # Validate
    print("\n" + "=" * 50)
    print("VALIDATION")
    print("=" * 50)

    is_valid, details = validate_tab_output(raw_output)

    if is_valid:
        print("PASS - All frets are valid for E Phrygian scale")
        final_output = raw_output
    else:
        print(f"FAIL - Found invalid frets:")
        for err in details['errors']:
            print(f"  {err['string']}: frets {err['invalid_frets']}")

        if args.correct:
            print("\nAuto-correcting...")
            final_output = correct_tab_output(raw_output)
            print("\nCORRECTED OUTPUT:")
            print(final_output)

            # Verify correction
            is_valid_now, _ = validate_tab_output(final_output)
            print(f"\nPost-correction validation: {'PASS' if is_valid_now else 'FAIL'}")
        else:
            final_output = raw_output

    # Open in dashboard if requested
    if args.play:
        print("\n" + "=" * 50)
        print("OPENING DASHBOARD")
        print("=" * 50)

        # Extract just the tab lines for the URL
        tab_lines = []
        for line in final_output.split('\n'):
            if line.strip().startswith(('e|', 'B|', 'G|', 'D|', 'A|', 'E|')):
                tab_lines.append(line.strip())

        if tab_lines:
            encoded_tab = urllib.parse.quote('\n'.join(tab_lines))
            dashboard_url = f"https://guitar.projectlavos.com/tabplayer?tab={encoded_tab}"
            print(f"Opening: guitar.projectlavos.com/tabplayer")
            webbrowser.open(dashboard_url)
        else:
            print("No tab lines found to open in player")

    return 0 if is_valid else 1

if __name__ == "__main__":
    sys.exit(main())
