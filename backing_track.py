#!/usr/bin/env python3
"""
Neural Backing Track Generator

Pipeline:
1. Generate power chord progression in a key
2. Create Guitar Pro file with the progression
3. Render MIDI to audio using synthesized guitar
4. Process through NeuralDSP VST3 plugin for authentic tone

Requirements:
- pyguitarpro: GP file generation
- pedalboard: VST3 plugin hosting
- midiutil: MIDI generation
- soundfile: Audio I/O
- numpy: Audio processing
"""

import json
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from midiutil import MIDIFile

# Try importing optional dependencies
try:
    import guitarpro
    HAS_GUITARPRO = True
except ImportError:
    HAS_GUITARPRO = False
    print("Warning: pyguitarpro not available, GP export disabled")

try:
    from pedalboard import Pedalboard, load_plugin  # noqa: F401
    from pedalboard.io import AudioFile  # noqa: F401
    HAS_PEDALBOARD = True
except ImportError:
    HAS_PEDALBOARD = False
    print("Warning: pedalboard not available, VST processing disabled")


# Musical constants
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Power chord intervals (root + fifth + octave)
POWER_CHORD_INTERVALS = [0, 7, 12]

# Common chord progressions by style (scale degrees)
PROGRESSIONS = {
    'rock': [1, 4, 5, 1],           # I-IV-V-I
    'blues': [1, 1, 4, 4, 1, 1, 5, 4, 1, 5],  # 12-bar blues (simplified)
    'metal': [1, 6, 4, 5],          # i-VI-iv-v (minor)
    'punk': [1, 5, 6, 4],           # I-V-vi-IV
    'grunge': [1, 4, 1, 5],         # I-IV-I-V
    'djent': [1, 2, 6, 5],          # Chromatic movement
}

# Rhythm patterns for variety (master_guitar_instructor recommendation)
RHYTHM_PATTERNS = {
    'straight': [1, 1, 1, 1, 1, 1, 1, 1],
    'syncopated': [1.5, 0.5, 1, 1, 1.5, 0.5, 1, 1],
    'triplet': [0.67, 0.67, 0.66, 0.67, 0.67, 0.66, 0.67, 0.67, 0.66],
    'gallop': [0.5, 0.5, 1, 0.5, 0.5, 1, 0.5, 0.5, 1, 0.5, 0.5, 1],
    'staccato': [0.3, 0.7, 0.3, 0.7, 0.3, 0.7, 0.3, 0.7],
    'tremolo': [0.25, 0.25, 0.25, 0.25] * 8,
}

# Accent patterns for dynamics (master_guitar_instructor recommendation)
ACCENT_PATTERNS = {
    'none': [1.0] * 8,
    'downbeat': [1.2, 0.8, 1.0, 0.8, 1.2, 0.8, 1.0, 0.8],
    'backbeat': [0.8, 1.2, 0.8, 1.2, 0.8, 1.2, 0.8, 1.2],
    'buildup': [0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3],
}

# NeuralDSP preset paths
NEURAL_PRESETS_BASE = Path.home() / "Library/Audio/Presets/Neural DSP"
NEURAL_VST3_PATH = Path("/Library/Audio/Plug-Ins/VST3")

# Available NeuralDSP plugins
NEURAL_PLUGINS = {
    'gojira': 'Archetype Gojira.vst3',
    'gojira_x': 'Archetype Gojira X.vst3',
    'plini': 'ArchetypePlini.vst3',
    'plini_x': 'Archetype Plini X.vst3',
    'nolly': 'Archetype Nolly.vst3',
    'petrucci': 'Archetype Petrucci.vst3',
    'petrucci_x': 'Archetype Petrucci X.vst3',
    'misha_x': 'Archetype Misha Mansoor X.vst3',
}


@dataclass
class ChordEvent:
    """Represents a chord in the progression"""
    root_note: int  # MIDI note number
    duration: float  # In beats
    velocity: int = 100


@dataclass
class BackingTrackConfig:
    """Configuration for backing track generation"""
    key: str = 'E'
    octave: int = 2
    style: str = 'metal'
    bpm: int = 120
    bars: int = 4
    beats_per_bar: int = 4
    plugin: str = 'gojira'
    preset_name: Optional[str] = None
    # Model recommendations
    rhythm_pattern: str = 'straight'
    accent_pattern: str = 'downbeat'
    articulation: str = 'palm_mute'
    modulation: str = 'none'
    attack_style: str = 'aggressive'
    # Bass track options
    include_bass: bool = False
    bass_octave: int = 1
    bass_style: str = 'root'
    bass_volume: float = 0.7


def note_to_midi(note: str, octave: int) -> int:
    """Convert note name to MIDI number"""
    note_upper = note.upper()
    # Handle flat notes (Bb -> A#, Db -> C#, etc.) but NOT the note B itself
    if note_upper == 'BB':
        note_upper = 'A#'
    elif note_upper == 'DB':
        note_upper = 'C#'
    elif note_upper == 'EB':
        note_upper = 'D#'
    elif note_upper == 'GB':
        note_upper = 'F#'
    elif note_upper == 'AB':
        note_upper = 'G#'
    note_idx = NOTES.index(note_upper)
    return (octave + 1) * 12 + note_idx


def get_scale_degree_note(root: str, degree: int, minor: bool = False) -> str:
    """Get note for scale degree (1-7)"""
    root_idx = NOTES.index(root)

    # Major scale intervals
    major_intervals = [0, 2, 4, 5, 7, 9, 11]
    # Natural minor intervals
    minor_intervals = [0, 2, 3, 5, 7, 8, 10]

    intervals = minor_intervals if minor else major_intervals
    interval = intervals[(degree - 1) % 7]

    return NOTES[(root_idx + interval) % 12]


