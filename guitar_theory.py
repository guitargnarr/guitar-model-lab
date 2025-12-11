#!/usr/bin/env python3
"""
Guitar Theory Module - Deterministic music theory for tab generation.

Extracted from FretVision.jsx logic. This is the single source of truth
for scale definitions, note mappings, and fret calculations.

Usage:
    from guitar_theory import GuitarTheory

    gt = GuitarTheory()
    positions = gt.get_scale_positions('E', 'phrygian')
    tab = gt.generate_pattern('E', 'phrygian', 'ascending', bars=4)
"""

from typing import List, Dict, Tuple, Optional
import random

# Chromatic scale - same as FretVision.jsx
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Scale intervals - same as FretVision.jsx
SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "blues": [0, 3, 5, 6, 7, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "locrian": [0, 1, 3, 5, 6, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
}

# Tunings - open strings from low to high (6th string to 1st)
TUNINGS = {
    "standard": ['E', 'A', 'D', 'G', 'B', 'E'],
    "drop_d": ['D', 'A', 'D', 'G', 'B', 'E'],
    "drop_c": ['C', 'G', 'C', 'F', 'A', 'D'],
    "half_step_down": ['D#', 'G#', 'C#', 'F#', 'A#', 'D#'],
}

# Common chord progressions by style
CHORD_PROGRESSIONS = {
    "blues_12bar": [1, 1, 1, 1, 4, 4, 1, 1, 5, 4, 1, 5],  # I-I-I-I-IV-IV-I-I-V-IV-I-V
    "pop_4chord": [1, 5, 6, 4],  # I-V-vi-IV (most popular progression)
    "rock_power": [1, 4, 5, 5],  # I-IV-V-V
    "jazz_251": [2, 5, 1],  # ii-V-I
    "metal_riff": [1, 'b7', 'b6', 5],  # i-bVII-bVI-V (Phrygian-based)
    "sad_progression": [6, 4, 1, 5],  # vi-IV-I-V (Axis progression from minor)
    "andalusian": ['b7', 'b6', 5, 1],  # bVII-bVI-V-i (Flamenco cadence)
}

# Chord qualities for each scale degree in major/minor
MAJOR_CHORD_QUALITIES = {
    1: 'maj', 2: 'min', 3: 'min', 4: 'maj', 5: 'maj', 6: 'min', 7: 'dim'
}
MINOR_CHORD_QUALITIES = {
    1: 'min', 2: 'dim', 3: 'maj', 4: 'min', 5: 'min', 6: 'maj', 7: 'maj'
}

# Chord intervals from root
CHORD_INTERVALS = {
    'maj': [0, 4, 7],        # Major triad
    'min': [0, 3, 7],        # Minor triad
    'dim': [0, 3, 6],        # Diminished triad
    'aug': [0, 4, 8],        # Augmented triad
    'maj7': [0, 4, 7, 11],   # Major 7th
    'min7': [0, 3, 7, 10],   # Minor 7th
    'dom7': [0, 4, 7, 10],   # Dominant 7th
    '5': [0, 7],             # Power chord
}

# MIDI note numbers for standard tuning open strings
MIDI_BASE = {
    "standard": [40, 45, 50, 55, 59, 64],  # E2, A2, D3, G3, B3, E4
    "drop_d": [38, 45, 50, 55, 59, 64],
    "drop_c": [36, 43, 48, 53, 57, 62],
    "half_step_down": [39, 44, 49, 54, 58, 63],
}


class GuitarTheory:
    """Core guitar theory calculations."""

    def __init__(self, tuning: str = "standard", max_fret: int = 24):
        self.tuning = tuning
        self.open_strings = TUNINGS[tuning]
        self.midi_base = MIDI_BASE[tuning]
        self.max_fret = max_fret

    def get_note_at_fret(self, string: int, fret: int) -> str:
        """Get note name at a specific string/fret position.

        Args:
            string: 0-5 (0 = low E, 5 = high e in standard)
            fret: 0-24
        """
        open_note = self.open_strings[string]
        open_index = NOTE_NAMES.index(open_note)
        note_index = (open_index + fret) % 12
        return NOTE_NAMES[note_index]

    def get_midi_note(self, string: int, fret: int) -> int:
        """Get MIDI note number for a string/fret position."""
        return self.midi_base[string] + fret

    def get_scale_notes(self, root: str, scale: str) -> List[str]:
        """Get all note names in a scale.

        Args:
            root: Root note (e.g., 'E', 'A', 'C#')
            scale: Scale name (e.g., 'phrygian', 'minor')
        """
        root_index = NOTE_NAMES.index(root)
        intervals = SCALES[scale]
        return [NOTE_NAMES[(root_index + i) % 12] for i in intervals]

    def get_scale_positions(self, root: str, scale: str,
                           min_fret: int = 0, max_fret: int = 12) -> List[Dict]:
        """Get all valid fret positions for a scale.

        Returns list of {string, fret, note, midi} dicts.
        """
        scale_notes = self.get_scale_notes(root, scale)
        positions = []

        for string in range(6):
            for fret in range(min_fret, max_fret + 1):
                note = self.get_note_at_fret(string, fret)
                if note in scale_notes:
                    positions.append({
                        'string': string,
                        'fret': fret,
                        'note': note,
                        'midi': self.get_midi_note(string, fret),
                        'is_root': note == root
                    })

        return positions

    def get_box_position(self, root: str, scale: str, position: int = 1) -> List[Dict]:
        """Get scale notes in a playable box position (4-fret hand span).

        Box positions are the standard way guitarists learn scales.
        Each position covers all scale notes within a 4-5 fret span.

        Args:
            root: Root note
            scale: Scale type
            position: Position number (1-5 for most scales)

        Returns:
            List of {string, fret, note, midi, finger} dicts organized by string
        """
        scale_notes = self.get_scale_notes(root, scale)
        root_index = NOTE_NAMES.index(root)

        # Find root note positions on low E string
        root_frets_low_e = []
        for fret in range(self.max_fret):
            if self.get_note_at_fret(0, fret) == root:
                root_frets_low_e.append(fret)

        # Position 1 starts at/near first root on low E (or open if root is E)
        # Position 2 starts ~3-4 frets higher, etc.
        if position <= len(root_frets_low_e):
            base_fret = root_frets_low_e[position - 1]
        else:
            base_fret = root_frets_low_e[0] + (position - 1) * 3

        # Allow some flexibility before base fret for open strings or reach-back
        min_fret = max(0, base_fret - 1)
        max_fret = base_fret + 4  # 4-fret span

        # Get all scale notes in this range, organized by string
        box_notes = []
        for string in range(6):
            string_notes = []
            for fret in range(min_fret, max_fret + 1):
                note = self.get_note_at_fret(string, fret)
                if note in scale_notes:
                    # Assign finger based on fret distance from base
                    fret_offset = fret - base_fret
                    if fret_offset <= 0:
                        finger = 1  # Index
                    elif fret_offset == 1:
                        finger = 1
                    elif fret_offset == 2:
                        finger = 2  # Middle
                    elif fret_offset == 3:
                        finger = 3  # Ring
                    else:
                        finger = 4  # Pinky

                    string_notes.append({
                        'string': string,
                        'fret': fret,
                        'note': note,
                        'midi': self.get_midi_note(string, fret),
                        'is_root': note == root,
                        'finger': finger
                    })
            box_notes.extend(string_notes)

        return box_notes

    def get_3nps_position(self, root: str, scale: str, position: int = 1) -> List[Dict]:
        """Get 3-notes-per-string scale pattern.

        The 3NPS system is popular for fast playing and consistent fingering.
        Each string has exactly 3 notes, creating uniform patterns.

        Args:
            root: Root note
            scale: Scale type (must be 7-note scale)
            position: Starting position (1-7)
        """
        scale_notes = self.get_scale_notes(root, scale)
        if len(scale_notes) != 7:
            raise ValueError("3NPS requires a 7-note scale")

        # Find starting fret based on position
        root_index = NOTE_NAMES.index(root)
        root_fret_low_e = 0
        for fret in range(self.max_fret):
            if self.get_note_at_fret(0, fret) == root:
                root_fret_low_e = fret
                break

        # Rotate scale to start from position
        rotated_scale = scale_notes[position - 1:] + scale_notes[:position - 1]

        notes = []
        current_scale_idx = 0

        for string in range(6):
            # Find 3 consecutive scale notes on this string
            string_notes = []
            # Start searching from a reasonable fret
            search_start = root_fret_low_e + (string * 2) - 2 if string > 0 else root_fret_low_e
            search_start = max(0, search_start)

            for fret in range(search_start, search_start + 8):
                note = self.get_note_at_fret(string, fret)
                target_note = rotated_scale[current_scale_idx % 7]

                if note == target_note:
                    finger = len(string_notes) + 1  # 1, 2, 3 or 1, 2, 4
                    if len(string_notes) == 2:
                        finger = 4  # Pinky for third note

                    string_notes.append({
                        'string': string,
                        'fret': fret,
                        'note': note,
                        'midi': self.get_midi_note(string, fret),
                        'is_root': note == root,
                        'finger': finger
                    })
                    current_scale_idx += 1

                    if len(string_notes) == 3:
                        break

            notes.extend(string_notes)

        return notes

    def get_position_box(self, root: str, scale: str,
                        start_fret: int, span: int = 4) -> List[Dict]:
        """Get scale positions within a fret box (typical hand position).

        Args:
            start_fret: Lowest fret in the box
            span: Number of frets the hand can reach (typically 4-5)
        """
        return self.get_scale_positions(root, scale, start_fret, start_fret + span)

    def get_chord_notes(self, root: str, quality: str = 'maj') -> List[str]:
        """Get note names for a chord.

        Args:
            root: Root note of chord
            quality: Chord quality (maj, min, dim, aug, maj7, min7, dom7, 5)
        """
        root_index = NOTE_NAMES.index(root)
        intervals = CHORD_INTERVALS.get(quality, CHORD_INTERVALS['maj'])
        return [NOTE_NAMES[(root_index + i) % 12] for i in intervals]

    def get_chord_voicing(self, root: str, quality: str = 'maj',
                         position: int = 1) -> List[Dict]:
        """Get a playable chord voicing within a box position.

        Returns list of {string, fret, note, midi} for each string to play.
        """
        chord_notes = self.get_chord_notes(root, quality)

        # Find root on low E string near position
        root_fret = 0
        for fret in range(self.max_fret):
            if self.get_note_at_fret(0, fret) == root:
                if position == 1 or fret >= (position - 1) * 3:
                    root_fret = fret
                    break

        # Build voicing from bass up
        voicing = []
        for string in range(6):
            # Find closest chord tone on this string
            best_fret = None
            best_note = None
            for fret in range(max(0, root_fret - 2), root_fret + 5):
                note = self.get_note_at_fret(string, fret)
                if note in chord_notes:
                    if best_fret is None or abs(fret - root_fret) < abs(best_fret - root_fret):
                        best_fret = fret
                        best_note = note

            if best_fret is not None:
                voicing.append({
                    'string': string,
                    'fret': best_fret,
                    'note': best_note,
                    'midi': self.get_midi_note(string, best_fret)
                })

        return voicing

    def get_progression_chords(self, root: str, scale: str,
                               progression_name: str) -> List[Dict]:
        """Get chord roots and qualities for a progression.

        Args:
            root: Key root (e.g., 'E')
            scale: Scale type (determines chord qualities)
            progression_name: Name from CHORD_PROGRESSIONS

        Returns:
            List of {root, quality, degree} dicts
        """
        if progression_name not in CHORD_PROGRESSIONS:
            raise ValueError(f"Unknown progression: {progression_name}")

        progression = CHORD_PROGRESSIONS[progression_name]
        scale_notes = self.get_scale_notes(root, scale)
        root_index = NOTE_NAMES.index(root)

        # Determine if major or minor key
        is_minor = scale in ['minor', 'phrygian', 'dorian', 'locrian',
                            'harmonic_minor', 'melodic_minor']
        qualities = MINOR_CHORD_QUALITIES if is_minor else MAJOR_CHORD_QUALITIES

        chords = []
        for degree in progression:
            if isinstance(degree, str) and degree.startswith('b'):
                # Flat degree (e.g., 'b7' = flat 7th)
                deg_num = int(degree[1:])
                chord_root_idx = (root_index + (deg_num - 1) * 2 - 1) % 12
                quality = 'maj'  # Flat degrees are usually major
            else:
                deg_num = int(degree)
                chord_root_idx = NOTE_NAMES.index(scale_notes[deg_num - 1])
                quality = qualities.get(deg_num, 'maj')

            chords.append({
                'root': NOTE_NAMES[chord_root_idx],
                'quality': quality,
                'degree': degree
            })

        return chords


class TabGenerator:
    """Generate playable tabs using music theory."""

    def __init__(self, theory: Optional[GuitarTheory] = None):
        self.theory = theory or GuitarTheory()

    def generate_ascending_run(self, root: str, scale: str,
                               position: int = 1, bars: int = 1) -> List[List[Dict]]:
        """Generate an ascending scale run within a box position.

        Plays string-by-string from low to high, staying in position.
        This is how guitarists actually play ascending scales.
        """
        box_notes = self.theory.get_box_position(root, scale, position)

        # Group by string, then sort each string's notes by fret
        by_string = {}
        for note in box_notes:
            by_string.setdefault(note['string'], []).append(note)

        for string in by_string:
            by_string[string].sort(key=lambda n: n['fret'])

        # Build ascending pattern: low E to high e, low fret to high
        ascending = []
        for string in range(6):  # 0=low E to 5=high e
            if string in by_string:
                ascending.extend(by_string[string])

        # Take enough notes for the requested bars (4 notes per bar)
        notes_needed = bars * 4
        selected = ascending[:notes_needed]

        return [[pos] for pos in selected]

    def generate_descending_run(self, root: str, scale: str,
                                position: int = 1, bars: int = 1) -> List[List[Dict]]:
        """Generate a descending scale run within a box position."""
        box_notes = self.theory.get_box_position(root, scale, position)

        # Group by string
        by_string = {}
        for note in box_notes:
            by_string.setdefault(note['string'], []).append(note)

        for string in by_string:
            by_string[string].sort(key=lambda n: n['fret'], reverse=True)

        # Build descending pattern: high e to low E, high fret to low
        descending = []
        for string in range(5, -1, -1):  # 5=high e down to 0=low E
            if string in by_string:
                descending.extend(by_string[string])

        notes_needed = bars * 4
        selected = descending[:notes_needed]

        return [[pos] for pos in selected]

    def generate_pedal_tone(self, root: str, scale: str,
                           position: int = 1, bars: int = 1) -> List[List[Dict]]:
        """Generate a pedal tone pattern (alternating root with scale notes).

        Uses box position for realistic fingering.
        """
        box_notes = self.theory.get_box_position(root, scale, position)

        # Find root note on lowest string available
        root_notes = [n for n in box_notes if n['is_root']]
        root_notes.sort(key=lambda n: n['string'])  # Prefer lower strings for pedal
        pedal = root_notes[0] if root_notes else box_notes[0]

        # Get melody notes on higher strings within the box
        melody_notes = [n for n in box_notes if n['string'] > pedal['string']]
        melody_notes.sort(key=lambda n: (n['string'], n['fret']))

        if not melody_notes:
            melody_notes = [n for n in box_notes if n != pedal]

        columns = []
        notes_needed = bars * 4

        for i in range(notes_needed):
            if i % 2 == 0:
                columns.append([pedal])
            else:
                melody_idx = (i // 2) % len(melody_notes)
                columns.append([melody_notes[melody_idx]])

        return columns

    def generate_arpeggio(self, root: str, scale: str,
                         position: int = 1, bars: int = 1) -> List[List[Dict]]:
        """Generate an arpeggio pattern (1-3-5 of the scale) within box position."""
        box_notes = self.theory.get_box_position(root, scale, position)
        scale_notes = self.theory.get_scale_notes(root, scale)

        # Get 1st, 3rd, 5th degrees
        arpeggio_degrees = [scale_notes[0], scale_notes[2], scale_notes[4]]

        # Filter to arpeggio notes within box
        arp_notes = [n for n in box_notes if n['note'] in arpeggio_degrees]

        # Sort by string then fret for playable sweep pattern
        arp_notes.sort(key=lambda n: (n['string'], n['fret']))

        columns = []
        notes_needed = bars * 4

        for i in range(notes_needed):
            idx = i % len(arp_notes)
            columns.append([arp_notes[idx]])

        return columns

    def generate_random_pattern(self, root: str, scale: str,
                                position: int = 1, bars: int = 1) -> List[List[Dict]]:
        """Generate a random but playable pattern within a box position."""
        box_notes = self.theory.get_box_position(root, scale, position)

        if not box_notes:
            box_notes = self.theory.get_scale_positions(root, scale, 0, 5)

        columns = []
        notes_needed = bars * 4

        # Group by string for playability
        by_string = {}
        for p in box_notes:
            by_string.setdefault(p['string'], []).append(p)

        prev_string = None
        for _ in range(notes_needed):
            # Prefer adjacent strings for playability
            available_strings = list(by_string.keys())
            if prev_string is not None:
                # Weight towards nearby strings (max 2 string jump)
                weights = []
                for s in available_strings:
                    distance = abs(s - prev_string)
                    if distance <= 2:
                        weights.append(1 / (distance + 1))
                    else:
                        weights.append(0.1)  # Penalize big jumps
            else:
                weights = [1] * len(available_strings)

            total = sum(weights)
            weights = [w / total for w in weights]

            chosen_string = random.choices(available_strings, weights=weights)[0]
            chosen_note = random.choice(by_string[chosen_string])
            columns.append([chosen_note])
            prev_string = chosen_string

        return columns

    def generate_3nps_run(self, root: str, scale: str,
                          position: int = 1, bars: int = 1,
                          ascending: bool = True) -> List[List[Dict]]:
        """Generate a 3-notes-per-string scale run.

        Great for fast alternate picking and legato runs.
        """
        notes = self.theory.get_3nps_position(root, scale, position)

        if not ascending:
            notes = list(reversed(notes))

        notes_needed = bars * 4
        selected = notes[:notes_needed]

        return [[pos] for pos in selected]

    def generate_chord_progression(self, root: str, scale: str,
                                   progression: str = 'blues_12bar',
                                   position: int = 1,
                                   chord_type: str = '5') -> List[List[Dict]]:
        """Generate a chord progression as tab.

        Args:
            root: Key root
            scale: Scale type (for chord qualities)
            progression: Progression name from CHORD_PROGRESSIONS
            position: Box position
            chord_type: '5' for power chords, 'maj'/'min' for full chords

        Returns:
            List of columns, each containing chord voicing notes
        """
        chords = self.theory.get_progression_chords(root, scale, progression)
        columns = []

        for chord in chords:
            if chord_type == '5':
                # Power chord - root and 5th only
                voicing = self.theory.get_chord_voicing(
                    chord['root'], '5', position
                )
                # Keep only bottom 2-3 strings for power chord feel
                voicing = [n for n in voicing if n['string'] <= 2]
            else:
                # Use chord quality from progression
                voicing = self.theory.get_chord_voicing(
                    chord['root'], chord['quality'], position
                )

            if voicing:
                columns.append(voicing)

        return columns

    def generate_power_chord_riff(self, root: str, scale: str,
                                  position: int = 1, bars: int = 2) -> List[List[Dict]]:
        """Generate a power chord based riff.

        Uses common metal/rock patterns with power chords.
        """
        # Get power chord voicings for common riff notes
        scale_notes = self.theory.get_scale_notes(root, scale)
        root_idx = NOTE_NAMES.index(root)

        # Common power chord riff: root, b7 (or 5th), root octave, 4th
        riff_degrees = [0, 10, 0, 5]  # Semitones from root

        columns = []
        notes_needed = bars * 4

        for i in range(notes_needed):
            degree_semitones = riff_degrees[i % len(riff_degrees)]
            chord_root = NOTE_NAMES[(root_idx + degree_semitones) % 12]
            voicing = self.theory.get_chord_voicing(chord_root, '5', position)
            # Keep bottom strings only for heavy sound
            voicing = [n for n in voicing if n['string'] <= 2]
            if voicing:
                columns.append(voicing)

        return columns

    def columns_to_tab(self, columns: List[List[Dict]],
                       notes_per_measure: int = 4) -> List[str]:
        """Convert column data to ASCII tab format.

        Returns 6 strings (high e to low E).
        """
        string_names = ['e', 'B', 'G', 'D', 'A', 'E']
        tab_lines = [''] * 6

        for col_idx, column in enumerate(columns):
            # Add bar line every measure
            if col_idx > 0 and col_idx % notes_per_measure == 0:
                for i in range(6):
                    tab_lines[i] += '-|--'

            # Find what's played on each string
            frets = {}
            for note in column:
                string = note['string']
                frets[string] = note['fret']

            # Build column - consistent 4 char width per note
            for i in range(6):
                display_string = 5 - i  # Reverse for display (high e first)
                if display_string in frets:
                    fret = frets[display_string]
                    if fret >= 10:
                        tab_lines[i] += f'-{fret}-'
                    else:
                        tab_lines[i] += f'--{fret}-'
                else:
                    tab_lines[i] += '----'

        # Add final bar line
        for i in range(6):
            tab_lines[i] += '-|'

        # Format with string names
        return [f'{string_names[i]}|{tab_lines[i]}' for i in range(6)]


def generate_tab(root: str = 'E', scale: str = 'phrygian',
                 pattern: str = 'ascending', bars: int = 4,
                 position: int = 1, tuning: str = 'standard',
                 progression: str = None) -> str:
    """High-level function to generate a complete tab.

    Args:
        root: Root note
        scale: Scale type
        pattern: 'ascending', 'descending', 'pedal', 'arpeggio', 'random', '3nps',
                 'power_chords', 'progression'
        bars: Number of measures
        position: Box position (1-5) - determines fret range
        tuning: Guitar tuning ('standard', 'drop_d', 'drop_c', 'half_step_down')
        progression: Progression name for 'progression' pattern

    Returns:
        ASCII tab string
    """
    theory = GuitarTheory(tuning=tuning)
    gen = TabGenerator(theory)

    if pattern == 'ascending':
        columns = gen.generate_ascending_run(root, scale, position, bars)
    elif pattern == 'descending':
        columns = gen.generate_descending_run(root, scale, position, bars)
    elif pattern == 'pedal':
        columns = gen.generate_pedal_tone(root, scale, position, bars)
    elif pattern == 'arpeggio':
        columns = gen.generate_arpeggio(root, scale, position, bars)
    elif pattern == 'random':
        columns = gen.generate_random_pattern(root, scale, position, bars)
    elif pattern == '3nps':
        columns = gen.generate_3nps_run(root, scale, position, bars, ascending=True)
    elif pattern == 'power_chords':
        columns = gen.generate_power_chord_riff(root, scale, position, bars)
    elif pattern == 'progression':
        prog_name = progression or 'blues_12bar'
        columns = gen.generate_chord_progression(root, scale, prog_name, position)
    else:
        raise ValueError(f"Unknown pattern: {pattern}")

    tab_lines = gen.columns_to_tab(columns)
    return '\n'.join(tab_lines)


if __name__ == '__main__':
    # Demo
    print("E Phrygian Scale Notes:")
    gt = GuitarTheory()
    print(gt.get_scale_notes('E', 'phrygian'))

    print("\n--- Ascending Run (2 bars) ---")
    print(generate_tab('E', 'phrygian', 'ascending', bars=2))

    print("\n--- Descending Run (2 bars) ---")
    print(generate_tab('E', 'phrygian', 'descending', bars=2))

    print("\n--- Pedal Tone (2 bars) ---")
    print(generate_tab('E', 'phrygian', 'pedal', bars=2))

    print("\n--- Arpeggio (2 bars) ---")
    print(generate_tab('E', 'phrygian', 'arpeggio', bars=2))

    print("\n--- Random Pattern (2 bars) ---")
    print(generate_tab('E', 'phrygian', 'random', bars=2))
