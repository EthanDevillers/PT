# game.py
from note import Note
import random
from music import midi_to_note, note_to_midi
import note
from partition import Partition
from config import *
from staff import  Staff


class Game:

    def __init__(self): 
        self.staff = Staff()
        self.current_note = self.new_note()
        #if more than one note is to be played at once (partition mode)
        self.current_notes = []
        self.mode = "game"  # "game" or "partition"
        self.partition = None
        self.visible_start = 0
        self.notes_played = set()
        
    def get_visible_measures(self, staff):
        #Return measures list to display on screen
        x_start = 100
        screen_width = WIDTH
        measures = []
        x = x_start
        i = int(self.visible_start) # force  index to be int
        measure_width = staff.get_measure_width(self.partition)

        while i < len(self.partition.measures):
            if x + measure_width > screen_width:
                break
            measures.append(self.partition.measures[i])
            x += measure_width
            i += 1
        return measures

    def new_note(self):
        midi = random.randint(MIDI_START, MIDI_END)
        note_name = midi_to_note(midi)

        note = Note(note_name)

        # 🎼 attribution automatique de la portée
        if midi < note_to_midi("C4"):
            note.staff = 2  # clé de fa (main gauche)
        else:
            note.staff = 1  # clé de sol (main droite)

        return note

    def _check_game_note(self, played_note):
        # Compare via MIDI numbers to avoid accidental string mismatches
        try:
            played_midi = note_to_midi(played_note)
            expected_midi = note_to_midi(self.current_note.name)
        except Exception as e:
            print(f"[Game] Error converting notes to MIDI: {e}")
            return False

        correct = played_midi == expected_midi
        # Debug output
        print(f"[Game] Played: {played_note} (MIDI {played_midi}) | Expected: {self.current_note.name} (MIDI {expected_midi}) => {'OK' if correct else 'NO'}")

        if correct:
            self.current_note = self.new_note()
            return True
        return False

    def _check_partition_note(self, played_note):
        if not self.partition:
            return False

        expected_notes = self.partition.current_notes()
        if not expected_notes:
            return False

        #  ignorer les grace notes
        playable_expected_notes = [
            n for n in expected_notes
            if not getattr(n, "is_grace", False)]

        if not playable_expected_notes:
            self.advance_partition()
            return True
        
        if len(expected_notes) == 1: 
            # 🎵 mode note unique
            expected_note = playable_expected_notes[0]
            try:
                played_midi = note_to_midi(played_note)
                expected_midi = note_to_midi(expected_note.name)
            except Exception as e:
                print(f"[Game] MIDI conversion error: {e}")
                print(f"[DEBUG] played_note={played_note}")
                return False
            correct = played_midi == expected_midi  
            
        else :
            # 🔧 normaliser played_note
            if isinstance(played_note, list):
                played_note = "".join(played_note)
            if not isinstance(played_note, str) or played_note.strip() == "":
                return False

            try:
                played_midi = note_to_midi(played_note)
                expected_midi = {note_to_midi(n.name) for n in playable_expected_notes}
            except Exception as e:
                print(f"[Game] MIDI conversion error: {e}")
                print(f"[DEBUG] played_note={played_note}")
                return False

            # 🎹 initialiser la mémoire d'accord
            if not hasattr(self, "notes_played"):
                self.notes_played = set()

            # ➕ ajouter / retirer la note jouée
            if played_midi in self.notes_played:
                self.notes_played.remove(played_midi)
                note.highlighted = False


            else:
                self.notes_played.add(played_midi)
                note.highlighted = True
            print(f"[Game:Partition] Played MIDI set: {self.notes_played} | "f"Expected MIDI set: {expected_midi}")

            correct = self.notes_played == expected_midi

        if correct:
            self.advance_partition()
            self.notes_played.clear()
            return True
        else:
            return False

    def advance_partition(self):
        VISIBLE_MEASURES = self.staff.get_visible_measures_count(self.partition, WIDTH)

        # Déléger l'avancement à l'objet Partition (garde les index cohérents)
        if not self.partition:
            return

        # Sauvegarder l'indice précédent pour vérifier si on change de page
        prev_measure = self.partition.current_measure_idx
        last_visible = self.visible_start + VISIBLE_MEASURES - 1

        total_measures = len(self.partition.measures)

        # Avancer dans la partition
        self.partition.advance()
        current_idx = self.partition.current_measure_idx

        # mettre à jour les notes courantes affichées
        self.current_notes = self.partition.current_notes()

        # Scroller SEULEMENT si:
        # 1. La mesure précédente était la dernière visible
        # 2. Et on a vraiment avancé au-delà (on a terminé la mesure)
        # 3. Et l'index d'événement de la nouvelle mesure est 0 (début de la nouvelle mesure)
        if prev_measure == last_visible and current_idx > last_visible and self.partition.current_event_idx == 0:
            # Faire défiler pour afficher les mesures suivantes
            new_start = prev_measure + 1
            # si on n'a pas assez de mesures restantes, recaler pour afficher
            # autant de mesures que possible à droite
            if new_start + VISIBLE_MEASURES > total_measures:
                new_start = max(0, total_measures - VISIBLE_MEASURES)
            self.visible_start = new_start

        # Clamp final: si on est près de la fin, décaler la fenêtre pour toujours afficher les dernières mesures
        if self.visible_start + VISIBLE_MEASURES > total_measures:
            self.visible_start = max(0, total_measures - VISIBLE_MEASURES)

    def check_note(self, played_notes):
        if self.mode == "game":
            return self._check_game_note(played_notes)
        else:
            return self._check_partition_note(played_notes)

    def load_partition(self, path):
        # Partition accepts a JSON file with {"notes": ["C4","D4",...]}
        try:
            self.partition = Partition(path)
            self.partition.reset()
            self.mode = "partition"
            self.visible_start = 0
            self.current_notes = self.partition.current_notes()
            return True
        except Exception as e:
            print(f"[Game] Failed to load partition {path}: {e}")
            self.partition = None
            self.mode = "game"
            return False

    def unload_partition(self):
        self.partition = None
        self.mode = "game"
        self.current_note = self.new_note()
