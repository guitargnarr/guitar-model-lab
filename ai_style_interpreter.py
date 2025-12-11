#!/usr/bin/env python3
"""
AI Style Interpreter - Phase 4 of Guitar Model Lab

Uses Ollama (guitar_expert_precise) to interpret natural language style requests
and output structured parameters for the deterministic tab generator.

The AI suggests (creativity), Python generates (accuracy).

Usage:
    python3 ai_style_interpreter.py "give me something aggressive in E"
    python3 ai_style_interpreter.py "bluesy lick in A minor, slow and soulful"
    python3 ai_style_interpreter.py "fast metal riff, drop D tuning"

Output:
    JSON with: root, scale, pattern, position, tempo, tuning
"""

import argparse
import json
import subprocess
import sys
import re
from typing import Dict, Optional

# Valid options (must match guitar_theory.py)
VALID_SCALES = [
    "major", "minor", "pentatonic_major", "pentatonic_minor", "blues",
    "phrygian", "lydian", "mixolydian", "dorian", "locrian",
    "harmonic_minor", "melodic_minor"
]

VALID_PATTERNS = [
    "ascending", "descending", "pedal", "arpeggio", "random", "3nps"
]

VALID_TUNINGS = ["standard", "drop_d", "drop_c", "half_step_down"]

VALID_ROOTS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Style mapping hints for the AI
STYLE_HINTS = """
Style to parameter mappings:
- "metal", "aggressive", "heavy" -> phrygian/minor, pedal/3nps, fast tempo (140-180)
- "blues", "soulful", "bb king" -> blues/pentatonic_minor, pedal/random, slow (80-120)
- "jazz", "sophisticated" -> dorian/lydian/melodic_minor, arpeggio, medium (100-140)
- "rock", "classic rock" -> pentatonic_minor/mixolydian, ascending/random, medium (120-140)
- "country", "twangy" -> major/mixolydian, ascending/pedal, medium (120-140)
- "shred", "neoclassical" -> harmonic_minor/phrygian, 3nps, fast (160-200)
- "chill", "ambient" -> major/lydian, arpeggio/ascending, slow (70-100)
- "funk", "groove" -> mixolydian/dorian, pedal/random, medium (100-120)

Drop tunings: "drop d", "drop c", "downtuned" -> drop_d or drop_c
Half step: "eb tuning", "half step down" -> half_step_down
"""

SYSTEM_PROMPT = f"""You are a guitar style interpreter. Given a natural language description of a desired guitar riff style, output ONLY a JSON object with parameters for a tab generator.

{STYLE_HINTS}

Output format (JSON only, no explanation):
{{
  "root": "E",           // {', '.join(VALID_ROOTS)}
  "scale": "phrygian",   // {', '.join(VALID_SCALES)}
  "pattern": "pedal",    // {', '.join(VALID_PATTERNS)}
  "position": 1,         // 1-5 (lower = lower frets)
  "tempo": 140,          // 60-200 BPM
  "tuning": "standard",  // {', '.join(VALID_TUNINGS)}
  "reasoning": "brief explanation of choices"
}}

IMPORTANT:
- Output ONLY valid JSON, no markdown code blocks
- All values must be from the valid options listed
- If user mentions a specific key/root, use it
- If user mentions tuning, use it
- For 3nps pattern, only use 7-note scales (not pentatonic/blues)
"""


