# Guitar Theory Engine - Parallel Validation Plan

**Project:** Guitar Theory Engine
**Created:** 2025-12-10
**Approach:** Parallel Development Playbook v4

---

## Executive Summary

Building a deterministic guitar theory engine that generates 100% accurate, playable tabs for any scale/key/pattern combination. Using parallel terminals to systematically validate all 720+ combinations.

**Current State:** E Phrygian position 1 validated
**Target State:** Full validation matrix complete, production-ready engine

---

## Phase 0: Deployment Discovery (COMPLETE)

```
✓ guitar.projectlavos.com/tabplayer - Working MIDI playback
✓ TabPlayer.jsx - Multi-digit fret parsing fixed
✓ generate_riff_v2.py - Deterministic generator working
✓ guitar_theory.py - Music theory module implemented
```

---

## Phase 1: Task Identification

### Batch 1 - Core Scales Validation (4 parallel tasks)

| Priority | Task | Scale/Root | Patterns | Est. Time |
|----------|------|------------|----------|-----------|
| 🔴 1 | Validate A Minor | A minor | ascending, descending | 15 min |
| 🔴 2 | Validate E Minor | E minor | ascending, pedal | 15 min |
| 🟠 3 | Validate G Major | G major | ascending, arpeggio | 15 min |
| 🟠 4 | Validate E Blues | E blues | ascending, random | 15 min |

### Batch 2 - Position Coverage (4 parallel tasks)

| Priority | Task | Scale | Positions | Est. Time |
|----------|------|-------|-----------|-----------|
| 🔴 1 | E Phrygian positions | E phrygian | 1, 2, 3, 4, 5 | 20 min |
| 🟠 2 | A Minor positions | A minor | 1, 2, 3, 4, 5 | 20 min |
| 🟡 3 | E Minor positions | E minor | 1, 2, 3, 4, 5 | 20 min |
| 🟢 4 | G Major positions | G major | 1, 2, 3, 4, 5 | 20 min |

### Batch 3 - Pattern Types (4 parallel tasks)

| Priority | Task | Pattern | Scales to Test | Est. Time |
|----------|------|---------|----------------|-----------|
| 🔴 1 | 3NPS validation | 3nps | E phrygian, A minor | 20 min |
| 🟠 2 | Pedal tone validation | pedal | E minor, G major | 15 min |
| 🟡 3 | Arpeggio validation | arpeggio | All validated scales | 15 min |
| 🟢 4 | Descending validation | descending | All validated scales | 15 min |

### Batch 4 - Extended Scales (4 parallel tasks)

| Priority | Task | Scales | Root Notes | Est. Time |
|----------|------|--------|------------|-----------|
| 🔴 1 | Pentatonic scales | pentatonic_minor, pentatonic_major | E, A, G | 20 min |
| 🟠 2 | Modal scales | dorian, lydian, mixolydian | E, A | 20 min |
| 🟡 3 | Exotic scales | harmonic_minor, melodic_minor | E, A | 20 min |
| 🟢 4 | Locrian validation | locrian | B, E | 15 min |

---

## Phase 2: Terminal Prompts

### Batch 1, Task 1: A Minor Validation

```markdown
cd ~/Projects/guitar-model-lab

## Task: Validate A Minor Scale Generation

**Context**: Guitar theory engine generating deterministic tabs. Need to validate A minor scale produces correct, playable output.

**Goal**: Verify A minor ascending/descending patterns work correctly with --play

**Validation Steps**:
1. Generate A minor ascending position 1:
   ```bash
   python3 generate_riff_v2.py --root A --scale minor --pattern ascending --position 1 --bars 2 --play
   ```
2. Verify in browser: audio matches visual tab
3. Verify fingering: all frets within 4-fret span
4. Generate descending and verify same way

**Expected A Minor Notes**: A, B, C, D, E, F, G

**Success Criteria**:
- [ ] Ascending audio matches visual
- [ ] Descending audio matches visual
- [ ] Frets within playable box (4-fret span)
- [ ] Update protocol.md validation matrix

**Output**: Report PASS or FAIL with details
```

