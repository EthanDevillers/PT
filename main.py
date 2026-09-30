#main.py
import pygame
import os
from config import *
from staff import Staff
from keyboard import Keyboard
from game import Game
from midi_player import MidiPlayer
from ui import UIButton, UIDropdown
from music import note_to_midi, midi_to_note

# INIT
pygame.init()
flags = pygame.NOFRAME if BORDERLESS_WINDOW else 0
screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
pygame.display.set_caption("Piano Trainer")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 20)
Bold_font = pygame.font.SysFont("arial", 24, bold=True)
# Background
try:
    bg = pygame.image.load("assets/Wallpaper2.jpg").convert()
    bg = pygame.transform.smoothscale(bg, (WIDTH, HEIGHT))
except Exception:
    bg = None
# PIANO / STAFF / GAME
staff = Staff()
keyboard = Keyboard(full_piano=True)

print("=== DEBUG NOTES ===")
for k in keyboard.keys[:24]:
    print(k.note)

game = Game()
midi = MidiPlayer()
# Mode & UI
show_labels = False
correction_mode = False
toggle_rect = pygame.Rect(20, 20, 36, 28)
# Sidebar
sidebar_open = False
sidebar_x, sidebar_y = 10, 10
sidebar_w = 320
sidebar_pad = 12
ctrl_x = sidebar_x + sidebar_pad
ctrl_w = sidebar_w - sidebar_pad * 2
# Partitions
partitions_dir = "partitions"
partitions = sorted([f for f in os.listdir(partitions_dir) if f.endswith(".json")]) if os.path.isdir(partitions_dir) else []
selected_partition = partitions[0] if partitions else None
partition_dropdown_open = False
# Feedback
last_feedback = ""
last_feedback_time = 0
FEEDBACK_MS = 1500
streak = 0
best_streak = 0 
# =========================
# CALLBACKS
# =========================
def toggle_correction():
    global correction_mode
    correction_mode = not correction_mode

def toggle_labels():
    global show_labels
    show_labels = not show_labels

def  GameMode_Select():
    if game.mode == "game":
        game.mode = "partition"
        load_partition()
    else:
        game.mode = "game"
        game.partition = None
        game.current_note = game.new_note()

    buttons[2].set_label(f"Mode :{game.mode}")

def load_partition():
    global last_feedback, last_feedback_time
    if selected_partition:
        if game.load_partition(os.path.join(partitions_dir, selected_partition)):
            last_feedback = f"Chargé {selected_partition}"
        else:
            last_feedback = "Erreur chargement"
        last_feedback_time = pygame.time.get_ticks()

def reset_game():
    game.score = 0
    game.mode = "game"
    game.current_note = game.new_note()
    global last_feedback, last_feedback_time
    last_feedback = "Réinitialisé"
    last_feedback_time = pygame.time.get_ticks()

def select_partition(name):
    global selected_partition
    selected_partition = name
    load_partition()
def toggle_sidebar():
    global sidebar_open
    sidebar_open = not sidebar_open

# =========================
# UI ELEMENTS
# =========================

#Side bar toggle button sans fond
toggle_button = UIButton((ctrl_x, 20, 80, 32), "Menu", Bold_font, toggle_sidebar,with_background=False,show_border_when_no_bg=True,underline_on_hover=False)

buttons = []
y_start = sidebar_y + 16 + 40
buttons.append(UIButton((ctrl_x, y_start, ctrl_w, 32), "Mode correction", font, toggle_correction))
buttons.append(UIButton((ctrl_x, y_start + 40, ctrl_w, 32), "Afficher notes", font, toggle_labels))
buttons.append(UIButton((ctrl_x, y_start + 80, ctrl_w, 32), f"Mode {game.mode}", font, GameMode_Select))
buttons.append(UIButton((ctrl_x, y_start + 950, ctrl_w, 32), "Réinitialiser", font, reset_game))
dropdown = UIDropdown((ctrl_x, y_start + 120, ctrl_w, 32),options=partitions if partitions else ["Aucune partition"], font=font, on_select=select_partition)

# =========================
# MAIN LOOP
# =========================