def generate_progression(config: BackingTrackConfig) -> List[ChordEvent]:
    """Generate chord progression based on config"""
    # metal_reference uses same progression as metal
    if config.style == 'metal_reference':
        style_for_progression = 'metal'
    else:
        style_for_progression = config.style
    progression = PROGRESSIONS.get(style_for_progression, PROGRESSIONS['rock'])

    # Determine if minor key (metal typically uses minor)
    is_minor = config.style in ['metal', 'metal_reference', 'djent', 'grunge']

    events = []
    beats_per_chord = config.beats_per_bar  # One chord per bar by default

    total_beats = config.bars * config.beats_per_bar
    chord_idx = 0
    current_beat = 0

    while current_beat < total_beats:
        degree = progression[chord_idx % len(progression)]
        chord_root = get_scale_degree_note(config.key, degree, is_minor)
        midi_note = note_to_midi(chord_root, config.octave)

        events.append(ChordEvent(
            root_note=midi_note,
            duration=beats_per_chord,
            velocity=100
        ))

        current_beat += beats_per_chord
        chord_idx += 1

    return events


def create_midi_file(events: List[ChordEvent],
                     config: BackingTrackConfig, output_path: str) -> None:
    """Create MIDI file from chord events"""
    midi = MIDIFile(1)  # One track
    track = 0
    channel = 0  # Guitar channel
    time = 0  # Start at beginning

    midi.addTempo(track, 0, config.bpm)
    midi.addProgramChange(track, channel, 0, 30)  # Distortion Guitar

    for event in events:
        # Add power chord notes
        for interval in POWER_CHORD_INTERVALS:
            midi.addNote(
                track,
                channel,
                event.root_note + interval,
                time,
                event.duration,
                event.velocity
            )
        time += event.duration

    with open(output_path, 'wb') as f:
        midi.writeFile(f)

    return output_path


def create_guitar_pro_file(
        events: List[ChordEvent],
        config: BackingTrackConfig,
        output_path: str) -> None:
    """Create Guitar Pro file from chord events"""
    if not HAS_GUITARPRO:
        print("pyguitarpro not available, skipping GP export")
        return None

    song = guitarpro.models.Song()
    song.title = f"{config.key} {config.style.title()} Backing Track"
    song.tempo = config.bpm

    # Create track with song reference
    track = guitarpro.models.Track(song)
    track.name = "Rhythm Guitar"
    track.channel.instrument = 30  # Distortion Guitar
    track.isPercussionTrack = False

    # Standard tuning for 6-string (E A D G B E)
    track.strings = [
        guitarpro.models.GuitarString(1, 64),  # E4
        guitarpro.models.GuitarString(2, 59),  # B3
        guitarpro.models.GuitarString(3, 55),  # G3
        guitarpro.models.GuitarString(4, 50),  # D3
        guitarpro.models.GuitarString(5, 45),  # A2
        guitarpro.models.GuitarString(6, 40),  # E2
    ]

    # Create measure headers for the song
    for i, event in enumerate(events):
        header = guitarpro.models.MeasureHeader()
        header.number = i + 1
        # GP uses 960 ticks per quarter
        header.start = i * 960 * int(event.duration)
        header.timeSignature.numerator = config.beats_per_bar
        header.timeSignature.denominator.value = 4
        song.measureHeaders.append(header)

    # Create measures for the track
    for i, event in enumerate(events):
        header = song.measureHeaders[i]
        measure = guitarpro.models.Measure(header, track)

        # Access the first voice
        voice = measure.voices[0]

        # Create beat with power chord
        beat = guitarpro.models.Beat(voice)
        beat.duration.value = 1  # Whole note (fills the bar)

        # Calculate fret positions for power chord
        root_fret = event.root_note - 40  # E2 is fret 0 on low E

        if root_fret >= 0 and root_fret <= 24:
            # Root on low E string
            note1 = guitarpro.models.Note(beat)
            note1.string = 6
            note1.value = root_fret
            beat.notes.append(note1)

            # Fifth on A string (same fret + 2)
            note2 = guitarpro.models.Note(beat)
            note2.string = 5
            note2.value = root_fret + 2
            beat.notes.append(note2)

            # Octave on D string (same fret + 2)
            note3 = guitarpro.models.Note(beat)
            note3.string = 4
            note3.value = root_fret + 2
            beat.notes.append(note3)

        voice.beats.append(beat)
        track.measures.append(measure)

    song.tracks.append(track)

    guitarpro.write(song, output_path)
    return output_path


def karplus_strong(
        freq: float,
        duration: float,
        sample_rate: int = 44100,
        decay: float = 0.996,
        brightness: float = 0.5) -> np.ndarray:
    """
    Karplus-Strong algorithm for realistic plucked string synthesis.
    This generates rich harmonics naturally through the delay-line feedback.
    """
    n_samples = int(duration * sample_rate)

    # Delay line length determines fundamental frequency
    delay_length = int(sample_rate / freq)
    if delay_length < 2:
        delay_length = 2

    # Initialize delay line with noise (string excitation)
    # Mix of white noise and impulse for different attack characteristics
    delay_line = np.random.uniform(-1, 1, delay_length)

    # Output buffer
    output = np.zeros(n_samples)

    # Karplus-Strong with averaging filter
    for i in range(n_samples):
        # Output current sample
        output[i] = delay_line[i % delay_length]

        # Average filter (low-pass) with decay
        next_idx = (i + 1) % delay_length
        # Brightness controls blend between pure averaging and keeping high
        # frequencies
        avg = (delay_line[i % delay_length] + delay_line[next_idx]) * 0.5
        blend = brightness * delay_line[i %
                                        delay_length] + (1 - brightness) * avg
        delay_line[i % delay_length] = blend * decay

    return output


