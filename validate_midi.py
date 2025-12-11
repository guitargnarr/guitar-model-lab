#!/usr/bin/env python3
"""
MIDI Validation for Guitar Theory Engine

Simulates TabPlayer.jsx parsing and MIDI calculation in Python.
Validates that generated tabs will produce correct audio playback.

Usage:
    python3 validate_midi.py                    # Run all MIDI tests
    python3 validate_midi.py --root E --scale phrygian  # Test specific scale
"""

import argparse
import re
from typing import List, Tuple, Dict
from guitar_theory import GuitarTheory, generate_tab, SCALES, NOTE_NAMES

# TabPlayer.jsx MIDI mapping (from line 12)
# Index 0 = high e (MIDI 64), Index 5 = low E (MIDI 40)
TABPLAYER_MIDI = [64, 59, 55, 50, 45, 40]

# Note name to MIDI offset within octave
NOTE_TO_OFFSET = {
    'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
    'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11
}


def parse_tab_like_tabplayer(tab_string: str) -> List[Dict]:
    """
    Replicate TabPlayer.jsx parseTab() logic (lines 134-182).

    Args:
        tab_string: Full ASCII tab with 6 lines

    Returns:
        List of columns, each with {notes: [{string, fret}], position}
    """
    lines = tab_string.strip().split('\n')
    if len(lines) != 6:
        raise ValueError(f"Expected 6 tab lines, got {len(lines)}")

    # Remove string labels (e.g., "e|" prefix)
    cleaned_lines = []
    for line in lines:
        # Find and remove the "X|" prefix
        match = re.match(r'^[eEBGDA]\|', line)
        if match:
            cleaned_lines.append(line[2:])
        else:
            cleaned_lines.append(line)

    # Parse each string for fret numbers (like TabPlayer's parseTab)
    string_notes = []
    for line in cleaned_lines:
        notes = []
        i = 0
        while i < len(line):
            if not line[i].isdigit():
                i += 1
                continue
            # Found digit - collect consecutive digits (handles 10, 12, etc)
            num_str = ''
            start_pos = i
            while i < len(line) and line[i].isdigit():
                num_str += line[i]
                i += 1
            notes.append({'fret': int(num_str), 'position': start_pos})
        string_notes.append(notes)

    # Find all unique positions
    all_positions = set()
    for notes in string_notes:
        for n in notes:
            all_positions.add(n['position'])

    sorted_positions = sorted(all_positions)

    # Build columns at each position
    columns = []
    for pos in sorted_positions:
        column = {'notes': [], 'position': pos}
        for string_idx in range(6):
            note = next((n for n in string_notes[string_idx] if n['position'] == pos), None)
            if note:
                column['notes'].append({'string': string_idx, 'fret': note['fret']})
        if column['notes']:
            columns.append(column)

    return columns


def calculate_midi_sequence(columns: List[Dict]) -> List[int]:
    """
    Calculate MIDI note sequence that TabPlayer would play.

    Args:
        columns: Parsed tab columns from parse_tab_like_tabplayer()

    Returns:
        List of MIDI note numbers in playback order
    """
    midi_notes = []
    for col in columns:
        for note in col['notes']:
            string = note['string']
            fret = note['fret']
            midi = TABPLAYER_MIDI[string] + fret
            midi_notes.append(midi)
    return midi_notes