running = True
# MAIN LOOP
while running:
    clock.tick(FPS)
    # Background
    if bg:
        screen.blit(bg, (0, 0))
    else:
        screen.fill(GRAY)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        handle_event = toggle_button.handle_event(event)
        if handle_event:
            continue
        # Sidebar buttons
        if sidebar_open:
            for btn in buttons:
                if btn.handle_event(event):
                    break  # un clic ne peut activer qu'un bouton

            # Dropdown
            if dropdown.handle_event(event):
                pass  # sélection gérée via callback
        selected_notes = []
        # Piano
        if event.type == pygame.MOUSEBUTTONDOWN:
            key = keyboard.get_key_at_pos(event.pos)
            if key:
                midi.play_note(key.note)
                correct = game.check_note(key.note)
                    # scoring only in non-correction mode: increment streak on successive corrects, reset on any error
                if not correction_mode:
                    if correct:
                        streak += 1
                        if streak > best_streak:
                            best_streak = streak
                    else:
                        streak = 0
                    # feedback to show briefly on screen
                last_feedback = "Correct!" if correct else f"Played {key.note}"
                last_feedback_time = pygame.time.get_ticks()

        # Exit
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    # =========================
    # DESSIN
    # =========================
    staff.draw(screen)
    if game.mode == "partition" and game.partition:
        visible_measures = game.get_visible_measures(staff)
        cursor_x = staff.get_cursor_x(game.partition, game.visible_start)
        if cursor_x:    
            staff.draw_play_cursor(screen, cursor_x)
        staff.draw_partition(screen, game.partition, visible_measures)

        # Draw partition name at top center
        partition_name = selected_partition if selected_partition else "Aucune"
        label_text = f"Partition : {partition_name}"
        label = font.render(label_text, True, BLACK)
        pygame.draw.rect(screen, WHITE, (WIDTH/2 - label.get_width()/2 - 10,  20, label.get_width() + 20, label.get_height() +20 ))
        pygame.draw.rect(screen, BLACK, (WIDTH/2 - label.get_width()/2 - 10,  20, label.get_width() + 20, label.get_height() +20 ), 2)
        screen.blit(label, (WIDTH/2 - label.get_width()/2, 30))
    else:
        staff.draw_note(screen, game.current_note, x=WIDTH/2)

    keyboard.draw(screen, show_labels)

    toggle_button.draw(screen)
    if game.mode == "partition" and game.partition:
        if correction_mode:
            for note in game.current_notes:
                keyboard.draw_highlight(screen, note.name)  
        for midi_value in game.notes_played:
            note_name = midi_to_note(midi_value)
            keyboard.draw_highlight(screen, note_name, color=RED)


    elif game.mode == "game":
        if correction_mode:
            keyboard.draw_highlight(screen, game.current_note.name)


    # Sidebar panel
    if sidebar_open:
        panel = pygame.Rect(sidebar_x, sidebar_y, sidebar_w, HEIGHT - sidebar_y - 20)
        pygame.draw.rect(screen, (240, 240, 240), panel, border_radius=20)
        pygame.draw.rect(screen, BLACK, panel, 2, border_radius=20)
        toggle_button.draw(screen)
        for btn in buttons:
            btn.draw(screen)
        dropdown.draw(screen)

    # Feedback
    now  = pygame.time.get_ticks()
    if now - last_feedback_time < FEEDBACK_MS and last_feedback:
        fb = Bold_font.render(last_feedback, True, RED if last_feedback != "Correct!" else GREEN)
        screen.blit(fb, (WIDTH - (fb.get_width()+30), KEYBOARD_TOP - 40))
    # draw current streak (non-correction mode) and best streak
    streak_text = Bold_font.render(f"Streak: {streak}", True, BLACK)
    best_text = Bold_font.render(f"Best: {best_streak}", True, BLACK)
    screen.blit(best_text, (WIDTH - (best_text.get_width()+60), 40))
    screen.blit(streak_text, (WIDTH - (streak_text.get_width()+60), 68))

    midi.update()
    pygame.display.flip()

midi.close()
pygame.quit()