def synthesize_guitar_audio(
        midi_path: str, output_path: str,
        config: BackingTrackConfig) -> np.ndarray:
    """
    Synthesize guitar audio from MIDI using Karplus-Strong + harmonic synthesis

    Incorporates recommendations from:
    - guitar_expert_precise: Realistic tone, natural attack, mid-range body
    - master_guitar_instructor: Rhythm variety, dynamics, accents
    - guitar_expert_qwen: Modulation effects, articulation options
    """
    sample_rate = 44100
    # scipy.signal used implicitly via apply_amp_simulation

    duration_seconds = (config.bars * config.beats_per_bar * 60) / config.bpm
    samples = int(duration_seconds * sample_rate)

    audio = np.zeros(samples, dtype=np.float32)
    beat_samples = int((60 / config.bpm) * sample_rate)

    events = generate_progression(config)
    current_sample = 0

    # Get rhythm and accent patterns (master_guitar_instructor)
    rhythm = RHYTHM_PATTERNS.get(
        config.rhythm_pattern, RHYTHM_PATTERNS['straight'])
    accents = ACCENT_PATTERNS.get(
        config.accent_pattern, ACCENT_PATTERNS['downbeat'])

    # Attack style settings (guitar_expert_precise)
    attack_settings = {
        'aggressive': {'attack_ms': 10, 'attack_amp': 2.5, 'decay_exp': 0.3},
        # More realistic
        'natural': {'attack_ms': 25, 'attack_amp': 1.5, 'decay_exp': 0.5},
        'soft': {'attack_ms': 40, 'attack_amp': 0.8, 'decay_exp': 0.7},
    }
    attack_cfg = attack_settings.get(
        config.attack_style, attack_settings['aggressive'])

    # Articulation settings (guitar_expert_qwen)
    articulation_settings = {
        'palm_mute': {'decay_rate': 12, 'gate_point': 0.7, 'brightness': 0.85},
        'staccato': {'decay_rate': 18, 'gate_point': 0.5, 'brightness': 0.9},
        'legato': {'decay_rate': 4, 'gate_point': 0.95, 'brightness': 0.7},
    }
    artic_cfg = articulation_settings.get(
        config.articulation, articulation_settings['palm_mute'])

    # Subdivisions based on style
    subdivisions = 8 if config.style in ['metal', 'djent', 'punk'] else 4

    for event in events:
        chord_samples = int(event.duration * beat_samples)
        chunk_samples = chord_samples // subdivisions

        for sub in range(subdivisions):
            # Apply rhythm pattern timing (master_guitar_instructor)
            rhythm_idx = sub % len(rhythm)
            rhythm_mult = rhythm[rhythm_idx]
            actual_chunk = int(chunk_samples * rhythm_mult)
            if actual_chunk < 100:
                actual_chunk = chunk_samples  # Fallback for very short

            # Apply accent pattern (master_guitar_instructor)
            accent_idx = sub % len(accents)
            velocity_mult = accents[accent_idx]

            chunk_start = sub * chunk_samples
            t = np.linspace(0, actual_chunk / sample_rate, actual_chunk)

            chunk_audio = np.zeros(actual_chunk)

            for interval in POWER_CHORD_INTERVALS:
                freq = 440 * (2 ** ((event.root_note + interval - 69) / 12))

                # 1. Karplus-Strong with configurable decay/brightness
                ks = karplus_strong(
                    freq,
                    actual_chunk / sample_rate,
                    sample_rate,
                    decay=0.95,
                    brightness=artic_cfg['brightness'])
                if len(ks) > actual_chunk:
                    ks = ks[:actual_chunk]
                elif len(ks) < actual_chunk:
                    ks = np.pad(ks, (0, actual_chunk - len(ks)))

                # 2. Harmonics with mid-body emphasis (guitar_expert_precise:
                # 250-350Hz warmth)
                harmonics = np.zeros(actual_chunk)
                # Adjusted harmonic weights - more mid-range body
                harmonic_weights = [1.0, 0.2, 0.7, 0.15,
                                    0.5, 0.1, 0.4, 0.08, 0.3, 0.05]
                for h, weight in enumerate(harmonic_weights, 1):
                    harm_freq = freq * h
                    if harm_freq < sample_rate / 2:
                        harmonics += weight * np.sin(2 * np.pi * harm_freq * t)

                # Add mid-body warmth (guitar_expert_precise: 250-350Hz band)
                mid_body_freq = 300  # Center of warmth band
                mid_body = np.sin(2 * np.pi * mid_body_freq * t) * 0.15
                harmonics += mid_body

                # 3. Pick attack with configurable style
                # (guitar_expert_precise)
                attack_samples_count = int(
                    attack_cfg['attack_ms'] / 1000 * sample_rate)
                attack_samples_count = min(attack_samples_count, actual_chunk)
                attack = np.zeros(actual_chunk)
                attack[:attack_samples_count] = np.random.uniform(
                    -1, 1, attack_samples_count) * attack_cfg['attack_amp']
                attack[:attack_samples_count] *= np.linspace(
                    1, 0, attack_samples_count) ** attack_cfg['decay_exp']

                # 4. Envelope with configurable articulation
                # (guitar_expert_qwen)
                attack_time = 0.001
                envelope = np.ones(actual_chunk)
                attack_samps = int(attack_time * sample_rate)
                if attack_samps > 0 and attack_samps < actual_chunk:
                    envelope[:attack_samps] = np.linspace(0, 1, attack_samps)
                # Exponential decay based on articulation
                envelope *= np.exp(-t * artic_cfg['decay_rate'])
                # Gate based on articulation
                gate_start = int(actual_chunk * artic_cfg['gate_point'])
                if gate_start < actual_chunk:
                    envelope[gate_start:] *= np.linspace(
                        1, 0, actual_chunk - gate_start) ** 2

                # Mix with velocity/accent applied (master_guitar_instructor)
                note = (ks * 0.3 + harmonics * 0.4 + attack * 0.3) * \
                    envelope * velocity_mult
                chunk_audio += note * 0.4

            # Pre-distortion - reduced per guitar_expert_precise (was 4, now
            # 2.8)
            chunk_audio = np.tanh(chunk_audio * 2.8) * 1.2

            # Second stage overdrive
            chunk_audio = np.tanh(chunk_audio * 1.3)

            # "Chug" transient
            chug_samples = int(0.008 * sample_rate)
            chug_samples = min(chug_samples, actual_chunk)
            if chug_samples > 0:
                chug = np.zeros(actual_chunk)
                chug[:chug_samples] = np.sin(
                    2 * np.pi * 90 * t[:chug_samples]) * 0.5
                chug[:chug_samples] *= np.exp(-t[:chug_samples] * 150)
                chunk_audio[:chug_samples] += chug[:chug_samples]

            # Place chunk in output
            start = current_sample + chunk_start
            end = min(start + actual_chunk, samples)
            actual_len = end - start
            if actual_len > 0 and actual_len <= len(chunk_audio):
                audio[start:end] = chunk_audio[:actual_len]

        current_sample += chord_samples

    # Apply modulation effects (guitar_expert_qwen)
    audio = apply_modulation(audio, sample_rate, config.modulation)

    # Add subtle noise floor for "amp hiss" realism
    noise = np.random.normal(0, 0.005, samples).astype(np.float32)
    audio += noise

    # Normalize before saving
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.95

    sf.write(output_path, audio, sample_rate)
    return output_path


