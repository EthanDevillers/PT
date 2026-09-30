# partition.py
from note import Note
from config import *

class Partition:
    def __init__(self, path):
        import json
        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.title = self.data.get("title", "Sans titre")
        self.measures = self.data.get("measures", [])
        # Ensure events in each measure are sorted by offset (temporal order).
        for measure in self.measures:
            if "events" in measure and isinstance(measure["events"], list):
                measure["events"].sort(key=lambda e: float(e.get("offset", 0)))
        self.current_measure_idx = 0
        self.current_event_idx = 0

        ts = self.data.get("time_signature", "4/4")
        num, denom = ts.split("/")
        num = int(num)
        denom = int(denom)
        self.measure_duration = num * (4 / denom)  # en temps

    def current_notes(self):
        """
        Retourne la liste des notes jouables au même offset dans la mesure courante.
        Ignore les rests mais avance automatiquement si la mesure est finie.
        """
        while self.current_measure_idx < len(self.measures):
            measure = self.measures[self.current_measure_idx]

            if self.current_event_idx >= len(measure["events"]):
                # passer à la mesure suivante
                self.current_measure_idx += 1
                self.current_event_idx = 0
                continue

            # Offset de la note actuelle
            current_offset = measure["events"][self.current_event_idx].get("offset", 0)

            # Collecter toutes les notes au même offset
            notes = []
            for event in measure["events"]:
                if event.get("offset", 0) == current_offset and event["type"] == "note":
                    note_obj = Note(event["pitch"])
                    note_obj.staff = event.get("staff", 1)
                    note_obj.is_grace = event.get("is_grace", False)
                    notes.append(note_obj)

            if notes:
                return notes
            else:
                # Si aucun note mais rest à cet offset → avancer automatiquement
                self.advance()
                continue

        # Fin de partition
        return []

    def advance(self):
        if self.current_measure_idx >= len(self.measures):
            return

        measure = self.measures[self.current_measure_idx]
        current_offset = measure["events"][self.current_event_idx].get("offset", 0)

        self.current_event_idx += 1

        while (
            self.current_event_idx < len(measure["events"])
            and measure["events"][self.current_event_idx].get("offset", 0) == current_offset
        ):
            self.current_event_idx += 1

        if self.current_event_idx >= len(measure["events"]):
            self.current_measure_idx += 1
            self.current_event_idx = 0


    def reset(self):
        """
        Remet la partition au début.
        """
        self.current_measure_idx = 0
        self.current_event_idx = 0

    def is_finished(self):
        """
        Retourne True si la partition est terminée.
        """
        return self.current_measure_idx >= len(self.measures)