def midi_to_note_name(midi: int) -> str:
    """Convert MIDI number to note name (e.g., 40 -> 'E2')."""
    octave = (midi // 12) - 1
    note_idx = midi % 12
    note_name = NOTE_NAMES[note_idx]
    return f"{note_name}{octave}"


def get_scale_midi_notes(root: str, scale: str) -> set:
    """Get all MIDI note numbers that belong to a scale (across all octaves)."""
    gt = GuitarTheory()
    scale_notes = gt.get_scale_notes(root, scale)

    # Convert note names to chromatic offsets
    offsets = set()
    for note in scale_notes:
        offsets.add(NOTE_TO_OFFSET[note])

    return offsets


def validate_midi_in_scale(midi_notes: List[int], root: str, scale: str) -> Tuple[bool, List[str]]:
    """
    Validate that all MIDI notes belong to the specified scale.

    Returns:
        (is_valid, list_of_errors)
    """
    scale_offsets = get_scale_midi_notes(root, scale)
    errors = []

    for midi in midi_notes:
        note_offset = midi % 12
        if note_offset not in scale_offsets:
            actual_note = midi_to_note_name(midi)
            errors.append(f"MIDI {midi} ({actual_note}) not in {root} {scale}")

    return len(errors) == 0, errors


def validate_tab_midi(root: str, scale: str, pattern: str, position: int, bars: int = 2) -> Dict:
    """
    Full MIDI validation for a generated tab.

    Returns:
        {
            'status': 'PASS' or 'FAIL',
            'midi_notes': [list of MIDI numbers],
            'note_names': [list of note names],
            'errors': [list of error messages]
        }
    """
    result = {
        'root': root,
        'scale': scale,
        'pattern': pattern,
        'position': position,
    }

    try:
        # Generate tab
        tab = generate_tab(root, scale, pattern, bars, position)
        result['tab'] = tab

        # Parse like TabPlayer
        columns = parse_tab_like_tabplayer(tab)
        result['column_count'] = len(columns)

        # Calculate MIDI sequence
        midi_notes = calculate_midi_sequence(columns)
        result['midi_notes'] = midi_notes
        result['note_names'] = [midi_to_note_name(m) for m in midi_notes]

        # Validate notes are in scale
        is_valid, errors = validate_midi_in_scale(midi_notes, root, scale)
        result['errors'] = errors
        result['status'] = 'PASS' if is_valid else 'FAIL'

    except Exception as e:
        result['status'] = 'ERROR'
        result['errors'] = [str(e)]

    return result


def run_midi_validation(roots=None, scales=None, patterns=None, positions=None, verbose=True):
    """Run MIDI validation across multiple combinations."""
    if roots is None:
        roots = ['E', 'A', 'D', 'G', 'C']
    if scales is None:
        scales = list(SCALES.keys())
    if patterns is None:
        patterns = ['ascending', 'descending', 'pedal', 'arpeggio', 'random']
    if positions is None:
        positions = [1, 2, 3]

    results = []
    total = len(roots) * len(scales) * len(patterns) * len(positions)
    current = 0

    for scale in scales:
        # Skip 3nps for non-7-note scales
        scale_patterns = patterns.copy()
        if len(SCALES[scale]) != 7 and '3nps' in scale_patterns:
            scale_patterns = [p for p in scale_patterns if p != '3nps']

        for root in roots:
            for pattern in scale_patterns:
                for position in positions:
                    current += 1
                    result = validate_tab_midi(root, scale, pattern, position)
                    results.append(result)

                    if verbose:
                        status = result['status']
                        symbol = '✓' if status == 'PASS' else '✗' if status == 'FAIL' else '!'
                        print(f"[{current}/{total}] {symbol} MIDI: {root} {scale} {pattern} pos{position}: {status}")
                        if status != 'PASS' and result.get('errors'):
                            for err in result['errors'][:3]:
                                print(f"         {err}")

    return results


def print_midi_summary(results):
    """Print MIDI validation summary."""
    passed = [r for r in results if r['status'] == 'PASS']
    failed = [r for r in results if r['status'] == 'FAIL']
    errors = [r for r in results if r['status'] == 'ERROR']

    print(f"\n{'='*60}")
    print("MIDI VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total:   {len(results)}")
    print(f"Passed:  {len(passed)} ({100*len(passed)/len(results):.1f}%)")
    print(f"Failed:  {len(failed)}")
    print(f"Errors:  {len(errors)}")

    if failed:
        print(f"\nMIDI FAILURES (notes outside scale):")
        for r in failed[:10]:
            print(f"  {r['root']} {r['scale']} {r['pattern']} pos{r['position']}")
            for err in r.get('errors', [])[:2]:
                print(f"    → {err}")


def main():
    parser = argparse.ArgumentParser(description="Validate MIDI playback for guitar theory engine")
    parser.add_argument('--root', type=str, help='Test specific root note')
    parser.add_argument('--scale', type=str, help='Test specific scale')
    parser.add_argument('--pattern', type=str, help='Test specific pattern')
    parser.add_argument('--position', type=int, help='Test specific position')
    parser.add_argument('--quick', action='store_true', help='Quick test (E phrygian only)')

    args = parser.parse_args()

    if args.quick:
        # Quick test - just E Phrygian
        result = validate_tab_midi('E', 'phrygian', 'ascending', 1)
        print(f"E Phrygian Ascending Position 1:")
        print(f"  Status: {result['status']}")
        print(f"  MIDI: {result.get('midi_notes', [])}")
        print(f"  Notes: {result.get('note_names', [])}")
        if result.get('errors'):
            print(f"  Errors: {result['errors']}")
        return

    # Determine test scope
    roots = [args.root] if args.root else None
    scales = [args.scale] if args.scale else None
    patterns = [args.pattern] if args.pattern else None
    positions = [args.position] if args.position else None

    print("MIDI Validation - Guitar Theory Engine")
    print("Simulating TabPlayer.jsx parsing + MIDI calculation\n")

    results = run_midi_validation(roots, scales, patterns, positions)
    print_midi_summary(results)


if __name__ == '__main__':
    main()