def apply_modulation(audio: np.ndarray, sample_rate: int,
                     mod_type: str) -> np.ndarray:
    """
    Apply modulation effects (guitar_expert_qwen recommendation)

    Options: none, phaser, flanger, chorus
    """
    if mod_type == 'none':
        return audio

    from scipy import signal  # noqa: F401

    n_samples = len(audio)
    t = np.arange(n_samples) / sample_rate

    if mod_type == 'phaser':
        # Simple phaser: modulated allpass filter
        rate = 0.5  # Hz
        depth = 0.7
        lfo = np.sin(2 * np.pi * rate * t) * depth

        # Create phase-shifted version
        phased = np.zeros_like(audio)
        for i in range(n_samples):
            delay_samples = int((lfo[i] + 1) * 50)  # 0-100 samples delay
            if i - delay_samples >= 0:
                phased[i] = audio[i - delay_samples]
            else:
                phased[i] = audio[i]

        # Mix original with phased
        return audio * 0.7 + phased * 0.3

    elif mod_type == 'flanger':
        # Flanger: short modulated delay with feedback
        rate = 0.3  # Hz
        depth = 0.8
        lfo = (np.sin(2 * np.pi * rate * t) + 1) * 0.5 * depth

        max_delay = int(0.007 * sample_rate)  # 7ms max
        flanged = np.zeros_like(audio)

        for i in range(n_samples):
            delay = int(lfo[i] * max_delay)
            if i - delay >= 0:
                flanged[i] = audio[i] + audio[i - delay] * 0.5
            else:
                flanged[i] = audio[i]

        return flanged * 0.8

    elif mod_type == 'chorus':
        # Chorus: multiple detuned voices
        rate = 1.5  # Hz
        depth = 0.3

        # Create 3 slightly detuned copies
        chorus = audio.copy()
        for voice in range(3):
            phase = voice * 2 * np.pi / 3
            lfo = np.sin(2 * np.pi * rate * t + phase) * depth

            delayed = np.zeros_like(audio)
            for i in range(n_samples):
                delay = int((lfo[i] + 0.5) * 0.02 * sample_rate)  # Up to 20ms
                if i - delay >= 0:
                    delayed[i] = audio[i - delay]
                else:
                    delayed[i] = audio[i]

            chorus += delayed * 0.2

        return chorus * 0.7

    return audio