def interpret_style(prompt: str, model: str = "guitar_expert_precise") -> Optional[Dict]:
    """Use Ollama to interpret a style request.

    Args:
        prompt: Natural language style description
        model: Ollama model to use

    Returns:
        Dict with generator parameters or None on failure
    """
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser request: {prompt}"

    try:
        result = subprocess.run(
            ["ollama", "run", model, full_prompt],
            capture_output=True,
            text=True,
            timeout=30
        )

        response = result.stdout.strip()

        # Try to extract JSON from response
        # Handle potential markdown code blocks
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if not json_match:
            print(f"Error: No JSON found in response", file=sys.stderr)
            print(f"Raw response: {response}", file=sys.stderr)
            return None

        json_str = json_match.group()
        params = json.loads(json_str)

        # Validate and sanitize
        return validate_params(params)

    except subprocess.TimeoutExpired:
        print("Error: Ollama timed out", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None


def validate_params(params: Dict) -> Dict:
    """Validate and sanitize AI output to ensure valid parameters."""
    validated = {}

    # Root
    root = params.get("root", "E").upper()
    if root not in VALID_ROOTS:
        root = "E"
    validated["root"] = root

    # Scale
    scale = params.get("scale", "minor").lower().replace(" ", "_")
    if scale not in VALID_SCALES:
        scale = "minor"
    validated["scale"] = scale

    # Pattern
    pattern = params.get("pattern", "ascending").lower()
    if pattern not in VALID_PATTERNS:
        pattern = "ascending"
    # 3nps requires 7-note scale
    if pattern == "3nps":
        note_counts = {
            "pentatonic_major": 5, "pentatonic_minor": 5, "blues": 6
        }
        if scale in note_counts:
            pattern = "ascending"  # Fallback for incompatible scales
    validated["pattern"] = pattern

    # Position
    position = params.get("position", 1)
    try:
        position = int(position)
        position = max(1, min(5, position))
    except (ValueError, TypeError):
        position = 1
    validated["position"] = position

    # Tempo
    tempo = params.get("tempo", 120)
    try:
        tempo = int(tempo)
        tempo = max(60, min(200, tempo))
    except (ValueError, TypeError):
        tempo = 120
    validated["tempo"] = tempo

    # Tuning
    tuning = params.get("tuning", "standard").lower().replace(" ", "_")
    if tuning not in VALID_TUNINGS:
        tuning = "standard"
    validated["tuning"] = tuning

    # Reasoning (optional, for display)
    validated["reasoning"] = params.get("reasoning", "")

    return validated


def get_default_params() -> Dict:
    """Return sensible defaults when AI is unavailable."""
    return {
        "root": "E",
        "scale": "minor",
        "pattern": "ascending",
        "position": 1,
        "tempo": 120,
        "tuning": "standard",
        "reasoning": "Default parameters (AI unavailable)"
    }


def main():
    parser = argparse.ArgumentParser(
        description="Interpret natural language style requests for tab generation"
    )
    parser.add_argument("prompt", nargs="?", help="Style description")
    parser.add_argument("--model", default="guitar_expert_precise",
                       help="Ollama model to use")
    parser.add_argument("--test", action="store_true",
                       help="Run test suite")

    args = parser.parse_args()

    if args.test:
        run_tests(args.model)
        return 0

    if not args.prompt:
        # Interactive mode
        print("AI Style Interpreter - Enter a style description")
        print("Examples:")
        print("  'aggressive metal riff in E'")
        print("  'slow blues lick in A minor'")
        print("  'fast shred run, drop D tuning'")
        print()
        prompt = input("Style: ").strip()
        if not prompt:
            print("No input provided")
            return 1
    else:
        prompt = args.prompt

    print(f"Interpreting: '{prompt}'")
    print("-" * 50)

    params = interpret_style(prompt, args.model)

    if params:
        print(json.dumps(params, indent=2))
        print("-" * 50)
        print(f"Generator command:")
        print(f"  python3 generate_riff_v2.py \\")
        print(f"    --root {params['root']} \\")
        print(f"    --scale {params['scale']} \\")
        print(f"    --pattern {params['pattern']} \\")
        print(f"    --position {params['position']} \\")
        print(f"    --bpm {params['tempo']} \\")
        print(f"    --play")
        return 0
    else:
        print("Failed to interpret style, using defaults")
        params = get_default_params()
        print(json.dumps(params, indent=2))
        return 1


def run_tests(model: str):
    """Test suite for style interpretation."""
    test_cases = [
        ("aggressive metal riff in E", {"scale": "phrygian", "root": "E"}),
        ("slow blues in A", {"scale": "blues", "root": "A"}),
        ("fast shred run", {"pattern": "3nps"}),
        ("country lick in G", {"scale": "major", "root": "G"}),
        ("drop D metal", {"tuning": "drop_d"}),
        ("jazz chord tones in Dm", {"scale": "dorian", "root": "D"}),
    ]

    print("Running AI Style Interpreter Tests")
    print("=" * 60)

    passed = 0
    for prompt, expected in test_cases:
        print(f"\nTest: '{prompt}'")
        params = interpret_style(prompt, model)

        if params:
            matches = all(
                params.get(k) == v or params.get(k, "").lower() == v.lower()
                for k, v in expected.items()
            )
            status = "PASS" if matches else "PARTIAL"
            if matches:
                passed += 1
            print(f"  Result: {status}")
            print(f"  Params: {json.dumps(params, indent=4)}")
        else:
            print(f"  Result: FAIL (no response)")

    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{len(test_cases)} tests passed")


if __name__ == "__main__":
    sys.exit(main())
