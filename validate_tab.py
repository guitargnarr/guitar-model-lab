#!/usr/bin/env python3
"""
Tab Validator for E Phrygian Scale
Validates model-generated tabs against correct fret positions.
"""

import re
import subprocess
import sys

# E Phrygian valid frets per string (standard tuning)
E_PHRYGIAN_FRETS = {
    'E': {0, 1, 3, 5, 7, 8, 10, 12, 13, 15, 17, 19, 20, 22},  # low E
    'A': {0, 2, 3, 5, 7, 8, 10, 12, 14, 15, 17, 19, 20, 22},
    'D': {0, 2, 3, 5, 7, 9, 10, 12, 14, 15, 17, 19, 21, 22},
    'G': {0, 2, 4, 5, 7, 9, 10, 12, 14, 16, 17, 19, 21, 22},
    'B': {0, 1, 3, 5, 6, 8, 10, 12, 13, 15, 17, 18, 20, 22},
    'e': {0, 1, 3, 5, 7, 8, 10, 12, 13, 15, 17, 19, 20, 22},  # high e
}

def parse_tab_line(line: str) -> tuple[str, list[int]]:
    """Extract string name and fret numbers from a tab line."""
    match = re.match(r'^([eEBGDA])\|(.+)\|?', line.strip())
    if not match:
        return None, []

    string_name = match.group(1)
    content = match.group(2)

    # Find all numbers (fret positions)
    frets = [int(f) for f in re.findall(r'\d+', content)]
    return string_name, frets

def validate_frets(string_name: str, frets: list[int]) -> tuple[bool, list[int]]:
    """Check if all frets are valid for the given string."""
    # Normalize: both E and e use same validation
    key = 'E' if string_name == 'E' else string_name
    if key not in E_PHRYGIAN_FRETS:
        key = string_name.lower() if string_name.lower() in E_PHRYGIAN_FRETS else 'e'

    valid_set = E_PHRYGIAN_FRETS.get(key, E_PHRYGIAN_FRETS['e'])
    invalid = [f for f in frets if f not in valid_set]
    return len(invalid) == 0, invalid

def validate_tab_output(output: str) -> tuple[bool, dict]:
    """Validate entire tab output. Returns (is_valid, details)."""
    lines = output.strip().split('\n')
    results = {'valid': True, 'errors': []}

    for line in lines:
        string_name, frets = parse_tab_line(line)
        if string_name and frets:
            is_valid, invalid_frets = validate_frets(string_name, frets)
            if not is_valid:
                results['valid'] = False
                results['errors'].append({
                    'string': string_name,
                    'invalid_frets': invalid_frets,
                    'line': line.strip()
                })

    return results['valid'], results

def nearest_valid_fret(string_name: str, fret: int) -> int:
    """Find nearest valid E Phrygian fret for a given invalid fret."""
    key = 'E' if string_name.upper() == 'E' else string_name
    if key not in E_PHRYGIAN_FRETS:
        key = 'e' if string_name.lower() == 'e' else string_name

    valid_set = E_PHRYGIAN_FRETS.get(key, E_PHRYGIAN_FRETS['e'])

    if fret in valid_set:
        return fret

    # Find nearest valid fret
    below = [f for f in valid_set if f < fret]
    above = [f for f in valid_set if f > fret]

    nearest_below = max(below) if below else None
    nearest_above = min(above) if above else None

    if nearest_below is None:
        return nearest_above
    if nearest_above is None:
        return nearest_below

    # Return closer one (prefer lower if tie)
    if fret - nearest_below <= nearest_above - fret:
        return nearest_below
    return nearest_above

def correct_tab_line(line: str) -> str:
    """Correct invalid frets in a tab line."""
    match = re.match(r'^([eEBGDA])\|(.+?)(\|?)$', line.strip())
    if not match:
        return line

    string_name = match.group(1)
    content = match.group(2)
    end_bar = match.group(3)

    # Replace each fret number with corrected version
    def replace_fret(m):
        fret = int(m.group(0))
        corrected = nearest_valid_fret(string_name, fret)
        return str(corrected)

    corrected_content = re.sub(r'\d+', replace_fret, content)
    return f"{string_name}|{corrected_content}{end_bar}"

def correct_tab_output(output: str) -> str:
    """Correct all invalid frets in tab output."""
    lines = output.split('\n')
    corrected = []

    for line in lines:
        if re.match(r'^[eEBGDA]\|', line.strip()):
            corrected.append(correct_tab_line(line))
        else:
            corrected.append(line)

    return '\n'.join(corrected)

def generate_and_validate(model: str, prompt: str, max_retries: int = 3) -> tuple[str, bool]:
    """Generate tab with retry loop until valid or max retries."""
    for attempt in range(max_retries):
        print(f"Attempt {attempt + 1}/{max_retries}...")

        result = subprocess.run(
            ['ollama', 'run', model, prompt],
            capture_output=True,
            text=True,
            timeout=120
        )

        output = result.stdout
        is_valid, details = validate_tab_output(output)

        if is_valid:
            print(f"VALID on attempt {attempt + 1}")
            return output, True
        else:
            print(f"INVALID: {details['errors']}")

    print(f"Failed after {max_retries} attempts")
    return output, False

if __name__ == '__main__':
    # Test with stdin or direct call
    if len(sys.argv) > 1:
        model = sys.argv[1] if len(sys.argv) > 1 else 'guitar_expert_qwen'
        prompt = sys.argv[2] if len(sys.argv) > 2 else "Give me a 4-bar E Phrygian riff in standard tuning at 140 BPM. Use ASCII tablature format."
        output, valid = generate_and_validate(model, prompt)
        print("\n=== FINAL OUTPUT ===")
        print(output)
        print(f"\nValidation: {'PASS' if valid else 'FAIL'}")
    else:
        # Read from stdin for manual validation
        import sys
        tab = sys.stdin.read()
        is_valid, details = validate_tab_output(tab)
        print(f"Valid: {is_valid}")
        if not is_valid:
            for err in details['errors']:
                print(f"  {err['string']}: invalid frets {err['invalid_frets']}")
