#!/usr/bin/env python3
"""
AI to GP5 Drums - Generate drum patterns using AI style interpretation + Python

Flow:
1. User provides style description (e.g., "Meshuggah polyrhythmic groove")
2. drum_architect model interprets style → JSON
3. Python drum_theory generates deterministic pattern
4. export_gp creates GP5 file

Usage:
    python3 ai_to_gp5_drums.py "blast beat at 220 BPM"
    python3 ai_to_gp5_drums.py "Tool tribal groove" --bars 8
    python3 ai_to_gp5_drums.py "djent syncopated pattern" -o my_drums.gp5
"""

import subprocess
import json
import argparse
import os
import re
from datetime import datetime
from drum_theory import (
    DrumPatternGenerator, get_pattern_from_style,
    PATTERN_MAP, bars_to_tab
)
from export_gp import create_drum_gp5_file


def query_drum_architect(prompt: str) -> dict:
    """Query drum_architect model for style interpretation."""
    system_msg = """Interpret this drum style request. Output ONLY valid JSON with:
{
  "pattern_type": "one of: blast_beat, metal_double_bass, half_time, djent_groove, polyrhythmic, thrash_gallop, groove_metal, progressive_7_8, tribal, shuffle, punk_fast, basic_rock",
  "tempo": <number 60-280>,
  "feel": "<brief description>",
  "reference_artists": ["artist1", "artist2"]
}"""

    full_prompt = f"{system_msg}\n\nRequest: {prompt}"

    try:
        result = subprocess.run(
            ["ollama", "run", "drum_architect", full_prompt],
            capture_output=True,
            text=True,
            timeout=60
        )

        output = result.stdout.strip()

        # Extract JSON from response
        json_match = re.search(r'\{[^{}]*\}', output, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())

    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        print(f"Note: AI interpretation failed ({e}), using keyword matching")

    return None


def extract_tempo_from_prompt(prompt: str) -> int:
    """Extract tempo from prompt like '220 BPM' or 'at 180'."""
    patterns = [
        r'(\d+)\s*bpm',
        r'at\s+(\d+)',
        r'tempo\s+(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, prompt.lower())
        if match:
            tempo = int(match.group(1))
            if 40 <= tempo <= 300:
                return tempo

    return 120  # Default


def generate_drum_gp5(prompt: str, output_path: str = None, bars: int = 4) -> str:
    """
    Generate a drum GP5 file from a style description.

    Args:
        prompt: Style description (e.g., "blast beat at 220 BPM")
        output_path: Optional output path
        bars: Number of bars to generate

    Returns:
        Path to generated .gp5 file
    """
    print(f"Querying drum_architect: '{prompt}'")

    # Try AI interpretation first
    ai_response = query_drum_architect(prompt)

    if ai_response:
        print(f"AI response: {json.dumps(ai_response, indent=2)}")
        pattern_type = ai_response.get("pattern_type", "basic_rock")
        tempo = ai_response.get("tempo", extract_tempo_from_prompt(prompt))
        feel = ai_response.get("feel", "")
    else:
        # Fallback to keyword matching
        pattern_type = get_pattern_from_style(prompt)
        tempo = extract_tempo_from_prompt(prompt)
        feel = ""
        print(f"Using keyword matching: pattern={pattern_type}, tempo={tempo}")

    # Validate pattern type
    valid_patterns = [
        "basic_rock", "metal_double_bass", "blast_beat", "half_time",
        "djent_groove", "polyrhythmic", "thrash_gallop", "groove_metal",
        "progressive_7_8", "tribal", "shuffle", "punk_fast"
    ]

    if pattern_type not in valid_patterns:
        # Try to map from AI suggestion
        pattern_type = get_pattern_from_style(pattern_type)

    print(f"Generating {bars} bars of '{pattern_type}' at {tempo} BPM")

    # Generate drum pattern
    generator = DrumPatternGenerator()
    drum_bars = generator.generate_pattern(
        pattern_type,
        bars=bars,
        add_crashes=True,
        add_fills=True
    )

    # Show ASCII tab preview
    print("\nASCII Tab Preview:")
    print(bars_to_tab(drum_bars[:2]))  # Show first 2 bars
    if bars > 2:
        print("...")

    # Create title from prompt
    title = re.sub(r'[^\w\s-]', '', prompt)[:40].strip()
    title = title.replace(' ', '_')
    if not title:
        title = f"drums_{pattern_type}"

    # Generate output path
    if output_path is None:
        timestamp = datetime.now().strftime("%H%M%S")
        output_path = os.path.expanduser(
            f"~/Desktop/{title}_{tempo}bpm_{timestamp}.gp5"
        )

    # Create GP5 file
    output_file = create_drum_gp5_file(
        drum_bars,
        title=f"{title} ({pattern_type})",
        tempo=tempo,
        output_path=output_path
    )

    print(f"\nCreated: {output_file}")
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description='Generate drum GP5 files using AI + Python'
    )
    parser.add_argument(
        'prompt',
        help='Style description (e.g., "blast beat at 220 BPM")'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output .gp5 file path'
    )
    parser.add_argument(
        '-b', '--bars',
        type=int,
        default=4,
        help='Number of bars to generate (default: 4)'
    )

    args = parser.parse_args()

    output_file = generate_drum_gp5(
        args.prompt,
        output_path=args.output,
        bars=args.bars
    )

    return output_file


if __name__ == "__main__":
    main()
