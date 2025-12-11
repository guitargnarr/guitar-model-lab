# Guitar Model Lab

**Goal:** Generate theoretically accurate guitar tabs via Ollama models, validate via web playback.

## Current Status
| Model | Base | Benchmark | Status |
|-------|------|-----------|--------|
| guitar_expert_precise | llama3.2 (2.0GB) | E Phrygian 5-pass | **Test 5 running** |

## Model Config
```
Temperature: 0.4 | Top_p: 0.85 | Context: 16384
Default tuning: EADGBE
```

## Validation Criteria (E Phrygian)
- **Valid notes:** E, F, G, A, B, C, D only
- **Tab format:** 6-line (e/B/G/D/A/E)
- **Pass:** All frets map to scale degrees
- **Fail:** Chromatic notes (F#, Bb, etc.)

## End Goal
```
User: "give me a random riff"
→ generates tab → opens dashboard → plays audio
```

## Reference
- Protocol: `./protocol.md`
- Cross-session: `~/.claude/reference/cross-session-context-protocol.md`
- Modelfile: `~/.claude/reference/guitar-ollama-workflow.md`
