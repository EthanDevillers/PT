# config.py
WIDTH, HEIGHT = 1920, 1080
FPS = 60
BORDERLESS_WINDOW = True

STAFF_TOP = 200
STAFF_HEIGHT = 200
STAFF_LINE_SPACING = 20  # distance between staff lines (pixels)
STAFF_GAP = 100  # vertical gap between treble and bass staves (pixels)

KEYBOARD_HEIGHT = 250
KEYBOARD_BOTTOM_MARGIN = 100  # pixels from bottom
KEYBOARD_TOP = HEIGHT - KEYBOARD_HEIGHT - KEYBOARD_BOTTOM_MARGIN

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 200, 0)
RED = (200, 0, 0)

MIDI_START = 21   # A0
MIDI_END = 108    # C8
START_END_WIDTH = 20
PIXELS_PER_BEAT = 20