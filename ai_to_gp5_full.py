#!/usr/bin/env python3
"""
AI Full Band GP5 Generator - Guitar + Drums in one file

Combines:
- lead_architect / rhythm_architect for guitar style
- drum_architect for drum style
- Deterministic Python generation for both

Usage:
    python3 ai_to_gp5_full.py "Meshuggah djent groove at 130 BPM"
    python3 ai_to_gp5_full.py "Tool tribal progressive" --bars 8
    python3 ai_to_gp5_full.py "blast beat thrash metal at 200 BPM" --lead
"""

import json
import subprocess
import sys
import argparse
import re
import os
from datetime import datetime

import guitarpro
from guitarpro.models import (
    Song, Track, Measure, Voice, Beat, Note,
    MeasureHeader, Duration, NoteType
)

from guitar_theory import GuitarTheory, TabGenerator, generate_tab, SCALES
from drum_theory import (
    DrumPatternGenerator, get_pattern_from_style, DRUM_MAP,
    PATTERN_MAP as DRUM_PATTERN_MAP
)
from export_gp import parse_ascii_tab, TUNING_MIDI


# Pattern mappings (from ai_to_gp5.py)
GUITAR_PATTERN_MAP = {
    "3-note-per-string": "3nps",
    "3nps": "3nps",
    "legato": "ascending",
    "sweep arpeggio": "arpeggio",
    "arpeggio": "arpeggio",
    "pedal": "pedal",
    "power_chord": "power_chords",
    "ascending": "ascending",
    "descending": "descending",
}

SCALE_MAP = [
    ("harmonic minor", ("A", "harmonic_minor")),
    ("melodic minor", ("A", "melodic_minor")),
    ("pentatonic", ("A", "pentatonic_minor")),
    ("phrygian", ("E", "phrygian")),
    ("dorian", ("D", "dorian")),
    ("minor", ("A", "minor")),
    ("blues", ("A", "blues")),
    ("mixolydian", ("G", "mixolydian")),
    ("lydian", ("F", "lydian")),
    ("major", ("C", "major")),
]


def query_ollama(model: str, prompt: str) -> dict:
    """Query Ollama model and parse JSON response."""
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=60
        )
        response = result.stdout.strip()

        # Extract JSON
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"Warning: {model} query failed: {e}")
    return {}


def extract_tempo(prompt: str, ai_response: dict = None) -> int:
    """Extract tempo from prompt or AI response."""
    # Try prompt first
    patterns = [r'(\d+)\s*bpm', r'at\s+(\d+)', r'tempo\s+(\d+)']
    for pattern in patterns:
        match = re.search(pattern, prompt.lower())
        if match:
            tempo = int(match.group(1))
            if 40 <= tempo <= 300:
                return tempo

    # Try AI response
    if ai_response:
        tempo_range = ai_response.get("tempo_range", [])
        if tempo_range and len(tempo_range) >= 2:
            return (tempo_range[0] + tempo_range[1]) // 2
        if "tempo" in ai_response:
            return int(ai_response["tempo"])
        style = ai_response.get("style_profile", {})
        if "tempo" in style:
            return int(style["tempo"])

    return 120


def get_guitar_params(prompt: str, is_lead: bool = True) -> dict:
    """Get guitar parameters from AI interpretation."""
    model = "lead_architect" if is_lead else "rhythm_architect"
    print(f"Querying {model}...")

    ai_response = query_ollama(model, prompt)

    # Extract scale
    root, scale = "E", "phrygian"
    scale_suggestion = ai_response.get("scale_suggestion", "").lower()
    for scale_key, (default_root, scale_name) in SCALE_MAP:
        if scale_key in scale_suggestion:
            scale = scale_name
            # Try to get root from suggestion
            parts = scale_suggestion.split()
            if parts and len(parts[0]) <= 2:
                potential = parts[0].upper().replace("B", "B").replace("#", "#")
                if potential in ["A", "B", "C", "D", "E", "F", "G", "A#", "C#", "D#", "F#", "G#"]:
                    root = potential
                else:
                    root = default_root
            break

    # Extract pattern
    pattern = "3nps" if is_lead else "power_chords"
    patterns = ai_response.get("pattern_recommendations", [])
    if patterns:
        ptype = patterns[0].get("type", "").lower()
        for ai_pat, gen_pat in GUITAR_PATTERN_MAP.items():
            if ai_pat in ptype:
                pattern = gen_pat
                break

    # Handle non-7-note scales with 3nps
    if pattern == "3nps" and scale in ["pentatonic_minor", "pentatonic_major", "blues"]:
        pattern = "ascending"

    tempo = extract_tempo(prompt, ai_response)

    return {
        "root": root,
        "scale": scale,
        "pattern": pattern,
        "tempo": tempo,
        "ai_response": ai_response
    }