def synthesize_bass_audio(config: BackingTrackConfig,
                          sample_rate: int = 44100) -> np.ndarray:
    """
    Synthesize bass guitar audio to complement the guitar track.

    Bass plays root notes (or root+fifth/octave patterns) one octave below
    guitar. Uses Karplus-Strong with longer decay and less brightness.
    """
    # scipy.signal used in apply_bass_amp_simulation

    duration_seconds = (config.bars * config.beats_per_bar * 60) / config.bpm
    samples = int(duration_seconds * sample_rate)

    audio = np.zeros(samples, dtype=np.float32)
    beat_samples = int((60 / config.bpm) * sample_rate)

    events = generate_progression(config)
    current_sample = 0

    # Bass rhythm patterns
    bass_patterns = {
        'root': [1.0],                    # Just root on each chord
        'eighth': [1.0] * 8,              # 8th notes on root
        'fifth': [1.0, 0.0, 0.8, 0.0],    # Root, rest, fifth, rest
        # Root-octave pattern
        'octave': [1.0, 0.0, 0.7, 0.0, 0.9, 0.0, 0.7, 0.0],
        'walking': [1.0, 0.6, 0.7, 0.8],  # Walking bass feel
    }

    pattern = bass_patterns.get(config.bass_style, bass_patterns['root'])
    subdivisions = len(pattern)

    for event in events:
        chord_samples = int(event.duration * beat_samples)
        chunk_samples = chord_samples // subdivisions

        # Bass note is root, one octave below guitar
        bass_note = event.root_note - 12  # One octave down

        for sub in range(subdivisions):
            velocity = pattern[sub % len(pattern)]
            if velocity <= 0:
                continue

            chunk_start = sub * chunk_samples
            t = np.linspace(0, chunk_samples / sample_rate, chunk_samples)

            # Determine which note to play based on bass_style
            if config.bass_style == 'fifth' and sub == 2:
                note_midi = bass_note + 7  # Fifth
            elif config.bass_style == 'octave' and sub in [2, 4, 6]:
                note_midi = bass_note + 12 if sub == 4 else bass_note + 7
            else:
                note_midi = bass_note

            freq = 440 * (2 ** ((note_midi - 69) / 12))

            # Bass Karplus-Strong: longer decay, less brightness
            ks = karplus_strong(
                freq,
                chunk_samples / sample_rate,
                sample_rate,
                decay=0.998,
                brightness=0.4)  # Warmer, longer sustain
            if len(ks) > chunk_samples:
                ks = ks[:chunk_samples]
            elif len(ks) < chunk_samples:
                ks = np.pad(ks, (0, chunk_samples - len(ks)))

            # Add fundamental emphasis for bass
            fundamental = np.sin(2 * np.pi * freq * t) * 0.6

            # Sub-harmonic for extra low end
            sub_harm = np.sin(2 * np.pi * freq * 0.5 * t) * 0.2

            # Gentle envelope (bass notes sustain more)
            envelope = np.ones(chunk_samples)
            attack_samps = int(0.005 * sample_rate)  # 5ms attack
            if attack_samps > 0 and attack_samps < chunk_samples:
                envelope[:attack_samps] = np.linspace(0, 1, attack_samps)
            # Slower decay than guitar
            envelope *= np.exp(-t * 3)

            # Mix bass components
            chunk_audio = (ks * 0.3 + fundamental * 0.5
                           + sub_harm * 0.2) * envelope * velocity

            # Place chunk
            start = current_sample + chunk_start
            end = min(start + chunk_samples, samples)
            actual_len = end - start
            if actual_len > 0 and actual_len <= len(chunk_audio):
                audio[start:end] += chunk_audio[:actual_len] * 0.5

        current_sample += chord_samples

    # Normalize
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.9

    return audio


def apply_bass_amp_simulation(audio: np.ndarray,
                              sample_rate: int) -> np.ndarray:
    """
    Apply bass amp simulation optimized for mixing with guitar.

    In metal production, bass sits in the 80-250Hz range to complement
    guitar mids. Cut sub-bass (<60Hz), emphasize low-mids for punch.
    """
    from scipy import signal

    # 1. Aggressive high-pass to remove sub-bass that causes muddiness
    # Modern metal bass sits above 60Hz
    b_hp, a_hp = signal.iirfilter(
        4, 60 / (sample_rate / 2), btype='high', ftype='butter')
    audio = signal.filtfilt(b_hp, a_hp, audio)

    # 2. Light saturation (bass amps are cleaner than guitar)
    audio = np.tanh(audio * 1.5) * 0.9

    # 3. Low-mid punch (100-200Hz) - this is where bass lives in metal
    b_punch, a_punch = signal.iirpeak(150 / (sample_rate / 2), 2)
    audio = signal.filtfilt(b_punch, a_punch, audio)

    # 4. Upper bass definition (300-500Hz) - attack and note clarity
    b_def, a_def = signal.iirpeak(400 / (sample_rate / 2), 2)
    audio = signal.filtfilt(b_def, a_def, audio) * 0.7

    # 5. Low-pass to remove string noise (bass shouldn't have much above 2kHz)
    b_lp, a_lp = signal.iirfilter(
        4, 2000 / (sample_rate / 2), btype='low', ftype='butter')
    audio = signal.filtfilt(b_lp, a_lp, audio)

    # Normalize
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.85

    return audio.astype(np.float32)


