# Guitar Model Lab - Claude Context

**Project:** `~/Projects/guitar-model-lab/`
**Goal:** Generate accurate tabs → auto-play in web dashboard

## Live Status

- **API:** https://guitar-model-lab.onrender.com (FastAPI, free tier - spins down after 15min)
- **Frontend:** https://guitar.projectlavos.com/riff-generator (GP5 button calls API)
- **Flow:** Generate riff → Click GP5 → Downloads .gp5 file → Open in Guitar Pro

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI with `/generate-gp5`, `/generate-tab`, `/scales`, `/patterns`, `/tunings` |
| `guitar_theory.py` | Deterministic tab generation (12 scales, 4 tunings, 8 patterns) |
| `export_gp.py` | PyGuitarPro GP5 file generation |
| `ai_style_interpreter.py` | AI style interpretation only |

## Critical Lesson

**LLMs generate musically INCORRECT tabs** (F# in E Phrygian - proven Dec 10).

Use Python for deterministic note generation, AI only for style interpretation:
- "aggressive metal" → `{root: E, scale: phrygian, pattern: pedal}`

## Cross-Session Communication

1. Check other session: `tail -15 ~/.claude/projects/-Users-matthewscott/b1079d33*.jsonl | jq -r '.toolUseResult.command // .message.content[0:300]'`
2. Issue directives via `SESSION_DIRECTIVE.md`
3. Update `protocol.md` LIVE STATUS on each check
4. **20 min limit** - if no 5 passes, propose solution

## Related Docs

- Protocol: `~/Projects/guitar-model-lab/protocol.md`
- Directive: `~/Projects/guitar-model-lab/SESSION_DIRECTIVE.md`
- Cross-session: `~/.claude/reference/cross-session-context-protocol.md`

## End Goal

`"give me a random riff"` → generates tab → opens dashboard → plays audio
