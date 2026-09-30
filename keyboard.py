# keyboard.py
import pygame
from config import *

class PianoKey:
    def __init__(self, note, rect, color):
        self.note = note
        self.rect = rect
        self.color = color
        self.base_color = color

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 1)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class Keyboard:
    def __init__(self, octaves=2, start_octave=3, full_piano=True):
        self.keys = []
        self.octaves = octaves
        self.start_octave = start_octave
        self.full_piano = full_piano
        self.create_keys()

    def create_keys(self):
        # Reset keys
        self.keys = []

        if self.full_piano:
            # Full 88-key piano from A0 (MIDI 21) to C8 (MIDI 108)
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            midi_start = 21
            midi_end = 108

            keys_info = []  # list of {'note': 'A0', 'is_black': False}
            for midi in range(midi_start, midi_end + 1):
                name = note_names[midi % 12]
                octave = midi // 12 - 1
                note = f"{name}{octave}"
                is_black = '#' in name
                keys_info.append({'note': note, 'is_black': is_black})

            total_white = sum(1 for k in keys_info if not k['is_black'])
            white_key_width = WIDTH // total_white
            black_key_width = int(white_key_width * 0.6)
            black_key_height = int(KEYBOARD_HEIGHT * 0.6)

            # Center the keyboard horizontally
            total_width = white_key_width * total_white
            x_start = max(0, (WIDTH - total_width) // 2)

            # 1) Add white keys and record their x positions
            white_positions = []
            x = x_start
            for k in keys_info:
                if not k['is_black']:
                    rect = pygame.Rect(x, KEYBOARD_TOP, white_key_width, KEYBOARD_HEIGHT)
                    self.keys.append(PianoKey(k['note'], rect, WHITE))
                    white_positions.append(x)
                    x += white_key_width

            # 2) Add black keys positioned between white keys
            white_index = 0
            for k in keys_info:
                if k['is_black']:
                    if white_index == 0:
                        # no left white key available (shouldn't happen in this range)
                        continue
                    left_x = white_positions[white_index - 1]
                    rect_x = left_x + white_key_width - black_key_width // 2
                    rect = pygame.Rect(rect_x, KEYBOARD_TOP, black_key_width, black_key_height)
                    self.keys.append(PianoKey(k['note'], rect, BLACK))
                else:
                    white_index += 1

        else:
            # Legacy (octave-based) keyboard generation
            white_notes = ["C", "D", "E", "F", "G", "A", "B"]
            black_notes = {
                "C": "C#",
                "D": "D#",
                "F": "F#",
                "G": "G#",
                "A": "A#"
            }

            total_white = self.octaves * 7
            white_key_width = WIDTH // total_white
            black_key_width = int(white_key_width * 0.6)
            black_key_height = int(KEYBOARD_HEIGHT * 0.6)

            x = 0
            octave = self.start_octave

            # 1️⃣ Touches blanches
            for o in range(self.octaves):
                for note in white_notes:
                    rect = pygame.Rect(
                        x,
                        KEYBOARD_TOP,
                        white_key_width,
                        KEYBOARD_HEIGHT
                    )
                    self.keys.append(
                        PianoKey(f"{note}{octave}", rect, WHITE)
                    )
                    x += white_key_width
                octave += 1

            # 2️⃣ Touches noires (dessinées par-dessus)
            x = 0
            octave = self.start_octave

            for o in range(self.octaves):
                for note in white_notes:
                    if note in black_notes:
                        rect = pygame.Rect(
                            x + white_key_width - black_key_width // 2,
                            KEYBOARD_TOP,
                            black_key_width,
                            black_key_height
                        )
                        self.keys.append(
                            PianoKey(
                                f"{black_notes[note]}{octave}",
                                rect,
                                BLACK
                            )
                        )
                    x += white_key_width
                octave += 1

    def draw(self, screen, show_labels=False):
        # blanches d'abord
        for key in self.keys:
            if key.color == WHITE:
                key.draw(screen)
        # noires ensuite
        for key in self.keys:
            if key.color == BLACK:
                key.draw(screen)

        # labels optionnels
        if show_labels:
            for key in self.keys:
                # skip drawing labels on very narrow keys
                if key.rect.width < 24:
                    continue
                font_size = max(12, key.rect.width // 3)
                font = pygame.font.SysFont("arial", font_size, bold=True)
                color = BLACK if key.color == WHITE else WHITE
                label = font.render(key.note, True, color)
                label_rect = label.get_rect(center=(key.rect.centerx, key.rect.centery + 100))
                screen.blit(label, label_rect)

    def get_key_at_pos(self, pos):
        # priorité aux noires
        for key in self.keys:
            if key.color == BLACK and key.is_clicked(pos):
                return key
        for key in self.keys:
            if key.color == WHITE and key.is_clicked(pos):
                return key
        return None

    def draw_highlight(self, screen, note_name, thickness=4, color =GREEN):
        """Draw a highlight border around the key matching note_name."""
        # normalize note name: handle flats (B-, Bb) to sharps (A#, etc.)
        note_normalized = note_name.replace('-', 'b')
        FLAT_TO_SHARP = {
            'Bb': 'A#', 'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#',
            'Cb': 'B',  'Fb': 'E'
        }
        # extract note letter + octave, normalize flats
        i = len(note_normalized) - 1
        while i >= 0 and note_normalized[i].isdigit():
            i -= 1
        note_part = note_normalized[:i+1]
        octave_part = note_normalized[i+1:]
        if note_part in FLAT_TO_SHARP:
            note_part = FLAT_TO_SHARP[note_part]
        note_normalized = note_part + octave_part
        
        for key in self.keys:
            if key.note == note_normalized:
                pygame.draw.rect(screen, color, key.rect, thickness)
                # draw a second thinner white border for contrast
                pygame.draw.rect(screen, WHITE, key.rect.inflate(-4, -4), 2)
                break