def apply_amp_simulation(audio: np.ndarray, sample_rate: int,
                         style: str = 'metal') -> np.ndarray:
    """
    Apply amp simulation using DSP to approximate NeuralDSP-style tones

    Based on analysis of real NeuralDSP Gojira output:
    - 90% of energy in mid frequencies (250-2000Hz)
    - Only 9% in lows (<250Hz)
    - Minimal highs (>2kHz)

    This uses:
    - Multi-stage tube saturation (generates harmonics)
    - Mid-focused tone stack
    - Cabinet simulation with speaker resonance
    """
    from scipy import signal

    # Amp settings - updated per guitar_expert_precise recommendations
    amp_settings = {
        'metal': {
            'gain': 14.0, 'bass': 0.25, 'mid': 1.3, 'treble': 0.65,
            'presence': 0.45, 'mid_freq': 850, 'body_freq': 300,
            'tight': True, 'gate': True, 'cab_res': 100,
            'cab_lpf': 4500
        },
        'metal_reference': {
            'gain': 14.0, 'bass': 0.6, 'mid': 1.6, 'treble': 0.1,
            'presence': 0.1, 'mid_freq': 850, 'body_freq': 300,
            'tight': True, 'gate': True, 'cab_res': 100,
            'cab_lpf': 2400, 'hp_freq': 60, 'bass_boost': 0.5
        },
        'rock': {
            'gain': 6.0, 'bass': 0.5, 'mid': 1.0, 'treble': 0.6,
            'presence': 0.4, 'mid_freq': 650, 'body_freq': 280,
            'tight': False
        },
        'blues': {
            'gain': 3.0, 'bass': 0.55, 'mid': 0.85, 'treble': 0.5,
            'presence': 0.3, 'mid_freq': 550, 'body_freq': 250,
            'tight': False
        },
        'punk': {
            'gain': 7.0, 'bass': 0.35, 'mid': 1.1, 'treble': 0.7,
            'presence': 0.5, 'mid_freq': 900, 'body_freq': 320,
            'tight': True
        },
        'djent': {
            'gain': 11.0, 'bass': 0.4, 'mid': 0.9, 'treble': 0.6,
            'presence': 0.4, 'mid_freq': 1100, 'body_freq': 280,
            'tight': True
        },
        'grunge': {
            'gain': 8.0, 'bass': 0.6, 'mid': 0.7, 'treble': 0.55,
            'presence': 0.35, 'mid_freq': 600, 'body_freq': 320,
            'tight': False
        },
    }

    settings = amp_settings.get(style, amp_settings['metal'])

    # 0. High-pass filter to remove rumble (tight low end like NeuralDSP)
    # NeuralDSP has only 9% energy below 250Hz - configurable HP filtering
    if settings.get('tight', False):
        hp_freq = settings.get('hp_freq', 80)  # Configurable high-pass
        # First pass: Remove sub-bass
        b_hp1, a_hp1 = signal.iirfilter(
            2, hp_freq / (sample_rate / 2), btype='high', ftype='butter')
        audio = signal.filtfilt(b_hp1, a_hp1, audio)
        # Second pass: Gentle roll off (only if hp_freq > 60)
        if hp_freq > 60:
            b_hp2, a_hp2 = signal.iirfilter(
                2, 120 / (sample_rate / 2), btype='high', ftype='butter')
            audio = signal.filtfilt(b_hp2, a_hp2, audio)

    # 1. Input boost/gain staging
    audio = audio * settings['gain']

    # 2. Multi-stage tube saturation (key to generating harmonics!)
    def tube_saturation(x, drive=1.0, bias=0.1):
        """Asymmetric tube-style saturation with harmonic generation"""
        x = x * drive + bias  # DC bias for even harmonics
        # Polynomial waveshaping (more harmonics than tanh)
        shaped = x - (x**3 / 3) + (x**5 / 5)
        # Soft clip
        return np.tanh(shaped * 0.8)

    # Stage 1: Pre-amp (high gain, generates lots of harmonics)
    audio = tube_saturation(audio, drive=3.0, bias=0.05)

    # Stage 2: More saturation (cascaded gain stages like real high-gain amp)
    audio = tube_saturation(audio, drive=2.0, bias=0.02)

    # 3. Tone stack - MID-FOCUSED (this is key to matching NeuralDSP!)

    # Cut extreme lows aggressively (NeuralDSP has only 9% below 250Hz)
    b_lc, a_lc = signal.iirfilter(
        4, 180 / (sample_rate / 2), btype='high', ftype='butter')
    audio = signal.filtfilt(b_lc, a_lc, audio)

    # Bass band (very reduced - just subtle warmth)
    nyq = sample_rate / 2
    b_bass, a_bass = signal.iirfilter(
        2, [150 / nyq, 250 / nyq], btype='band', ftype='butter')
    bass_band = signal.filtfilt(
        b_bass, a_bass, audio) * settings['bass'] * 0.3

    # Mid band (THIS IS THE KEY - where guitar lives)
    mid_freq = settings.get('mid_freq', 800)
    b_mid, a_mid = signal.iirfilter(
        2, [250 / nyq, 2500 / nyq], btype='band', ftype='butter')
    mid_band = signal.filtfilt(b_mid, a_mid, audio) * settings['mid']

    # Mid resonance peak (characteristic amp voicing) - guitar_expert_precise:
    # 800-850Hz
    b_peak, a_peak = signal.iirpeak(mid_freq / nyq, 2)
    mid_band = signal.filtfilt(b_peak, a_peak, mid_band) * 1.3

    # Add mid-body warmth (guitar_expert_precise: 250-350Hz band)
    body_freq = settings.get('body_freq', 300)
    b_body, a_body = signal.iirpeak(body_freq / nyq, 3)
    body_band = signal.filtfilt(b_body, a_body, audio) * 0.25

    # Treble band (brightness, but not harsh)
    b_treble, a_treble = signal.iirfilter(
        2, [2000 / nyq, 4500 / nyq], btype='band', ftype='butter')
    treble_band = signal.filtfilt(
        b_treble, a_treble, audio) * settings['treble']

    # Combine with HEAVY mid emphasis (NeuralDSP is 90%+ mids)
    # Added body_band for 250-350Hz warmth (guitar_expert_precise)
    audio = (bass_band * 0.2 + body_band * 0.4
             + mid_band * 2.0 + treble_band * 0.3)

    # 4. Power amp saturation (gentler, more compression-like)
    audio = tube_saturation(audio, drive=1.5, bias=0.0)

    # 5. Cabinet simulation
    # Real guitar cabs have a resonance around 100-120Hz and roll off above
    # 4-5kHz

    # Low-pass (speaker can't reproduce very high frequencies)
    # Use configurable cab_lpf for different cab darkness levels
    cab_lpf = settings.get('cab_lpf', 4500)
    b_cab, a_cab = signal.iirfilter(
        4, cab_lpf / (sample_rate / 2), btype='low', ftype='butter')
    audio = signal.filtfilt(b_cab, a_cab, audio)

    # Speaker resonance (the "thump" of a 4x12)
    # Tone architect: adjust resonance to 100Hz or lower for tighter sound
    cab_res = settings.get('cab_res', 120)
    b_res, a_res = signal.iirpeak(cab_res / (sample_rate / 2), 4)  # Tighter Q
    audio = signal.filtfilt(b_res, a_res, audio)

    # Mid presence (speaker cone breakup simulation)
    b_pres, a_pres = signal.iirpeak(2500 / (sample_rate / 2), 2)
    audio = signal.filtfilt(b_pres, a_pres, audio) * settings['presence']

    # 6. Noise gate for tightness (if enabled)
    if settings.get('gate', False):
        # Simple gate - reduce signal below threshold
        threshold = 0.02
        gate = np.where(np.abs(audio) > threshold,
                        1.0, np.abs(audio) / threshold)
        audio = audio * gate

    # 7. Final stage - aggressive limiting for punch
    audio = np.tanh(audio * 1.2) * 0.95

    # Normalize
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.9

    return audio.astype(np.float32)