### Batch 1, Task 2: E Minor Validation

```markdown
cd ~/Projects/guitar-model-lab

## Task: Validate E Minor Scale Generation

**Context**: Guitar theory engine generating deterministic tabs.

**Goal**: Verify E minor ascending/pedal patterns work correctly

**Validation Steps**:
1. Generate E minor ascending position 1:
   ```bash
   python3 generate_riff_v2.py --root E --scale minor --pattern ascending --position 1 --bars 2 --play
   ```
2. Generate E minor pedal:
   ```bash
   python3 generate_riff_v2.py --root E --scale minor --pattern pedal --position 1 --bars 2 --play
   ```
3. Verify each in browser

**Expected E Minor Notes**: E, F#, G, A, B, C, D

**Success Criteria**:
- [ ] Ascending audio matches visual
- [ ] Pedal audio matches visual
- [ ] Update protocol.md validation matrix

**Output**: Report PASS or FAIL with details
```

### Batch 1, Task 3: G Major Validation

```markdown
cd ~/Projects/guitar-model-lab

## Task: Validate G Major Scale Generation

**Context**: Guitar theory engine generating deterministic tabs.

**Goal**: Verify G major ascending/arpeggio patterns work correctly

**Validation Steps**:
1. Generate G major ascending:
   ```bash
   python3 generate_riff_v2.py --root G --scale major --pattern ascending --position 1 --bars 2 --play
   ```
2. Generate G major arpeggio:
   ```bash
   python3 generate_riff_v2.py --root G --scale major --pattern arpeggio --position 1 --bars 2 --play
   ```

**Expected G Major Notes**: G, A, B, C, D, E, F#

**Success Criteria**:
- [ ] Ascending audio matches visual
- [ ] Arpeggio audio matches visual
- [ ] Update protocol.md validation matrix

**Output**: Report PASS or FAIL with details
```

### Batch 1, Task 4: E Blues Validation

```markdown
cd ~/Projects/guitar-model-lab

## Task: Validate E Blues Scale Generation

**Context**: Guitar theory engine generating deterministic tabs.

**Goal**: Verify E blues ascending/random patterns work correctly

**Validation Steps**:
1. Generate E blues ascending:
   ```bash
   python3 generate_riff_v2.py --root E --scale blues --pattern ascending --position 1 --bars 2 --play
   ```
2. Generate E blues random:
   ```bash
   python3 generate_riff_v2.py --root E --scale blues --pattern random --position 1 --bars 2 --play
   ```

**Expected E Blues Notes**: E, G, A, Bb, B, D (6 notes)

**Success Criteria**:
- [ ] Ascending audio matches visual
- [ ] Random stays within box position
- [ ] Update protocol.md validation matrix

**Output**: Report PASS or FAIL with details
```

---

## Phase 3: Automated Validation Script

Create a validation runner that can test multiple combinations:

