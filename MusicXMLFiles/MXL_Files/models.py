class NoteData:
    def __init__(self, name, duration):
        self.name = name
        self.duration = duration

    def to_dict(self):
        return {
            "name": self.name,
            "duration": self.duration
        }


class PartitionData:
    def __init__(self, title="Partition importée", tempo=80):
        self.title = title
        self.tempo = tempo
        self.notes = []

    def add_note(self, note: NoteData):
        self.notes.append(note)

    def to_dict(self):
        return {
            "title": self.title,
            "tempo": self.tempo,
            "notes": [n.to_dict() for n in self.notes]
        }
