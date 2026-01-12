#!/usr/bin/env python3
"""
AI-Assisted GP5 Generator

Workflow:
1. Query lead_architect/rhythm_architect for style interpretation
2. Parse AI JSON response for style parameters
3. Use guitar_theory.py for deterministic note generation
4. Export to GP5 via export_gp.py

Usage:
    python ai_to_gp5.py "aggressive Plini-style lead in E Phrygian"
    python ai_to_gp5.py --rhythm "heavy djent groove at 120 BPM"
"""

import json
import subprocess
import sys
import argparse
import re
from guitar_theory import GuitarTheory, TabGenerator, generate_tab, SCALES
from export_gp import tab_to_gp5

# Pattern type mapping from AI suggestions to generator methods
PATTERN_MAP = {
    "3-note-per-string": "3nps",
    "3nps": "3nps",
    "legato": "ascending",  # Default legato to ascending runs
    "legato pull-offs": "descending",
    "sweep arpeggio": "arpeggio",
    "arpeggio": "arpeggio",
    "tapping": "random",  # Tapping patterns are varied
    "pedal": "pedal",
    "power_chord": "power_chords",
    "ascending": "ascending",
    "descending": "descending",
}

# Scale mapping from AI suggestions (ordered: most specific first)
SCALE_MAP = [
    ("a harmonic minor", ("A", "harmonic_minor")),
    ("harmonic minor", ("A", "harmonic_minor")),
    ("harmonic_minor", ("A", "harmonic_minor")),
    ("a melodic minor", ("A", "melodic_minor")),
    ("melodic minor", ("A", "melodic_minor")),
    ("pentatonic minor", ("A", "pentatonic_minor")),
    ("pentatonic", ("A", "pentatonic_minor")),
    ("e phrygian", ("E", "phrygian")),
    ("phrygian", ("E", "phrygian")),
    ("dorian", ("D", "dorian")),
    ("minor", ("A", "minor")),
    ("blues", ("A", "blues")),
    ("mixolydian", ("G", "mixolydian")),
    ("lydian", ("F", "lydian")),
    ("major", ("C", "major")),
]


def query_ollama(model: str, prompt: str) -> dict:
    """Query Ollama model and parse JSON response."""
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=60
        )

        response = result.stdout.strip()

        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                print(f"Warning: Could not extract JSON from response")
                print(f"Raw response: {response[:500]}")
                return {}

        return json.loads(json_str)

    except subprocess.TimeoutExpired:
        print(f"Warning: Ollama query timed out")
        return {}
    except json.JSONDecodeError as e:
        print(f"Warning: JSON parse error: {e}")
        return {}
    except Exception as e:
        print(f"Warning: Ollama query failed: {e}")
        return {}


def interpret_lead_style(prompt: str) -> dict:
    """Get style interpretation from lead_architect."""
    print(f"Querying lead_architect for style interpretation...")
    return query_ollama("lead_architect", prompt)


def interpret_rhythm_style(prompt: str) -> dict:
    """Get style interpretation from rhythm_architect."""
    print(f"Querying rhythm_architect for style interpretation...")
    return query_ollama("rhythm_architect", prompt)


def extract_pattern_from_ai(ai_response: dict) -> str:
    """Extract pattern type from AI response."""
    patterns = ai_response.get("pattern_recommendations", [])

    if patterns:
        first_pattern = patterns[0]
        pattern_type = first_pattern.get("type", "").lower()

        # Map to our generator patterns
        for ai_pattern, gen_pattern in PATTERN_MAP.items():
            if ai_pattern in pattern_type:
                return gen_pattern

    # Default based on style profile
    style = ai_response.get("style_profile", {})
    articulation = style.get("articulation", "").lower()

    if "legato" in articulation:
        return "ascending"
    elif "staccato" in articulation:
        return "pedal"

    return "ascending"  # Safe default


def extract_scale_from_ai(ai_response: dict) -> tuple:
    """Extract root and scale from AI response."""
    scale_suggestion = ai_response.get("scale_suggestion", "").lower()

    for scale_key, (root, scale) in SCALE_MAP:
        if scale_key in scale_suggestion:
            # Try to extract root from suggestion (e.g., "E Phrygian" -> E)
            parts = scale_suggestion.split()
            if len(parts) >= 1 and len(parts[0]) <= 2:
                potential_root = parts[0].upper()
                if potential_root in ["A", "B", "C", "D", "E", "F", "G",
                                      "A#", "C#", "D#", "F#", "G#"]:
                    root = potential_root
            return (root, scale)

    return ("E", "phrygian")  # Default


def extract_tempo_from_ai(ai_response: dict) -> int:
    """Extract tempo from AI response."""
    tempo_range = ai_response.get("tempo_range", [])
    if tempo_range and len(tempo_range) >= 2:
        return (tempo_range[0] + tempo_range[1]) // 2

    style = ai_response.get("style_profile", {})
    tempo = style.get("tempo")
    if tempo:
        return int(tempo)

    return 120  # Default


