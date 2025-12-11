#!/usr/bin/env python3
"""
Guitar Pro Export Module
Converts ASCII tab output to .gp5 format
"""

import guitarpro
from guitarpro.models import (
    Song, Track, Measure, Voice, Beat, Note,
    MeasureHeader, Duration, NoteType
)
import sys
import re
import argparse

# Standard tuning MIDI values (string 1=high e to string 6=low E)
TUNING_MIDI = {
    'standard': [64, 59, 55, 50, 45, 40],
    'drop_d': [64, 59, 55, 50, 45, 38],
    'drop_c': [62, 57, 53, 48, 43, 36],
    'half_step_down': [63, 58, 54, 49, 44, 39],
}


def parse_tab_line(line: str) -> tuple:
    """Parse a single tab line like 'e|--0--2--3--'"""
    match = re.match(r'^([eEBGDA])\|(.+)$', line.strip())
    if not match:
        return None, []

    string_name = match.group(1)
    content = match.group(2)

    # Parse fret numbers (handle multi-digit)
    frets = []
    i = 0
    while i < len(content):
        if content[i] == '-':
            frets.append('-')
            i += 1
        elif content[i].isdigit():
            num = ''
            while i < len(content) and content[i].isdigit():
                num += content[i]
                i += 1
            frets.append(num)
        else:
            i += 1

    return string_name, frets


def parse_ascii_tab(tab_text: str) -> list:
    """
    Parse ASCII tab into beat data.
    Returns list of beats, each beat is {string_num: fret_num}
    """
    lines = tab_text.strip().split('\n')

    # String order: e(1), B(2), G(3), D(4), A(5), E(6)
    tab_data = {}

    for line in lines:
        string_name, frets = parse_tab_line(line)
        if string_name:
            # Normalize to string number
            if string_name.lower() == 'e' and string_name == 'e':
                tab_data[1] = frets  # high e
            elif string_name.upper() == 'B':
                tab_data[2] = frets
            elif string_name.upper() == 'G':
                tab_data[3] = frets
            elif string_name.upper() == 'D':
                tab_data[4] = frets
            elif string_name.upper() == 'A':
                tab_data[5] = frets
            elif string_name.upper() == 'E' and string_name == 'E':
                tab_data[6] = frets  # low E

    if not tab_data:
        return []

    # Find max length
    max_len = max(len(frets) for frets in tab_data.values())

    # Build beats (each column is a potential beat)
    beats = []
    i = 0
    while i < max_len:
        beat = {}
        has_note = False

        for string_num in range(1, 7):
            if string_num in tab_data:
                frets = tab_data[string_num]
                if i < len(frets) and frets[i] != '-':
                    try:
                        beat[string_num] = int(frets[i])
                        has_note = True
                    except ValueError:
                        pass

        if has_note:
            beats.append(beat)
        i += 1

    return beats


def create_gp5_file(beats: list,
                    title: str = "Generated Riff",
                    tempo: int = 120,
                    tuning: str = 'standard',
                    output_path: str = None) -> str:
    """
    Create a Guitar Pro 5 file from beat data.
    Uses the default Song() structure and modifies it.
    """
    song = Song()
    song.title = title
    song.tempo = tempo
    song.artist = "Guitar Model Lab"

    # Use the default track (don't clear it)
    track = song.tracks[0]
    track.name = "Electric Guitar"
    track.channel.instrument = 25  # Steel Guitar

    # Set tuning
    tuning_midi = TUNING_MIDI.get(tuning, TUNING_MIDI['standard'])
    for i, midi_val in enumerate(tuning_midi):
        track.strings[i].value = midi_val

    # Calculate measures needed (4 beats per measure in 4/4)
    beats_per_measure = 4
    num_measures = max(1, (len(beats) + beats_per_measure - 1) // beats_per_measure)

    # Add additional measure headers if needed (default has 1)
    while len(song.measureHeaders) < num_measures:
        header = MeasureHeader()
        header.number = len(song.measureHeaders) + 1
        song.measureHeaders.append(header)

        # Also add corresponding measure to track
        measure = Measure(track, header)
        voice = Voice(measure)
        measure.voices.append(voice)
        track.measures.append(measure)

    # Now fill in the beats
    beat_idx = 0
    for measure_num in range(num_measures):
        measure = track.measures[measure_num]
        voice = measure.voices[0]  # Use first voice

        # Clear default beats in this voice
        voice.beats.clear()

        # Add beats to this measure
        for _ in range(beats_per_measure):
            beat = Beat(voice)
            beat.duration = Duration()
            beat.duration.value = 4  # Quarter note

            if beat_idx < len(beats):
                beat_data = beats[beat_idx]
                for string_num, fret in beat_data.items():
                    note = Note(beat)
                    note.string = string_num
                    note.value = fret
                    note.velocity = 95
                    note.type = NoteType.normal
                    beat.notes.append(note)
                beat_idx += 1
            else:
                # Rest beat
                beat.status = guitarpro.BeatStatus.rest

            voice.beats.append(beat)

    # Determine output path
    if output_path is None:
        output_path = f"{title.replace(' ', '_')}.gp5"

    guitarpro.write(song, output_path)
    return output_path


def tab_to_gp5(tab_text: str,
               title: str = "Generated Riff",
               tempo: int = 120,
               tuning: str = 'standard',
               output_path: str = None) -> str:
    """
    Convert ASCII tab text to Guitar Pro 5 file.

    Args:
        tab_text: ASCII tablature string
        title: Song title
        tempo: BPM
        tuning: One of 'standard', 'drop_d', 'drop_c', 'half_step_down'
        output_path: Output file path (default: {title}.gp5)

    Returns:
        Path to created .gp5 file
    """
    beats = parse_ascii_tab(tab_text)
    if not beats:
        raise ValueError("No valid tab data found in input")

    return create_gp5_file(beats, title, tempo, tuning, output_path)


def main():
    parser = argparse.ArgumentParser(description='Convert ASCII tab to Guitar Pro 5')
    parser.add_argument('input', nargs='?', help='Input file or - for stdin')
    parser.add_argument('-o', '--output', help='Output .gp5 file path')
    parser.add_argument('-t', '--title', default='Generated Riff', help='Song title')
    parser.add_argument('--tempo', type=int, default=120, help='Tempo (BPM)')
    parser.add_argument('--tuning', choices=['standard', 'drop_d', 'drop_c', 'half_step_down'],
                        default='standard', help='Guitar tuning')

    args = parser.parse_args()

    # Read input
    if args.input == '-' or args.input is None:
        tab_text = sys.stdin.read()
    else:
        with open(args.input) as f:
            tab_text = f.read()

    try:
        output_file = tab_to_gp5(
            tab_text,
            title=args.title,
            tempo=args.tempo,
            tuning=args.tuning,
            output_path=args.output
        )
        print(f"Created: {output_file}")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
