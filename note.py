# note.py
class Note:
    def __init__(self, name):
        self.name = name
        # y is computed at draw time because it depends on which staff the note
        # will be placed on (treble vs bass). See Staff.draw_note.
        self.y = None
        self.active = True
