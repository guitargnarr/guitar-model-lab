# Guitar Model Lab

Production API for generating Guitar Pro 5 (.gp5) files from scale/pattern parameters.

**Live API:** https://guitar-model-lab.onrender.com

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    guitar.projectlavos.com                      │
│                      (React Frontend)                           │
└─────────────────────────┬───────────────────────────────────────┘
                          │ POST /generate-gp5
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 guitar-model-lab.onrender.com                   │
│                    (FastAPI Backend)                            │
├─────────────────────────────────────────────────────────────────┤
│  main.py          → API routes & request handling               │
│  guitar_theory.py → Deterministic note generation               │
│  export_gp.py     → PyGuitarPro GP5 file creation               │
└─────────────────────────┬───────────────────────────────────────┘
                          │ Returns .gp5 binary
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Guitar Pro 8                               │
│              (User opens downloaded file)                       │
└─────────────────────────────────────────────────────────────────┘
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/generate-gp5` | POST | Generate GP5 file from parameters |
| `/generate-tab` | POST | Generate ASCII tab |
| `/scales` | GET | List available scales (12) |
| `/patterns` | GET | List available patterns (8) |
| `/tunings` | GET | List available tunings (4) |

## Quick Start

```bash
# Health check
curl https://guitar-model-lab.onrender.com/health

# Generate GP5 file
curl -X POST https://guitar-model-lab.onrender.com/generate-gp5 \
  -H "Content-Type: application/json" \
  -d '{"root":"E","scale":"phrygian","pattern":"ascending"}' \
  -o riff.gp5

# Open in Guitar Pro
open riff.gp5
```

## Parameters

**Roots:** C, C#, D, D#, E, F, F#, G, G#, A, A#, B

**Scales (12):**
- Major, Minor, Pentatonic Major, Pentatonic Minor
- Blues, Dorian, Phrygian, Lydian
- Mixolydian, Harmonic Minor, Melodic Minor, Locrian

**Patterns (8):**
- ascending, descending, pedal, arpeggio
- random, 3nps, power_chords, progression

**Tunings (4):**
- standard, drop_d, drop_c, half_step_down

## Why Deterministic Python (Not LLM)

We tested Ollama models (llama3.2, codellama, mistral) for tab generation. **They consistently produce musically incorrect output** - generating F# in E Phrygian, wrong fret positions, invalid intervals.

**Solution:** Python handles all note/fret calculations deterministically. 100% accuracy across 2,415 test combinations.

## Tech Stack

- **Framework:** FastAPI
- **GP5 Generation:** PyGuitarPro
- **Music Theory:** Pure Python (no ML)
- **Hosting:** Render (free tier, ~30s cold start)

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload --port 8000

# Test
curl http://localhost:8000/health
```

## Integration

Frontend integration in `RiffGenerator.jsx`:
```javascript
const response = await fetch(`${GP5_API_URL}/generate-gp5`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ root, scale, pattern, tuning })
});
const blob = await response.blob();
// Trigger download...
```

## Related

- **Frontend:** [guitar.projectlavos.com/riff-generator](https://guitar.projectlavos.com/riff-generator)
- **Monorepo:** [projectlavos-monorepo](https://github.com/guitargnarr/projectlavos-monorepo)

---

Built with Claude Code | Dec 2025
