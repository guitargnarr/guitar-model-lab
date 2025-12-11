#!/usr/bin/env python3
"""
Guitar Theory Engine - Automated Validation Suite

Systematically tests all scale/root/pattern/position combinations
and reports which ones pass or fail.

Usage:
    python3 validate_all.py              # Run all tests
    python3 validate_all.py --quick      # Quick test (subset)
    python3 validate_all.py --scale minor # Test specific scale
    python3 validate_all.py --play       # Open failures in browser for manual check
"""

import argparse
import subprocess
import sys
import json
from datetime import datetime
from guitar_theory import GuitarTheory, generate_tab, SCALES, NOTE_NAMES
from validate_midi import parse_tab_like_tabplayer, calculate_midi_sequence, validate_midi_in_scale

# Test configuration
ALL_ROOTS = ['E', 'A', 'D', 'G', 'C', 'F', 'B']
QUICK_ROOTS = ['E', 'A', 'G']
ALL_PATTERNS = ['ascending', 'descending', 'pedal', 'arpeggio', 'random', '3nps']
QUICK_PATTERNS = ['ascending', 'descending']
ALL_POSITIONS = [1, 2, 3, 4, 5]
QUICK_POSITIONS = [1, 2]


def validate_combination(root: str, scale: str, pattern: str, position: int) -> dict:
    """
    Validate a single scale/pattern/position combination.

    Returns dict with validation results.
    """
    result = {
        'root': root,
        'scale': scale,
        'pattern': pattern,
        'position': position,
        'timestamp': datetime.now().isoformat(),
    }

    # Skip invalid combinations by design
    scale_intervals = SCALES.get(scale, [])
    if pattern == '3nps' and len(scale_intervals) != 7:
        result['status'] = 'SKIP'
        result['skip_reason'] = f'3NPS requires 7-note scale, {scale} has {len(scale_intervals)}'
        return result

    try:
        # Generate the tab
        tab = generate_tab(root, scale, pattern, bars=2, position=position)
        result['tab'] = tab

        # Parse the tab to extract fret numbers
        lines = tab.split('\n')
        all_frets = []

        for line in lines:
            # Skip the string label (e.g., "e|")
            content = line[2:] if len(line) > 2 else ''
            i = 0
            while i < len(content):
                if content[i].isdigit():
                    # Collect multi-digit fret numbers
                    num_str = ''
                    while i < len(content) and content[i].isdigit():
                        num_str += content[i]
                        i += 1
                    all_frets.append(int(num_str))
                else:
                    i += 1

        result['frets_found'] = all_frets
        result['has_notes'] = len(all_frets) > 0

        if all_frets:
            result['min_fret'] = min(all_frets)
            result['max_fret'] = max(all_frets)
            result['fret_range'] = max(all_frets) - min(all_frets)
            # 3NPS patterns span more frets by design (position shifts)
            # Box patterns should stay within 5-fret span
            if pattern == '3nps':
                result['playable'] = result['fret_range'] <= 12  # 3NPS spans ~octave
            else:
                result['playable'] = result['fret_range'] <= 5
        else:
            result['playable'] = False
            result['fret_range'] = 0

        # Verify scale notes are correct
        gt = GuitarTheory()
        expected_notes = set(gt.get_scale_notes(root, scale))
        result['expected_notes'] = list(expected_notes)

        # Check that we have enough notes for the requested bars
        expected_note_count = 2 * 4  # 2 bars * 4 notes per bar
        result['note_count'] = len(all_frets)
        result['enough_notes'] = len(all_frets) >= expected_note_count * 0.5  # Allow some flexibility

        # MIDI Validation - verify notes are in scale
        try:
            columns = parse_tab_like_tabplayer(tab)
            midi_notes = calculate_midi_sequence(columns)
            midi_valid, midi_errors = validate_midi_in_scale(midi_notes, root, scale)
            result['midi_valid'] = midi_valid
            result['midi_errors'] = midi_errors
        except Exception as midi_err:
            result['midi_valid'] = False
            result['midi_errors'] = [str(midi_err)]

        # Overall status
        if result['has_notes'] and result['playable'] and result['enough_notes'] and result.get('midi_valid', True):
            result['status'] = 'PASS'
        else:
            result['status'] = 'FAIL'
            reasons = []
            if not result['has_notes']:
                reasons.append('no notes generated')
            if not result['playable']:
                reasons.append(f'fret range {result["fret_range"]} > 5')
            if not result['enough_notes']:
                reasons.append(f'only {result["note_count"]} notes')
            if not result.get('midi_valid', True):
                reasons.append('MIDI notes outside scale')
            result['fail_reason'] = ', '.join(reasons)

    except Exception as e:
        result['status'] = 'ERROR'
        result['error'] = str(e)

    return result


def run_validation(roots, scales, patterns, positions, verbose=True):
    """Run validation across all specified combinations."""
    results = []
    total = len(roots) * len(scales) * len(patterns) * len(positions)
    current = 0

    for scale in scales:
        for root in roots:
            for pattern in patterns:
                for position in positions:
                    current += 1
                    result = validate_combination(root, scale, pattern, position)
                    results.append(result)

                    status = result['status']
                    if verbose:
                        symbol = '✓' if status == 'PASS' else '✗' if status == 'FAIL' else '!'
                        print(f"[{current}/{total}] {symbol} {root} {scale} {pattern} pos{position}: {status}")
                        if status != 'PASS' and 'fail_reason' in result:
                            print(f"         Reason: {result['fail_reason']}")

    return results