def process_with_neural_dsp(
        input_path: str, output_path: str,
        config: BackingTrackConfig) -> None:
    """Process audio through amp simulation."""

    # Load audio
    audio, sample_rate = sf.read(input_path)
    if len(audio.shape) == 1:
        audio = audio.astype(np.float32)
    else:
        audio = audio[:, 0].astype(np.float32)  # Mono

    print(f"Applying {config.style} amp simulation...")

    # Apply our amp simulation
    processed = apply_amp_simulation(audio, sample_rate, config.style)

    # Make stereo with slight widening
    left = processed
    # Slight delay on right channel for width
    delay_samples = int(0.003 * sample_rate)  # 3ms
    right = np.roll(processed, delay_samples)
    right[:delay_samples] = 0

    stereo = np.column_stack([left, right])

    sf.write(output_path, stereo, sample_rate)
    print(f"Processed audio saved to: {output_path}")

    return output_path


def list_available_presets(plugin: str = 'gojira') -> List[str]:
    """List available presets for a NeuralDSP plugin"""
    plugin_names = {
        'gojira': 'Archetype Gojira',
        'gojira_x': 'Archetype Gojira X',
        'plini': 'Archetype Plini',
        'plini_x': 'Archetype Plini X',
        'nolly': 'Archetype Nolly',
        'petrucci': 'Archetype Petrucci',
        'petrucci_x': 'Archetype Petrucci X',
        'misha_x': 'Archetype Misha Mansoor X',
    }

    preset_dir = NEURAL_PRESETS_BASE / \
        plugin_names.get(plugin, plugin_names['gojira'])

    if not preset_dir.exists():
        return []

    return [f.stem for f in preset_dir.glob("*.aupreset")]


