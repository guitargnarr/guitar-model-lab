# Guitar Model Lab Protocol

## LIVE STATUS (update this section only)
```
Last check: 2025-12-11
STATUS: PHASES 4 & 5 COMPLETE - Full Feature Set Implemented

AUTOMATED VALIDATION RESULTS (with MIDI):
  Total tests:    2,520
  Skipped:        105 (3NPS + pentatonic/blues = invalid by design)
  Applicable:     2,415
  PASSED:         2,415 (100.0%)
  FAILED:         0
  ERRORS:         0

PHASE 4 COMPLETE - AI Creative Layer:
  ✓ ai_style_interpreter.py - Ollama style interpretation
  ✓ Natural language -> structured params (root, scale, pattern, etc.)
  ✓ Style mappings (metal, blues, jazz, rock, shred, etc.)
  ✓ Integration with generate_riff_v2.py via --ai flag

PHASE 5 COMPLETE - Advanced Features:
  ✓ Chord progressions (7 types: blues_12bar, pop_4chord, rock_power, etc.)
  ✓ Multiple tunings (standard, drop_d, drop_c, half_step_down)
  ✓ Power chord pattern
  ✓ Progression pattern

UI INTEGRATION (guitar.projectlavos.com):
  ✓ guitarTheory.js synced with Python backend
  ✓ RiffGenerator.jsx updated with tuning/progression selectors
  ✓ Build verified - all components working

VALIDATED SCALES (12/12):
  ✓ major, minor, phrygian, dorian, lydian, mixolydian
  ✓ locrian, harmonic_minor, melodic_minor
  ✓ pentatonic_major, pentatonic_minor, blues

VALIDATED PATTERNS (8/8):
  ✓ ascending, descending, pedal, arpeggio, random, 3nps
  ✓ power_chords, progression (NEW)

VALIDATED POSITIONS: 1-5 across all scales
VALIDATED ROOTS: E, A, D, G, C, F, B
VALIDATED TUNINGS: standard, drop_d, drop_c, half_step_down

NEXT STEPS:
  - Deploy to guitar.projectlavos.com (DONE)
  - MIDI file export (browser: RiffGenerator.jsx)
  - Guitar Pro export format (DONE: --gp5 flag)

VALIDATION COMMANDS:
  python3 validate_all.py          # Full validation (2,415 tests)
  python3 validate_midi.py --quick # Quick E Phrygian test
  python3 validate_midi.py         # MIDI-only validation (900 tests)
```

## What We're Building

### The Vision
A complete guitar education platform where:
1. User requests any scale/key/pattern combination
2. System generates 100% accurate, playable tabs
3. Visual tab + audio playback are perfectly synchronized
4. All 144 scale/root combinations work reliably
5. AI assists with creative direction, Python ensures accuracy

### Where We Started (Ollama Approach)
- LLM generates creative tab output
- Python validates against scale rules
- Auto-correction fixes invalid frets
- **Problem:** AI unreliable for deterministic tasks (fret mapping)

### Where We Are Now (Hybrid Approach)
- Python handles all note/fret calculations (deterministic)
- Box positions ensure playable fingering (CAGED system)
- TabPlayer parses and plays correctly
- **Validated:** E Phrygian position 1 only (1 of 144+ combinations)

### Where We're Going
- Validate all 12 scales × 12 roots = 144 combinations
- 5 positions per scale = 720 box patterns
- Multiple pattern types (ascending, descending, pedal, arpeggio, 3nps)
- AI role: creative pattern selection, not note generation
- Ollama models: may still be useful for "style" and "feel" suggestions

---

## Current Commands

### V2 Generator (Deterministic - RECOMMENDED)
```bash
python3 ~/Projects/guitar-model-lab/generate_riff_v2.py [options] --play

Options:
  --root E|A|D|G|C|F|B    Root note (default: E)
  --scale phrygian|minor|major|pentatonic_minor|blues|...
  --pattern ascending|descending|pedal|arpeggio|random|3nps|power_chords|progression
  --position 1-5          Box position (default: 1)
  --bars N                Number of measures (default: 4)
  --tuning standard|drop_d|drop_c|half_step_down (NEW)
  --progression blues_12bar|pop_4chord|rock_power|jazz_251|metal_riff|sad_progression|andalusian (NEW)
  --ai "style description" Use AI to interpret style, e.g. "aggressive metal" (NEW)
  --random                Randomize everything
  --play                  Open browser with MIDI playback

Examples:
  python3 generate_riff_v2.py --ai "aggressive metal in E"
  python3 generate_riff_v2.py --pattern progression --progression blues_12bar --root A
  python3 generate_riff_v2.py --pattern power_chords --tuning drop_d --root D
```

