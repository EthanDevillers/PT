from music21 import converter, note, meter, chord, harmony

# =========================
# DURÉES NORMALISÉES
# =========================

# duration (ton moteur) -> quarterLength (music21)
NORMALIZED_DURATIONS = {
    1: 0.25,     # double croche
    1.5: 0.375,  # double croche pointée
    2: 0.5,      # croche
    3: 0.75,     # croche pointée
    4: 1.0,      # noire
    6: 1.5,      # noire pointée
    8: 2.0,      # blanche
    12: 3.0,     # blanche pointée
    16: 4.0,     # ronde
    24: 6.0      # ronde pointée
}


def get_duration(e, tolerance=0.05):
    """
    Retourne la durée normalisée pour ton moteur.
    - Grace note → duration = 1
    - Sinon : quantification depuis quarterLength
    """
    # 🎵 Grace notes (Chopin ❤️)
    if e.duration.isGrace:
        return 1

    ql = float(e.quarterLength)

    best_match = None
    min_diff = float("inf")

    for duration, ref_ql in NORMALIZED_DURATIONS.items():
        diff = abs(ql - ref_ql)
        if diff < min_diff:
            min_diff = diff
            best_match = duration

    # Si aucune correspondance exacte, retourner la durée la plus proche
    if best_match is None or min_diff > tolerance:
        # Arrondir à la durée la plus proche
        for duration, ref_ql in NORMALIZED_DURATIONS.items():
            if abs(ql - ref_ql) == min_diff:
                return duration
    
    return best_match


def get_offset(offset):
    """
    Offset normalisé (basé sur la noire = 4)
    """
    return round(float(offset) * 4, 3)


# =========================
# CONVERSION MUSICXML → JSON
# =========================

def convert_musicxml(path):
    score = converter.parse(path)

    # ===== TITRE =====
    md = score.metadata
    if md:
        title = (
            md.bestTitle
            or md.title
            or md.workTitle
            or md.movementName
            or "Partition importée"
        )
    else:
        title = "Partition importée"

    # ===== TIME SIGNATURE =====
    time_sig = "4/4"
    ts = score.recurse().getElementsByClass(meter.TimeSignature)
    if ts:
        time_sig = ts[0].ratioString

    measures_json = {}

    # ===== PARCOURS DES PARTS =====
    for part_index, part in enumerate(score.parts):
        for measure in part.getElementsByClass("Measure"):
            m_num = measure.number

            if m_num not in measures_json:
                measures_json[m_num] = {
                    "number": m_num,
                    "events": []
                }

            for e in measure.notesAndRests:
                duration = get_duration(e)
                offset = get_offset(e.offset)

                # Si la durée n'a pas pu être déterminée, ignorer l'événement
                if duration is None:
                    continue

                # Ignorer les symboles d'harmonie (ChordSymbol, NoChord) qui
                # peuvent exposer des `pitches` (ex: 'E') et créer de fausses notes
                if isinstance(e, harmony.ChordSymbol) or isinstance(e, harmony.NoChord):
                    continue

                # staff (piano = 2 portées)
                staff = e.staff if hasattr(e, "staff") and e.staff else part_index + 1

                # ===== REST =====
                if e.isRest:
                    measures_json[m_num]["events"].append({
                        "type": "rest",
                        "duration": duration,
                        "offset": offset,
                        "staff": staff
                    })
                    continue

                # ===== NOTE =====
                if isinstance(e, note.Note):
                    measures_json[m_num]["events"].append({
                        "type": "note",
                        "pitch": e.pitch.nameWithOctave,
                        "duration": duration,
                        "offset": offset,
                        "staff": staff,
                        "is_grace": e.duration.isGrace
                    })

                # ===== ACCORD =====
                elif isinstance(e, chord.Chord):
                    for p in e.pitches:
                        measures_json[m_num]["events"].append({
                            "type": "note",
                            "pitch": p.nameWithOctave,
                            "duration": duration,
                            "offset": offset,
                            "staff": staff,
                            "is_grace": e.duration.isGrace
                        })

    # ===== TRI DES MESURES =====
    # Dédupliquer les notes identiques sur plusieurs portées (même offset + pitch)
    for m in measures_json.values():
        notes_map = {}
        other_events = []
        for ev in m['events']:
            if ev.get('type') != 'note':
                other_events.append(ev)
                continue
            key = (ev['offset'], ev['pitch'])
            if key not in notes_map:
                notes_map[key] = ev
            else:
                existing = notes_map[key]
                # garder l'événement avec la plus grande durée
                if ev.get('duration', 0) > existing.get('duration', 0):
                    notes_map[key] = ev
                elif ev.get('duration', 0) == existing.get('duration', 0):
                    # en cas d'égalité, préférer la staff 1
                    if existing.get('staff') != 1 and ev.get('staff') == 1:
                        notes_map[key] = ev

        # reconstruire la liste d'événements
        merged = other_events + list(notes_map.values())
        # trier par offset pour garder l'ordre temporel
        merged.sort(key=lambda x: (x.get('offset', 0), x.get('type') != 'note', x.get('pitch', '')))
        m['events'] = merged

    ordered_measures = [
        measures_json[k] for k in sorted(measures_json.keys())
    ]

    return {
        "title": title,
        "time_signature": time_sig,
        "measures": ordered_measures
    }