def generate_backing_track(config: BackingTrackConfig,
                           output_dir: str = None) -> dict:
    """
    Main function to generate a complete backing track

    Returns dict with paths to generated files
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="neural_backing_")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {
        'config': config.__dict__,
        'files': {}
    }

    # 1. Generate chord progression
    print(f"Generating {config.style} progression in {config.key}...")
    events = generate_progression(config)
    print(f"  Created {len(events)} chord events")

    # 2. Create MIDI file
    midi_path = str(output_dir / f"backing_{config.key}_{config.style}.mid")
    create_midi_file(events, config, midi_path)
    results['files']['midi'] = midi_path
    print(f"  MIDI: {midi_path}")

    # 3. Create Guitar Pro file
    gp_path = str(output_dir / f"backing_{config.key}_{config.style}.gp5")
    if create_guitar_pro_file(events, config, gp_path):
        results['files']['guitar_pro'] = gp_path
        print(f"  Guitar Pro: {gp_path}")

    # 4. Synthesize raw guitar audio
    raw_audio_path = str(
        output_dir / f"backing_{config.key}_{config.style}_raw.wav")
    synthesize_guitar_audio(midi_path, raw_audio_path, config)
    results['files']['raw_audio'] = raw_audio_path
    print(f"  Raw guitar audio: {raw_audio_path}")

    # 5. Process guitar through amp simulation
    processed_path = str(
        output_dir / f"backing_{config.key}_{config.style}_neural.wav")
    process_with_neural_dsp(raw_audio_path, processed_path, config)
    results['files']['processed_audio'] = processed_path
    print(f"  Processed guitar: {processed_path}")

    # 6. Optionally add bass track
    if config.include_bass:
        print(f"  Generating bass track ({config.bass_style} style)...")

        # Synthesize bass audio
        bass_audio = synthesize_bass_audio(config)

        # Apply bass amp simulation
        bass_processed = apply_bass_amp_simulation(bass_audio, 44100)

        # Save bass track separately
        bass_path = str(
            output_dir / f"backing_{config.key}_{config.style}_bass.wav")
        sf.write(bass_path, bass_processed, 44100)
        results['files']['bass_audio'] = bass_path
        print(f"  Bass track: {bass_path}")

        # Load guitar track and mix with bass
        guitar_audio, sr = sf.read(processed_path)
        if len(guitar_audio.shape) == 2:
            guitar_audio = guitar_audio.mean(axis=1)  # Mono

        # Match lengths
        max_len = max(len(guitar_audio), len(bass_processed))
        if len(guitar_audio) < max_len:
            guitar_audio = np.pad(
                guitar_audio, (0, max_len - len(guitar_audio)))
        if len(bass_processed) < max_len:
            bass_processed = np.pad(
                bass_processed, (0, max_len - len(bass_processed)))

        # Normalize each track independently FIRST to get balanced levels
        guitar_max = np.max(np.abs(guitar_audio))
        if guitar_max > 0:
            guitar_audio = guitar_audio / guitar_max * 0.9

        bass_max = np.max(np.abs(bass_processed))
        if bass_max > 0:
            bass_processed = bass_processed / bass_max * 0.9

        # Apply high-pass to bass to prevent sub-bass from overwhelming the mix
        # This is standard mixing practice - bass sits above 60Hz in modern
        # metal
        from scipy import signal as sig
        b_hp, a_hp = sig.iirfilter(
            4, 80 / (sr / 2), btype='high', ftype='butter')
        bass_processed = sig.filtfilt(b_hp, a_hp, bass_processed)

        # Re-normalize bass after HP filter
        bass_max = np.max(np.abs(bass_processed))
        if bass_max > 0:
            bass_processed = bass_processed / bass_max * 0.9

        # Mix: guitar dominates, bass provides low-end support
        # Guitar at 90%, bass at lower level for punch without mud
        guitar_level = 0.9
        # Scale down bass significantly (~17% with default 0.7)
        bass_level = config.bass_volume * 0.25

        # Make stereo (guitar slightly left, bass slightly right for
        # separation)
        delay_samples = int(0.002 * sr)  # 2ms for guitar width
        guitar_left = guitar_audio * guitar_level
        guitar_right = np.roll(guitar_audio, delay_samples) * guitar_level
        guitar_right[:delay_samples] = 0

        # Bass centered (mono bass is standard for punch)
        bass_mono = bass_processed * bass_level

        # Pan: guitar wider (60/40), bass centered
        left = guitar_left * 0.6 + guitar_right * 0.4 + bass_mono * 0.5
        right = guitar_left * 0.4 + guitar_right * 0.6 + bass_mono * 0.5

        # Normalize stereo
        stereo = np.column_stack([left, right])
        max_val = np.max(np.abs(stereo))
        if max_val > 0:
            stereo = stereo / max_val * 0.95

        # Save mixed track
        mixed_path = str(
            output_dir / f"backing_{config.key}_{config.style}_full.wav")
        sf.write(mixed_path, stereo, sr)
        results['files']['mixed_audio'] = mixed_path
        print(f"  Full mix (guitar + bass): {mixed_path}")

        # Update processed path to the full mix
        processed_path = mixed_path

    return results


def main() -> None:
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate backing tracks with NeuralDSP tone')
    parser.add_argument('--key', default='E', help='Key (e.g., E, A, D)')
    parser.add_argument(
        '--style',
        default='metal',
        choices=list(PROGRESSIONS.keys()) + ['metal_reference'],
        help='Style (metal_reference = 97%% NeuralDSP Gojira match)')
    parser.add_argument('--bpm', type=int, default=120)
    parser.add_argument('--bars', type=int, default=4)
    parser.add_argument('--plugin', default='gojira',
                        choices=list(NEURAL_PLUGINS.keys()))
    parser.add_argument('--output', '-o', default=None,
                        help='Output directory')
    parser.add_argument('--list-presets', action='store_true',
                        help='List available presets')
    # New options from model recommendations
    parser.add_argument(
        '--rhythm', default='straight',
        choices=list(RHYTHM_PATTERNS.keys()),
        help='Rhythm pattern')
    parser.add_argument(
        '--accents', default='downbeat',
        choices=list(ACCENT_PATTERNS.keys()),
        help='Accent pattern')
    parser.add_argument(
        '--articulation', default='palm_mute',
        choices=['palm_mute', 'staccato', 'legato'],
        help='Articulation style')
    parser.add_argument(
        '--modulation', default='none',
        choices=['none', 'phaser', 'flanger', 'chorus'],
        help='Modulation effect')
    parser.add_argument(
        '--attack', default='aggressive',
        choices=['aggressive', 'natural', 'soft'],
        help='Attack style')
    # Bass track options
    parser.add_argument(
        '--bass', action='store_true',
        help='Include bass track in output')
    parser.add_argument(
        '--bass-style', default='eighth',
        choices=['root', 'eighth', 'fifth', 'octave', 'walking'],
        help='Bass playing style')
    parser.add_argument(
        '--bass-volume', type=float, default=0.7,
        help='Bass volume (0.0-1.0)')

    args = parser.parse_args()

    if args.list_presets:
        print(f"Available presets for {args.plugin}:")
        for preset in list_available_presets(args.plugin):
            print(f"  - {preset}")
        return

    config = BackingTrackConfig(
        key=args.key,
        style=args.style,
        bpm=args.bpm,
        bars=args.bars,
        plugin=args.plugin,
        rhythm_pattern=args.rhythm,
        accent_pattern=args.accents,
        articulation=args.articulation,
        modulation=args.modulation,
        attack_style=args.attack,
        # Bass options
        include_bass=args.bass,
        bass_style=args.bass_style,
        bass_volume=args.bass_volume,
    )

    results = generate_backing_track(config, args.output)

    print("\n=== Generation Complete ===")
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
