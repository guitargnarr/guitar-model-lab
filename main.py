#!/usr/bin/env python3
"""
Guitar Platform API
Generates GP5 files from tab parameters
"""

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import tempfile
import os

from guitar_theory import generate_tab, SCALES, TUNINGS, CHORD_PROGRESSIONS
from export_gp import tab_to_gp5

app = FastAPI(
    title="Guitar Platform API",
    description="Generate Guitar Pro files from scale/pattern parameters",
    version="1.0.0"
)

# CORS for guitar.projectlavos.com
# NOTE: Cannot use allow_credentials=True with wildcard origins (security vulnerability)
# Fixed 2025-12-12 based on Mirador security audit
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://guitar.projectlavos.com",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Available patterns
PATTERNS = [
    'ascending', 'descending', 'pedal', 'arpeggio', 'random', '3nps',
    'power_chords', 'progression'
]


class GenerateRequest(BaseModel):
    root: str = "E"
    scale: str = "phrygian"
    pattern: str = "ascending"
    bars: int = 4
    tuning: str = "standard"
    tempo: int = 120
    position: int = 1
    progression: Optional[str] = None
    title: Optional[str] = None


@app.get("/")
def root():
    return {
        "name": "Guitar Platform API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/generate-gp5": "POST - Generate GP5 file",
            "/generate-tab": "POST - Generate ASCII tab",
            "/scales": "GET - List available scales",
            "/patterns": "GET - List available patterns",
            "/tunings": "GET - List available tunings",
        }
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/scales")
def list_scales():
    return {"scales": list(SCALES.keys())}


@app.get("/tunings")
def list_tunings():
    return {"tunings": list(TUNINGS.keys())}


@app.get("/patterns")
def list_patterns():
    return {"patterns": PATTERNS}


@app.get("/progressions")
def list_progressions():
    return {"progressions": list(CHORD_PROGRESSIONS.keys())}


@app.post("/generate-gp5")
def generate_gp5(request: GenerateRequest):
    """Generate a Guitar Pro 5 file from parameters"""
    try:
        # Generate tab using guitar_theory
        tab = generate_tab(
            root=request.root,
            scale=request.scale,
            pattern=request.pattern,
            bars=request.bars,
            position=request.position,
            tuning=request.tuning,
            progression=request.progression
        )

        # Create title
        title = request.title or f"{request.root} {request.scale.replace('_', ' ').title()} - {request.pattern.title()}"

        # Generate GP5 to temp file
        with tempfile.NamedTemporaryFile(suffix='.gp5', delete=False) as f:
            temp_path = f.name

        try:
            tab_to_gp5(
                tab_text=tab,
                title=title,
                tempo=request.tempo,
                tuning=request.tuning,
                output_path=temp_path
            )

            # Read and return the file
            with open(temp_path, 'rb') as f:
                gp5_data = f.read()

            # Generate filename
            filename = f"{request.root}_{request.scale}_{request.pattern}.gp5"

            return Response(
                content=gp5_data,
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-tab")
def generate_tab_endpoint(request: GenerateRequest):
    """Generate ASCII tab (no GP5, just text)"""
    try:
        tab = generate_tab(
            root=request.root,
            scale=request.scale,
            pattern=request.pattern,
            bars=request.bars,
            position=request.position,
            tuning=request.tuning,
            progression=request.progression
        )

        return {
            "tab": tab,
            "root": request.root,
            "scale": request.scale,
            "pattern": request.pattern,
            "bars": request.bars,
            "position": request.position,
            "tuning": request.tuning,
            "tempo": request.tempo,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
