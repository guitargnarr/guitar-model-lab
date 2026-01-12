#!/usr/bin/env python3
"""
Generate lead patterns for Red Thread over Fracture Pulse V19
Based on scale exercises mapped to E Phrygian / E Harmonic Minor
"""

import guitarpro
from datetime import datetime

# E Phrygian scale positions (frets on high strings)
E_PHRYGIAN = {
    'string_1': [0, 1, 3, 5, 7, 8, 10, 12],  # E F G A B C D E
    'string_2': [0, 1, 3, 5, 6, 8, 10, 12],  # B C D E F G A B
    'string_3': [0, 2, 4, 5, 7, 9, 10, 12],  # G A B C D E F G
}

# E Harmonic Minor - the D# difference
E_HARMONIC_MINOR = {
    'string_1': [0, 1, 3, 5, 7, 8, 11, 12],  # E F G A B C D# E
    'string_2': [0, 1, 3, 5, 6, 8, 11, 12],  # B C D# E F G A B  
    'string_3': [0, 2, 4, 5, 7, 9, 11, 12],  # G A B C D# E F G
}

def create_lead_pattern():
    """Create lead track for Red Thread over V19"""
    song = guitarpro.models.Song()
    song.title = "Red Thread Lead - Exercise Derived"
    song.artist = "FretVision Study"
    song.tempo = 102  # Match V19
    
    # Create lead guitar track
    track = guitarpro.models.Track(song)
    track.name = "Lead (Phrygian/HMin)"
    track.channel.instrument = 30  # Distortion Guitar
    track.channel.volume = 100
    track.channel.balance = 64  # Center pan
    
    # Standard tuning
    track.strings = [
        guitarpro.models.GuitarString(1, 64),  # E4
        guitarpro.models.GuitarString(2, 59),  # B3
        guitarpro.models.GuitarString(3, 55),  # G3
        guitarpro.models.GuitarString(4, 50),  # D3
        guitarpro.models.GuitarString(5, 45),  # A2
        guitarpro.models.GuitarString(6, 40),  # E2
    ]
    
    # Create 8-bar lead phrase patterns
    patterns = [
        # Pattern 1: Ascending Phrygian run (bars 1-2)
        [(1, 0), (1, 1), (1, 3), (1, 5), (1, 7), (1, 8), (1, 10), (1, 12)],
        [(2, 12), (2, 10), (2, 8), (2, 6), (2, 5), (2, 3), (2, 1), (2, 0)],
        
        # Pattern 2: Harmonic minor tension (bars 3-4) - note the D# (fret 11)
        [(1, 7), (1, 8), (1, 11), (1, 12), (2, 10), (2, 8), (2, 6), (2, 5)],
        [(3, 9), (3, 11), (3, 12), (2, 8), (2, 6), (2, 5), (2, 3), (2, 1)],
        
        # Pattern 3: Melodic phrase (bars 5-6)
        [(1, 12), (1, 10), (1, 8), (1, 7), (2, 10), (2, 8), (2, 6), (2, 5)],
        [(2, 5), (2, 6), (2, 8), (2, 10), (1, 7), (1, 8), (1, 10), (1, 12)],
        
        # Pattern 4: Resolution (bars 7-8)
        [(1, 8), (1, 7), (1, 5), (1, 3), (1, 1), (1, 0), (-1, -1), (-1, -1)],
        [(2, 0), (-1, -1), (-1, -1), (-1, -1), (-1, -1), (-1, -1), (-1, -1), (-1, -1)],
    ]
    
    for bar_idx, pattern in enumerate(patterns):
        measure = guitarpro.models.Measure(track.measures[0].header if track.measures else None)
        
        # Create measure header if needed
        if not song.measureHeaders:
            header = guitarpro.models.MeasureHeader()
            header.timeSignature.numerator = 4
            header.timeSignature.denominator.value = 4
            header.tempo.value = 102
            song.measureHeaders.append(header)
        elif bar_idx >= len(song.measureHeaders):
            header = guitarpro.models.MeasureHeader()
            header.timeSignature.numerator = 4
            header.timeSignature.denominator.value = 4
            header.tempo.value = 102
            song.measureHeaders.append(header)
        
        measure.header = song.measureHeaders[bar_idx]
        
        # Add notes (8 eighth notes per bar)
        for note_data in pattern:
            string, fret = note_data
            
            beat = guitarpro.models.Beat(measure.voices[0] if measure.voices else None)
            beat.duration.value = 8  # Eighth note
            
            if string > 0 and fret >= 0:
                note = guitarpro.models.Note(beat)
                note.string = string
                note.value = fret
                note.velocity = 95
                beat.notes.append(note)
            
            if not measure.voices:
                voice = guitarpro.models.Voice(measure)
                measure.voices.append(voice)
            measure.voices[0].beats.append(beat)
        
        track.measures.append(measure)
    
    song.tracks.append(track)
    return song

# Generate the file
song = create_lead_pattern()
output_path = "/Users/matthewscott/Desktop/LLM Music/red_thread_lead_exercises.gp5"
guitarpro.write(song, output_path)
print(f"Generated: {output_path}")
print(f"Tempo: 102 BPM (matches V19)")
print(f"Bars: 8 (repeatable phrase)")
print(f"Scales: E Phrygian + E Harmonic Minor (D# tension notes)")
