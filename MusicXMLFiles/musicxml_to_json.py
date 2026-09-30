# musicxml_to_json.py
from music21 import converter
import json
import sys

def musicxml_to_json(xml_path, json_path):
    score = converter.parse(xml_path)

    events = []

    for e in score.flat.notesAndRests:
        if e.isRest:
            events.append({
                "type": "rest",
                "duration": float(e.quarterLength) * 4
            })
        elif e.isNote:
            events.append({
                "type": "note",
                "pitch": e.pitch.nameWithOctave,
                "duration": float(e.quarterLength) * 4
            })

    partition = {
        "title": score.metadata.title if score.metadata else "Partition importée",
        "events": events
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(partition, f, indent=4, ensure_ascii=False)

    print("✅ Conversion terminée")

if __name__ == "__main__":
    musicxml_to_json(sys.argv[1], sys.argv[2])