def extract_rhythm_params(ai_response: dict) -> dict:
    """Extract rhythm parameters for djent/metal patterns."""
    skeleton = ai_response.get("rhythm_skeleton", {})
    chord = ai_response.get("chord_suggestions", {})
    style = ai_response.get("style_profile", {})

    return {
        "tempo": style.get("tempo", 120),
        "root": chord.get("root", "E"),
        "mode": chord.get("mode", "phrygian"),
        "tuning": chord.get("drop_tuning", "standard").replace("_", " "),
        "measures": skeleton.get("measures", 4),
        "accents": skeleton.get("accent_positions", [1, 5, 9, 13]),
    }


def generate_lead_gp5(prompt: str, output_path: str = None, bars: int = 8) -> str:
    """Generate lead guitar GP5 from natural language prompt."""

    # Step 1: Get AI style interpretation
    ai_response = interpret_lead_style(prompt)

    if not ai_response:
        print("Falling back to defaults (AI query failed)")
        ai_response = {
            "scale_suggestion": "E Phrygian",
            "tempo_range": [100, 130],
            "pattern_recommendations": [{"type": "3-note-per-string"}]
        }

    print(f"\nAI Style Interpretation:")
    print(json.dumps(ai_response, indent=2))

    # Step 2: Extract parameters
    root, scale = extract_scale_from_ai(ai_response)
    pattern = extract_pattern_from_ai(ai_response)
    tempo = extract_tempo_from_ai(ai_response)

    # 3NPS requires 7-note scales - fallback for pentatonic/blues
    non_7_note_scales = ["pentatonic_minor", "pentatonic_major", "blues"]
    if pattern == "3nps" and scale in non_7_note_scales:
        pattern = "ascending"  # Fallback for 5-6 note scales

    print(f"\nDeterministic Generation Parameters:")
    print(f"  Root: {root}")
    print(f"  Scale: {scale}")
    print(f"  Pattern: {pattern}")
    print(f"  Tempo: {tempo} BPM")

    # Step 3: Generate tab using deterministic Python
    print(f"\nGenerating tab...")
    tab = generate_tab(root, scale, pattern, bars=bars, position=1)
    print(f"\nGenerated Tab:")
    print(tab)

    # Step 4: Export to GP5
    title = f"AI_Lead_{root}_{scale}_{pattern}"
    if output_path is None:
        output_path = f"/Users/matthewscott/Desktop/{title}.gp5"

    gp5_path = tab_to_gp5(tab, title=title, tempo=tempo, output_path=output_path)
    print(f"\nCreated GP5: {gp5_path}")

    return gp5_path


def generate_rhythm_gp5(prompt: str, output_path: str = None, bars: int = 8) -> str:
    """Generate rhythm guitar GP5 from natural language prompt."""

    # Step 1: Get AI style interpretation
    ai_response = interpret_rhythm_style(prompt)

    if not ai_response:
        print("Falling back to defaults (AI query failed)")
        ai_response = {
            "style_profile": {"tempo": 120},
            "chord_suggestions": {"root": "E", "mode": "phrygian"},
        }

    print(f"\nAI Style Interpretation:")
    print(json.dumps(ai_response, indent=2))

    # Step 2: Extract parameters
    params = extract_rhythm_params(ai_response)
    root = params["root"]
    scale = params["mode"]
    tempo = params["tempo"]

    # Map mode names
    if scale == "mixolydian":
        scale = "mixolydian"
    elif scale not in SCALES:
        scale = "phrygian"

    print(f"\nDeterministic Generation Parameters:")
    print(f"  Root: {root}")
    print(f"  Scale: {scale}")
    print(f"  Tempo: {tempo} BPM")
    print(f"  Pattern: power_chords")

    # Step 3: Generate power chord riff
    print(f"\nGenerating tab...")
    tab = generate_tab(root, scale, "power_chords", bars=bars, position=1)
    print(f"\nGenerated Tab:")
    print(tab)

    # Step 4: Export to GP5
    title = f"AI_Rhythm_{root}_{scale}_djent"
    if output_path is None:
        output_path = f"/Users/matthewscott/Desktop/{title}.gp5"

    gp5_path = tab_to_gp5(tab, title=title, tempo=tempo, output_path=output_path)
    print(f"\nCreated GP5: {gp5_path}")

    return gp5_path


def main():
    parser = argparse.ArgumentParser(
        description="AI-assisted Guitar Pro 5 generator"
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default="aggressive metal lead in E Phrygian",
        help="Natural language description of desired riff"
    )
    parser.add_argument(
        "--rhythm", "-r",
        action="store_true",
        help="Generate rhythm guitar instead of lead"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output .gp5 file path"
    )
    parser.add_argument(
        "--bars", "-b",
        type=int,
        default=8,
        help="Number of bars to generate (default: 8)"
    )

    args = parser.parse_args()

    print(f"{'='*60}")
    print(f"AI-Assisted GP5 Generator")
    print(f"{'='*60}")
    print(f"Prompt: {args.prompt}")
    print(f"Type: {'Rhythm' if args.rhythm else 'Lead'}")
    print(f"{'='*60}")

    if args.rhythm:
        gp5_path = generate_rhythm_gp5(args.prompt, args.output, args.bars)
    else:
        gp5_path = generate_lead_gp5(args.prompt, args.output, args.bars)

    print(f"\n{'='*60}")
    print(f"SUCCESS!")
    print(f"Open in Guitar Pro 7: {gp5_path}")
    print(f"{'='*60}")

    return gp5_path


if __name__ == "__main__":
    main()