```python
# validate_all.py - Batch validation script
#!/usr/bin/env python3
"""
Automated validation for guitar theory engine.
Tests scale/pattern combinations and reports results.
"""

import subprocess
import sys
from guitar_theory import GuitarTheory, generate_tab, SCALES

ROOTS = ['E', 'A', 'D', 'G', 'C']
PATTERNS = ['ascending', 'descending', 'pedal', 'arpeggio']
POSITIONS = [1, 2, 3]

def validate_combination(root, scale, pattern, position):
    """Generate tab and return validation result."""
    try:
        tab = generate_tab(root, scale, pattern, bars=2, position=position)

        # Check tab has content
        lines = tab.split('\n')
        has_notes = any(any(c.isdigit() for c in line) for line in lines)

        # Check fret range (should be within 5 frets)
        frets = []
        for line in lines:
            for char in line:
                if char.isdigit():
                    frets.append(int(char))

        if frets:
            fret_range = max(frets) - min(frets)
            playable = fret_range <= 5
        else:
            playable = False

        return {
            'root': root,
            'scale': scale,
            'pattern': pattern,
            'position': position,
            'has_notes': has_notes,
            'playable': playable,
            'fret_range': fret_range if frets else 0,
            'status': 'PASS' if (has_notes and playable) else 'FAIL'
        }
    except Exception as e:
        return {
            'root': root,
            'scale': scale,
            'pattern': pattern,
            'position': position,
            'status': 'ERROR',
            'error': str(e)
        }

def main():
    results = []

    for scale in SCALES.keys():
        for root in ROOTS:
            for pattern in PATTERNS:
                for position in POSITIONS:
                    result = validate_combination(root, scale, pattern, position)
                    results.append(result)
                    status = result['status']
                    print(f"{status}: {root} {scale} {pattern} pos{position}")

    # Summary
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    errors = sum(1 for r in results if r['status'] == 'ERROR')

    print(f"\n{'='*50}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*50}")
    print(f"Total: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")

    # Show failures
    if failed > 0:
        print(f"\nFailed combinations:")
        for r in results:
            if r['status'] == 'FAIL':
                print(f"  - {r['root']} {r['scale']} {r['pattern']} pos{r['position']}")

if __name__ == '__main__':
    main()
```

---

## Phase 4: Success Metrics

### Validation Targets

| Metric | Target | Current |
|--------|--------|---------|
| Scales validated | 12 | 1 |
| Root notes validated | 7 | 1 |
| Patterns validated | 6 | 1 |
| Positions validated | 5 | 1 |
| Total combinations | 720+ | 1 |
| Pass rate | 100% | N/A |

### Quality Criteria

For each combination to PASS:
1. **Audio matches visual** - What you see is what you hear
2. **Playable fingering** - All notes within 4-5 fret span
3. **Scale accuracy** - Only notes from the specified scale
4. **No errors** - Generation completes without exceptions

---

## Phase 5: Execution Schedule

### Day 1: Core Validation
- [ ] Batch 1: Core scales (A minor, E minor, G major, E blues)
- [ ] Run automated validation script
- [ ] Fix any failures found

### Day 2: Position Coverage
- [ ] Batch 2: All 5 positions for validated scales
- [ ] Document any position-specific issues

### Day 3: Pattern Coverage
- [ ] Batch 3: All pattern types
- [ ] Special attention to 3NPS (more complex)

### Day 4: Extended Scales
- [ ] Batch 4: Pentatonic, modal, exotic scales
- [ ] Full validation matrix completion

### Day 5: Production Readiness
- [ ] 100% pass rate achieved
- [ ] Documentation complete
- [ ] Integration with guitar.projectlavos.com finalized

---

## Files to Create

| File | Purpose | Status |
|------|---------|--------|
| `validate_all.py` | Automated batch validation | TODO |
| `VALIDATION_RESULTS.md` | Detailed test results | TODO |
| `guitar_theory_test.py` | Unit tests for theory module | TODO |

---

## Integration Roadmap

### Current: Standalone Generator
```
User → generate_riff_v2.py → TabPlayer (browser)
```

### Future: Platform Integration
```
User → guitar.projectlavos.com/riff-generator
       ↓
       Scale/Pattern selector UI
       ↓
       guitar_theory.py (server-side or WASM)
       ↓
       Inline TabPlayer with MIDI
```

### AI Enhancement Layer (Future)
```
User: "Give me something that sounds metal"
       ↓
       Ollama: Suggests scale=phrygian, pattern=pedal, tempo=fast
       ↓
       Python: Generates accurate tab
       ↓
       TabPlayer: Plays it back
```

---

## Quick Start Commands

```bash
# Validate single combination
python3 generate_riff_v2.py --root A --scale minor --pattern ascending --play

# Run batch validation
python3 validate_all.py

# Test specific position
python3 generate_riff_v2.py --root E --scale phrygian --position 3 --play

# Random generation
python3 generate_riff_v2.py --random --play
```

---

**Ready to execute.** Start with Batch 1 (4 parallel terminals) or run automated validation?