### V1 Generator (Ollama-based - Legacy)
```bash
python3 ~/Projects/guitar-model-lab/generate_riff.py [scale] [--play] [--random]
```

---

## Files

### Core (V2 - Deterministic)
| File | Purpose |
|------|---------|
| `guitar_theory.py` | Music theory: scales, tunings, box positions, 3NPS, chord progressions |
| `generate_riff_v2.py` | Tab generator using Python (no AI) |
| `ai_style_interpreter.py` | Phase 4: Ollama-based style interpretation |

### Legacy (V1 - Ollama)
| File | Purpose |
|------|---------|
| `generate_riff.py` | Tab generator using Ollama model |
| `validate_tab.py` | Scale validation + auto-correction |

### Dashboard
| Location | Purpose |
|----------|---------|
| `guitar.projectlavos.com/tabplayer` | MIDI playback with tab display |
| `TabPlayer.jsx` | React component (multi-digit fret parsing fixed) |

---

## Validation Matrix (Automated - 2025-12-10)

### Scales (12/12 - 100%)
| Scale | E | A | D | G | C | F | B |
|-------|---|---|---|---|---|---|---|
| Major | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Minor | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Phrygian | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Dorian | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Lydian | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Mixolydian | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Locrian | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Harmonic Minor | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Melodic Minor | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Pentatonic Major | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Pentatonic Minor | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Blues | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

✓ = All patterns/positions pass automated validation

### Patterns (6/6 - 100%)
| Pattern | Status | Notes |
|---------|--------|-------|
| Ascending | ✓ | Box position, string-by-string |
| Descending | ✓ | Reverse of ascending |
| Pedal | ✓ | Root + melody alternating |
| Arpeggio | ✓ | 1-3-5 sweep pattern |
| Random | ✓ | Weighted adjacent strings |
| 3NPS | ✓ | 7-note scales only (by design) |

### Positions (5/5 - 100%)
All positions 1-5 validated across all scales and patterns.

---

## Cross-Session Protocol

### Hook Configuration
User-prompt-submit hook monitors this protocol file.

### Dual Terminal Coordination
- Terminal A: Primary development
- Terminal B: Benchmarking/validation (may be running tests)
- Both read/write to this protocol.md

### On Each Check
1. Run `date "+%Y-%m-%d %H:%M:%S"` for timestamp
2. Update LIVE STATUS section
3. Mark validated combinations in matrix
4. Note any failures or issues

---

## Key Learnings

### AI Limitations (Proven)
- Small models can't do arithmetic reliably
- Fret-to-note mapping is a lookup table, not creativity
- AI generates "plausible-looking" tabs that are musically wrong

### Python Strengths (Proven)
- Deterministic = 100% accurate every time
- Box positions from music theory = playable fingering
- No validation needed when generation is correct by design

### Hybrid Approach (Hypothesis)
- AI for: "Give me something that sounds metal" (style/feel)
- Python for: "These are the actual notes to play" (accuracy)
- Best of both worlds (not yet fully implemented)

---

## Ollama Models (Preserved)

```
guitar_expert_precise (2.0GB)
Base: llama3.2 | Temp: 0.4 | Top_p: 0.85 | Context: 16384
```

### Potential Future Use
- Style suggestions ("make it sound more aggressive")
- Pattern complexity hints ("add some chromaticism")
- Creative variations on deterministic base
- NOT for note/fret generation (proven unreliable)

---

## Next Actions

### Phase 1: Engine Validation (COMPLETE)
- [x] E Phrygian manual audio test
- [x] Automated validation suite (2,415 tests passing)
- [x] Box position implementation
- [x] 3NPS pattern implementation

### Phase 2: Manual Audio Verification (IN PROGRESS)
- [ ] Random sample of 10 scale/pattern combos with --play
- [ ] User confirms audio matches visual
- [ ] Document any edge cases

### Phase 3: Platform Integration
- [ ] Add scale selector UI to guitar.projectlavos.com
- [ ] Server-side or client-side generation
- [ ] Replace current tab sources with generated content

### Phase 4: AI Creative Layer (COMPLETE - 2025-12-11)
- [x] Ollama for style suggestions ("make it metal")
- [x] AI picks pattern type, Python generates notes
- [x] Natural language → tab generation via --ai flag
- [x] ai_style_interpreter.py with style mappings

### Phase 5: Advanced Features (COMPLETE - 2025-12-11)
- [x] Chord progressions (7 types implemented)
- [x] Multiple tunings (drop D, drop C, half-step down)
- [x] Power chord pattern
- [x] UI integration with RiffGenerator.jsx
- [ ] Tab export formats (Guitar Pro, MIDI file) - Future
