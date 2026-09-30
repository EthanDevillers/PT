# music.py
from config import STAFF_TOP, STAFF_LINE_SPACING, STAFF_GAP
NOTE_ORDER = ["C", "C#", "D", "D#", "E",
              "F", "F#", "G", "G#", "A", "A#", "B"]

REFERENCE_NOTE = "E4"   # ligne du bas (clé de sol)
REFERENCE_NOTE_BASS = "G2"  # ligne du bas (clé de fa)
# NOTE_STEP is half the staff line spacing (line -> space -> line)
NOTE_STEP = STAFF_LINE_SPACING / 2




def note_to_midi(note):
    # Split note into name (e.g., 'C#') and octave (e.g., '4') allowing multi-digit octaves
    i = len(note) - 1
    while i >= 0 and note[i].isdigit():
        i -= 1
    name = note[:i+1]
    octave = int(note[i+1:])
    # normalize accidentals: allow '-' (flat), 'b' (flat), '♭' (flat), '♯' (sharp)
    name_norm = name.replace('♭', 'b').replace('-', 'b').replace('♯', '#')

    # map common flat names to their enharmonic sharp equivalents when NOTE_ORDER uses sharps
    FLAT_TO_SHARP = {
        'Bb': 'A#', 'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#',
        'Cb': 'B',  'Fb': 'E'
    }

    if name_norm in NOTE_ORDER:
        semitone_name = name_norm
    elif name_norm in FLAT_TO_SHARP:
        semitone_name = FLAT_TO_SHARP[name_norm]
    else:
        raise ValueError(f"Unsupported note name: '{name}' (normalized: '{name_norm}')")

    # MIDI standard: midi = (octave + 1) * 12 + semitone_index
    return (octave + 1) * 12 + NOTE_ORDER.index(semitone_name)


def midi_to_note(midi):
    octave = midi // 12 - 1
    name = NOTE_ORDER[midi % 12]
    return f"{name}{octave}"


def parse_note(note):
    """Return (name, octave, base_letter) for a note string like 'C#4'."""
    i = len(note) - 1
    while i >= 0 and note[i].isdigit():
        i -= 1
    name = note[:i+1]
    octave = int(note[i+1:])
    base_letter = name[0]
    return name, octave, base_letter


def note_to_y(note, reference_note=REFERENCE_NOTE, reference_y=None):
    """Map note to a Y coordinate using diatonic steps (lines/spaces).

    Parameters:
    - note: 'C#4' etc.
    - reference_note: reference note name (e.g., 'E4' for treble bottom line)
    - reference_y: pixel Y coordinate of the reference_note (if None, uses treble bottom)

    Returns: float Y coordinate (pixels)
    """
    # allow either calling with the simple signature or the previous one
    if isinstance(note, str):
        name, octave, base_letter = parse_note(note)
    else:
        raise TypeError("note must be a string like 'C4' or 'C#4'")

    if reference_y is None:
        reference_y = STAFF_TOP + 4 * STAFF_LINE_SPACING

    # parse reference
    rname, roctave, rbase = parse_note(reference_note)

    diatonic = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    step = (octave - roctave) * 7 + (diatonic.index(base_letter) - diatonic.index(rbase))
    return reference_y - step * NOTE_STEP


if __name__ == "__main__":
    # quick visual test outputs
    print("Note mapping test (treble ref E4, bass ref G2):")
    test_notes = ["A0", "C1", "G2", "C3", "G3", "C4", "A4", "C5", "C8"]
    treble_ref_y = STAFF_TOP + 4 * STAFF_LINE_SPACING
    bass_ref_y = treble_ref_y + STAFF_GAP + 4 * STAFF_LINE_SPACING
    for n in test_notes:
        ty = note_to_y(n, reference_note=REFERENCE_NOTE, reference_y=treble_ref_y)
        by = note_to_y(n, reference_note=REFERENCE_NOTE_BASS, reference_y=bass_ref_y)
        print(f"{n}: treble_y={ty:.1f}, bass_y={by:.1f}, midi={note_to_midi(n)}")