def get_drum_params(prompt: str) -> dict:
    """Get drum parameters from AI interpretation."""
    print("Querying drum_architect...")

    ai_response = query_ollama("drum_architect", prompt)

    pattern_type = ai_response.get("pattern_type", "")
    if pattern_type not in DrumPatternGenerator().patterns:
        pattern_type = get_pattern_from_style(prompt)

    tempo = extract_tempo(prompt, ai_response)

    return {
        "pattern": pattern_type,
        "tempo": tempo,
        "ai_response": ai_response
    }


def create_combined_gp5(
    guitar_tab: str,
    drum_bars: list,
    title: str = "Full Band",
    tempo: int = 120,
    tuning: str = "standard",
    output_path: str = None,
    is_lead: bool = True
) -> str:
    """Create a GP5 file with both guitar and drum tracks."""

    song = Song()
    song.title = title
    song.tempo = tempo
    song.artist = "Guitar Model Lab"

    # Parse guitar tab
    guitar_beats = parse_ascii_tab(guitar_tab)
    beats_per_measure = 4
    num_measures = max(len(drum_bars), (len(guitar_beats) + beats_per_measure - 1) // beats_per_measure)

    # Ensure we have enough measure headers
    while len(song.measureHeaders) < num_measures:
        header = MeasureHeader()
        header.number = len(song.measureHeaders) + 1
        song.measureHeaders.append(header)

    # === TRACK 1: Guitar ===
    guitar_track = song.tracks[0]
    guitar_track.name = "Lead Guitar" if is_lead else "Rhythm Guitar"
    guitar_track.channel.instrument = 25 if is_lead else 26  # Steel/Jazz Guitar

    # Set tuning
    tuning_midi = TUNING_MIDI.get(tuning, TUNING_MIDI['standard'])
    for i, midi_val in enumerate(tuning_midi):
        guitar_track.strings[i].value = midi_val

    # Ensure guitar track has measures for all headers
    while len(guitar_track.measures) < num_measures:
        header = song.measureHeaders[len(guitar_track.measures)]
        measure = Measure(guitar_track, header)
        voice = Voice(measure)
        measure.voices.append(voice)
        guitar_track.measures.append(measure)

    # Fill guitar track
    beat_idx = 0
    for measure_num in range(num_measures):
        measure = guitar_track.measures[measure_num]
        voice = measure.voices[0]
        voice.beats.clear()

        for _ in range(beats_per_measure):
            beat = Beat(voice)
            beat.duration = Duration()
            beat.duration.value = 4  # Quarter note

            if beat_idx < len(guitar_beats):
                beat_data = guitar_beats[beat_idx]
                for string_num, fret in beat_data.items():
                    note = Note(beat)
                    note.string = string_num
                    note.value = fret
                    note.velocity = 95
                    note.type = NoteType.normal
                    beat.notes.append(note)
                beat_idx += 1
            else:
                beat.status = guitarpro.BeatStatus.rest

            voice.beats.append(beat)

    # === TRACK 2: Drums ===
    drum_track = Track(song)
    drum_track.name = "Drums"
    drum_track.channel.instrument = 0
    drum_track.channel.channel = 9  # MIDI channel 10
    drum_track.isPercussionTrack = True

    # Set up drum strings
    drum_track.strings = []
    drum_midi_notes = [36, 38, 42, 46, 49, 51, 50, 47, 45, 43, 52, 55]
    for i, midi_note in enumerate(drum_midi_notes):
        string = guitarpro.models.GuitarString(number=i + 1, value=midi_note)
        drum_track.strings.append(string)

    # Create measures for drum track
    for header in song.measureHeaders:
        measure = Measure(drum_track, header)
        voice = Voice(measure)
        measure.voices.append(voice)
        drum_track.measures.append(measure)

    # Fill drum track
    for measure_num in range(num_measures):
        measure = drum_track.measures[measure_num]
        voice = measure.voices[0]
        voice.beats.clear()

        # Get drum bar for this measure (loop if needed)
        if drum_bars:
            drum_bar = drum_bars[measure_num % len(drum_bars)]

            # Group hits by position
            hits_by_pos = {}
            for hit in drum_bar.hits:
                if hit.position not in hits_by_pos:
                    hits_by_pos[hit.position] = []
                hits_by_pos[hit.position].append(hit)

            # Create 16th note beats
            for pos in range(1, 17):
                beat = Beat(voice)
                beat.duration = Duration()
                beat.duration.value = 16  # 16th note

                if pos in hits_by_pos:
                    for hit in hits_by_pos[pos]:
                        if hit.drum in DRUM_MAP:
                            note = Note(beat)
                            note.value = DRUM_MAP[hit.drum]
                            note.string = 1
                            note.velocity = hit.velocity
                            note.type = NoteType.normal
                            beat.notes.append(note)

                if not beat.notes:
                    beat.status = guitarpro.BeatStatus.rest

                voice.beats.append(beat)
        else:
            # No drums - rest measure
            for _ in range(4):
                beat = Beat(voice)
                beat.duration = Duration()
                beat.duration.value = 4
                beat.status = guitarpro.BeatStatus.rest
                voice.beats.append(beat)

    # Add drum track to song
    song.tracks.append(drum_track)

    # Write file
    if output_path is None:
        timestamp = datetime.now().strftime("%H%M%S")
        output_path = os.path.expanduser(f"~/Desktop/{title}_{timestamp}.gp5")

    guitarpro.write(song, output_path)
    return output_path


def generate_full_band(prompt: str, bars: int = 4, is_lead: bool = False, output_path: str = None) -> str:
    """Generate a full band GP5 with guitar + drums."""

    print("=" * 60)
    print("AI Full Band GP5 Generator")
    print("=" * 60)
    print(f"Prompt: {prompt}")
    print(f"Bars: {bars}")
    print(f"Guitar: {'Lead' if is_lead else 'Rhythm'}")
    print("=" * 60)

    # Get parameters from AI
    guitar_params = get_guitar_params(prompt, is_lead)
    drum_params = get_drum_params(prompt)

    # Use consistent tempo (average if different)
    tempo = (guitar_params["tempo"] + drum_params["tempo"]) // 2

    print(f"\nGuitar: {guitar_params['root']} {guitar_params['scale']} - {guitar_params['pattern']}")
    print(f"Drums: {drum_params['pattern']}")
    print(f"Tempo: {tempo} BPM")

    # Generate guitar tab
    print("\nGenerating guitar tab...")
    guitar_tab = generate_tab(
        guitar_params["root"],
        guitar_params["scale"],
        guitar_params["pattern"],
        bars=bars,
        position=1
    )
    print(guitar_tab)

    # Generate drum pattern
    print("\nGenerating drum pattern...")
    generator = DrumPatternGenerator()
    drum_bars = generator.generate_pattern(
        drum_params["pattern"],
        bars=bars,
        add_crashes=True,
        add_fills=True
    )

    # Create title
    title = f"FullBand_{guitar_params['root']}_{guitar_params['scale']}_{drum_params['pattern']}_{tempo}bpm"

    # Create combined GP5
    print("\nCreating combined GP5...")
    output_file = create_combined_gp5(
        guitar_tab,
        drum_bars,
        title=title,
        tempo=tempo,
        is_lead=is_lead,
        output_path=output_path
    )

    print(f"\n{'=' * 60}")
    print(f"SUCCESS! Created: {output_file}")
    print(f"{'=' * 60}")

    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Generate GP5 with guitar + drums"
    )
    parser.add_argument(
        "prompt",
        help="Style description (e.g., 'Meshuggah djent groove at 130 BPM')"
    )
    parser.add_argument(
        "-b", "--bars",
        type=int,
        default=4,
        help="Number of bars (default: 4)"
    )
    parser.add_argument(
        "-l", "--lead",
        action="store_true",
        help="Use lead guitar instead of rhythm"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output .gp5 file path"
    )

    args = parser.parse_args()

    generate_full_band(
        args.prompt,
        bars=args.bars,
        is_lead=args.lead,
        output_path=args.output
    )


if __name__ == "__main__":
    main()
