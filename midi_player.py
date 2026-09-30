# midi_player.py
import pygame
import pygame.midi
from music import note_to_midi

class MidiPlayer:
    def __init__(self):
        pygame.midi.init()
        self.output = None
        default_id = pygame.midi.get_default_output_id()
        if default_id != -1:
            try:
                self.output = pygame.midi.Output(default_id)
            except Exception:
                self.output = None

        # If no default, search for the first output-capable device
        if self.output is None:
            count = pygame.midi.get_count()
            for i in range(count):
                info = pygame.midi.get_device_info(i)
                # info: (interf, name, is_input, is_output, opened)
                is_output = info[3]
                if is_output:
                    try:
                        self.output = pygame.midi.Output(i)
                        break
                    except Exception:
                        continue

        if self.output is None:
            print("[MidiPlayer] No MIDI output device found. MIDI disabled.")

        # active notes: midi -> (off_time_ms, channel)
        self.active = {}

    def play_note(self, note_name, duration_ms=500, velocity=127, channel=0):
        """Play a MIDI note (note_name like 'C4'). Note will be turned off after duration_ms."""
        if self.output is None:
            return
        midi = note_to_midi(note_name)
        try:
            self.output.note_on(midi, velocity, channel)
        except Exception:
            return
        off_time = pygame.time.get_ticks() + duration_ms
        self.active[midi] = (off_time, channel)

    def update(self):
        """Call each frame to send note_off events when due."""
        if self.output is None:
            return
        now = pygame.time.get_ticks()
        to_off = [m for m, (t, ch) in self.active.items() if t <= now]
        for m in to_off:
            off_time, ch = self.active.pop(m)
            try:
                self.output.note_off(m, 0, ch)
            except Exception:
                pass

    def close(self):
        if self.output:
            # turn off any lingering notes
            for m, (_, ch) in list(self.active.items()):
                try:
                    self.output.note_off(m, 0, ch)
                except Exception:
                    pass
            try:
                self.output.close()
            except Exception:
                pass
        try:
            pygame.midi.quit()
        except Exception:
            pass
