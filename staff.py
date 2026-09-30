# staff.py
from numpy import partition
import pygame
from config import *
from music import note_to_midi, note_to_y

# MIDI number for middle C (C4) used to decide staff assignment
MIDDLE_C_MIDI = note_to_midi('C4')

class Staff:
    def __init__(self):
        self.line_spacing = STAFF_LINE_SPACING

        # Treble staff (clé de sol)
        # positionner la portée visuellement en fonction de STAFF_TOP
        self.treble_top = STAFF_TOP
        self.treble_bottom = self.treble_top + 4 * self.line_spacing

        # Gap between staves and bass staff (clé de fa)
        self.staff_gap = STAFF_GAP  # gap in pixels (from config)
        self.bass_top = self.treble_bottom + self.staff_gap
        self.bass_bottom = self.bass_top + 4 * self.line_spacing

        # charger la clé de sol (image)
        self.treble_clef_img = pygame.image.load("assets/treble_clef.png").convert_alpha()
        self.treble_clef_img = pygame.transform.scale(self.treble_clef_img, (80, 80))
        # charger la clé de fa (image)
        self.bass_clef_img = pygame.image.load("assets/bass_clef.png").convert_alpha()
        self.bass_clef_img = pygame.transform.scale(self.bass_clef_img, (80, 80))


        NOTE_PATHS = {
            1: "assets/double_croche.png",
            1.5: "assets/dotted_double_croche.png",
            2: "assets/croche.png",
            3: "assets/dotted_croche.png",
            4: "assets/noire.png",
            6: "assets/dotted_noire.png",
            8: "assets/blanche.png",
            12: "assets/dotted_blanche.png",
            16: "assets/ronde.png",
            24: "assets/dotted_ronde.png",
        }

        # Mapping durée -> (w, h) cible
        NOTE_SIZES = {
            1: (120, 120),   # double-croche
            1.5: (120, 120), # double-croche pointée
            2: (120, 120),   # croche
            3: (120, 120),   # croche pointée
            4: (120, 120),   # noire
            6: (120, 120),   # noire pointée
            8: (120, 120),   # blanche
            12: (120, 120),  # blanche pointée
            16: (120, 120),  # ronde
            24: (120, 120),  # ronde pointée
        }
        self.note_images = {}
        for dur, path in NOTE_PATHS.items():
            img = pygame.image.load(path).convert_alpha()
            w, h = NOTE_SIZES[dur]
            self.note_images[dur] = pygame.transform.smoothscale(img, (w, h))

        # charger l'image du bémol
        self.bemol_img = pygame.image.load("assets/bemol.png").convert_alpha()
        self.bemol_img = pygame.transform.scale(self.bemol_img, (30, 30))


    def draw(self, screen):
        # Treble staff lines
        for i in range(5):
            y = self.treble_bottom - i * self.line_spacing
            pygame.draw.line(screen, BLACK, (80, y), (WIDTH - 50, y), 2)
        # Treble clef
        screen.blit(self.treble_clef_img, (10, self.treble_top + 10))
        # Bass staff lines
        for i in range(5):
            y = self.bass_top + i * self.line_spacing
            pygame.draw.line(screen, BLACK, (80, y), (WIDTH - 50, y), 2)
        # Bass clef (shifted down by 10 pixels)
        screen.blit(self.bass_clef_img, (10, self.bass_top - 15))

        # Draw First measure bar line
        pygame.draw.line(screen, BLACK, (80, self.treble_top), (80, self.bass_bottom), 3)
        # Draw Last measure bar line
        pygame.draw.line(screen, BLACK, (WIDTH - 50, self.treble_top), (WIDTH - 50, self.bass_bottom), 3)
        
    def get_measure_width(self, partition):
        """
        Largeur d'une mesure en pixels en fonction de la durée totale de la mesure.
        partition.measure_duration doit être le nombre de temps par mesure (ex: 4 pour 4/4)
        """
        beats_per_measure = partition.measure_duration 
        return beats_per_measure * 4  * PIXELS_PER_BEAT + START_END_WIDTH * 2

    def get_visible_measures_count(self, partition, screen_width):
        """
        Nombre maximal de mesures visibles à l'écran en tenant compte de la largeur disponible
        """
        x_start = 100
        available_width = (screen_width - x_start - 50)  # marge droite
        measure_width = self.get_measure_width(partition)
        return max(1, int(available_width // measure_width))
    
    def draw_note(self, screen, note, x):
        """Dessine une note à partir de son image"""
        midi = note_to_midi(note.name)

        # Respecter la portée déclarée dans la partition si fournie
        staff_flag = getattr(note, "staff", None)
        if staff_flag == 2:
            y = note_to_y(note.name, 'G2', self.bass_bottom)
        elif staff_flag == 1:
            y = note_to_y(note.name, 'E4', self.treble_bottom)
        else:
            # fallback basé sur la hauteur MIDI
            if midi < MIDDLE_C_MIDI:
                staff_flag = 2
                y = note_to_y(note.name, 'G2', self.bass_bottom)
            else:
                staff_flag = 1
                y = note_to_y(note.name, 'E4', self.treble_bottom)

        # Choisir image
        duration = getattr(note, "duration", 4)  # défaut = noire
        img = self.note_images.get(duration, self.note_images[4])

        # 🔹 Réduire taille si grace note
        if getattr(note, "is_grace", False):
            w, h = img.get_size()
            img = pygame.transform.smoothscale(img, (60, 60))

        # Appliquer offset
        rect = img.get_rect(center=(x, y))
        screen.blit(img, rect)

        # dièse
        if "#" in note.name:
            font = pygame.font.SysFont("arial", 28, bold=True)
            sharp = font.render("♯", True, BLACK)
            screen.blit(sharp, (x - 28, y - 16))

        # bémol
        if "-" in note.name or "b" in note.name:
            rect = self.bemol_img.get_rect(center=(x - 20, y - 5))
            screen.blit(self.bemol_img, rect)

        # ledger lines: use announced staff as starting point
        self.draw_ledger_lines(screen, x, y, staff_flag)


    def draw_ledger_lines(self, screen, x, y, staff_flag):
        # Draw ledger lines for notes outside the staff specified by staff_flag.
        # staff_flag: 1 = treble, 2 = bass. Use a small tolerance for rounding.
        tol = 2  # pixels tolerance
        line_len = 20  # half-length of ledger line

        if staff_flag == 2:
            staff_top, staff_bottom = self.bass_top, self.bass_bottom
        else:
            staff_top, staff_bottom = self.treble_top, self.treble_bottom

        # above the staff
        if y < staff_top - tol:
            current_y = staff_top - self.line_spacing
            while current_y >= y - tol:
                pygame.draw.line(screen, BLACK, (x - line_len, current_y), (x + line_len, current_y), 2)
                current_y -= self.line_spacing

        # below the staff
        elif y > staff_bottom + tol:
            current_y = staff_bottom + self.line_spacing
            while current_y <= y + tol:
                pygame.draw.line(screen, BLACK, (x - line_len, current_y), (x + line_len, current_y), 2)
                current_y += self.line_spacing

    def draw_partition(self, screen, partition, measures):
        x_start = 100
        x = x_start
        top = self.treble_top
        bottom = self.bass_bottom
        screen_width = screen.get_width()

        measure_width = self.get_measure_width(partition)

        for measure in measures:
            # Vérifier que la mesure tient complètement à l'écran
            # Si elle ne tient pas, ne rien dessiner de cette mesure
            if x + measure_width > screen_width - 50:  # marge de 50px à droite
                break
            
            # regrouper les events par offset
            events_by_offset = {}
            for event in measure["events"]:
                off = event["offset"]
                events_by_offset.setdefault(off, []).append(event)

            # offsets triés dans l’ordre temporel
            sorted_offsets = sorted(events_by_offset.keys())

            for offset in sorted_offsets:
                events = events_by_offset[offset]

                # position x basée sur l'offset (offset en beats depuis le début de la mesure)
                offset_x = x + START_END_WIDTH + offset * PIXELS_PER_BEAT

                # durée max à cet offset (utile si besoin, mais on n'avance plus le curseur par incrément)
                max_duration = 0

                for event in events:
                    duration = event.get("duration", 0)
                    max_duration = max(max_duration, duration)

                    if event.get("type") == "note":
                        pitch = event.get("pitch")
                        staff = event.get("staff", 1)

                        # note temporaire
                        class TempNote:
                            def __init__(self, name, duration, staff):
                                self.name = name
                                self.duration = duration
                                self.staff = staff

                        tmp_note = TempNote(pitch, duration, staff)
                        self.draw_note(screen, tmp_note, offset_x)

            # barre de mesure
            pygame.draw.line(screen, BLACK, (x + measure_width, top), (x + measure_width, bottom), 3)
            x += measure_width


    def draw_play_cursor(self, screen, x):
        top = self.treble_top - 10
        bottom = self.bass_bottom + 10
        pygame.draw.line(screen, (220, 0, 0), (x, top), (x, bottom), 3)

    def get_cursor_x(self, partition , visible_start):
        x_start = 100
        

        # mesure relative à la page
        # sécurité: partition valide et pas terminée
        if not partition:
            return None
        if partition.current_measure_idx < visible_start:
            return None
        if partition.current_measure_idx >= len(partition.measures):
            return None

        measure_idx = partition.current_measure_idx - visible_start
        if measure_idx < 0:
            return None

        measure_width = self.get_measure_width(partition)
        x = x_start + measure_idx * measure_width + START_END_WIDTH

        # position dans la mesure
        measure = partition.measures[partition.current_measure_idx]

        # On calcule la position du curseur en utilisant l'offset de
        # l'événement courant (ou la fin de la mesure si on est après
        # le dernier événement). Cela correspond au comportement de
        # draw_partition qui place les notes selon leur "offset".
        idx = partition.current_event_idx
        if idx < 0:
            beat_pos = 0
        elif idx >= len(measure.get("events", [])):
            beat_pos = partition.measure_duration
        else:
            ev = measure["events"][idx]
            beat_pos = ev.get("offset", 0)

        x += beat_pos * PIXELS_PER_BEAT
        return x