def print_summary(results):
    """Print validation summary."""
    passed = [r for r in results if r['status'] == 'PASS']
    failed = [r for r in results if r['status'] == 'FAIL']
    errors = [r for r in results if r['status'] == 'ERROR']
    skipped = [r for r in results if r['status'] == 'SKIP']

    print(f"\n{'='*60}")
    print(f"GUITAR THEORY ENGINE - VALIDATION SUMMARY")
    print(f"{'='*60}")
    applicable = len(results) - len(skipped)
    print(f"Total tests:  {len(results)}")
    print(f"Skipped:      {len(skipped)} (invalid combinations by design)")
    print(f"Applicable:   {applicable}")
    print(f"Passed:       {len(passed)} ({100*len(passed)/applicable:.1f}% of applicable)")
    print(f"Failed:       {len(failed)}")
    print(f"Errors:       {len(errors)}")

    if failed:
        print(f"\n{'='*60}")
        print("FAILURES:")
        print(f"{'='*60}")
        for r in failed[:20]:  # Show first 20
            print(f"  {r['root']} {r['scale']} {r['pattern']} pos{r['position']}")
            if 'fail_reason' in r:
                print(f"    -> {r['fail_reason']}")
        if len(failed) > 20:
            print(f"  ... and {len(failed) - 20} more")

    if errors:
        print(f"\n{'='*60}")
        print("ERRORS:")
        print(f"{'='*60}")
        for r in errors[:10]:
            print(f"  {r['root']} {r['scale']} {r['pattern']} pos{r['position']}")
            print(f"    -> {r.get('error', 'unknown error')}")

    # Scale breakdown
    print(f"\n{'='*60}")
    print("BY SCALE:")
    print(f"{'='*60}")
    for scale in SCALES.keys():
        scale_results = [r for r in results if r['scale'] == scale]
        scale_passed = sum(1 for r in scale_results if r['status'] == 'PASS')
        if scale_results:
            pct = 100 * scale_passed / len(scale_results)
            bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
            print(f"  {scale:20} {bar} {pct:5.1f}% ({scale_passed}/{len(scale_results)})")


def update_protocol_matrix(results):
    """Generate markdown for protocol.md validation matrix."""
    print(f"\n{'='*60}")
    print("VALIDATION MATRIX (copy to protocol.md):")
    print(f"{'='*60}")

    # Build matrix
    scales = list(SCALES.keys())
    roots = ALL_ROOTS

    header = "| Scale |" + " | ".join(roots) + " |"
    separator = "|" + "|".join(["-------"] * (len(roots) + 1)) + "|"

    print(header)
    print(separator)

    for scale in scales:
        row = f"| {scale.replace('_', ' ').title():20} |"
        for root in roots:
            # Check if any position passed for this scale/root
            matching = [r for r in results if r['scale'] == scale and r['root'] == root]
            passed = sum(1 for r in matching if r['status'] == 'PASS')
            total = len(matching)
            if total == 0:
                row += " ? |"
            elif passed == total:
                row += " ✓ |"
            elif passed > 0:
                row += " ~ |"  # Partial
            else:
                row += " ✗ |"
        print(row)


def main():
    parser = argparse.ArgumentParser(description="Validate guitar theory engine")
    parser.add_argument('--quick', action='store_true', help='Quick test (subset)')
    parser.add_argument('--scale', type=str, help='Test specific scale only')
    parser.add_argument('--root', type=str, help='Test specific root only')
    parser.add_argument('--pattern', type=str, help='Test specific pattern only')
    parser.add_argument('--play', action='store_true', help='Open first failure in browser')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--matrix', action='store_true', help='Output validation matrix only')

    args = parser.parse_args()

    # Determine test scope
    if args.quick:
        roots = QUICK_ROOTS
        patterns = QUICK_PATTERNS
        positions = QUICK_POSITIONS
    else:
        roots = ALL_ROOTS
        patterns = ALL_PATTERNS
        positions = ALL_POSITIONS

    scales = list(SCALES.keys())

    # Apply filters
    if args.scale:
        scales = [args.scale]
    if args.root:
        roots = [args.root]
    if args.pattern:
        patterns = [args.pattern]

    print(f"Guitar Theory Engine - Validation Suite")
    print(f"Testing: {len(scales)} scales × {len(roots)} roots × {len(patterns)} patterns × {len(positions)} positions")
    print(f"Total combinations: {len(scales) * len(roots) * len(patterns) * len(positions)}")
    print()

    # Run validation
    results = run_validation(roots, scales, patterns, positions, verbose=not args.json)

    if args.json:
        # Strip tab content for cleaner JSON
        for r in results:
            if 'tab' in r:
                del r['tab']
        print(json.dumps(results, indent=2))
    else:
        print_summary(results)

        if args.matrix:
            update_protocol_matrix(results)

    # Open first failure in browser if requested
    if args.play:
        failures = [r for r in results if r['status'] != 'PASS']
        if failures:
            f = failures[0]
            print(f"\nOpening first failure in browser: {f['root']} {f['scale']} {f['pattern']} pos{f['position']}")
            subprocess.run([
                'python3', 'generate_riff_v2.py',
                '--root', f['root'],
                '--scale', f['scale'],
                '--pattern', f['pattern'],
                '--position', str(f['position']),
                '--play'
            ])

    # Return exit code based on results
    failed = sum(1 for r in results if r['status'] != 'PASS')
    return 1 if failed > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
