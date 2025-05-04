import time
import random
import picographics
from machine import Pin, SPI

# --- Display Setup ---
BACKLIGHT_PIN = 20
display = picographics.PicoGraphics(display=picographics.DISPLAY_PICO_DISPLAY_2)
WIDTH, HEIGHT = display.get_bounds()

# --- Manual Backlight Control ---
backlight = Pin(BACKLIGHT_PIN, Pin.OUT)
backlight.value(1)

# --- Button Setup ---
button_a = Pin(12, Pin.IN, Pin.PULL_UP) # START / RESTART to Title
button_b = Pin(13, Pin.IN, Pin.PULL_UP) # LEFT
button_x = Pin(14, Pin.IN, Pin.PULL_UP) # Added for exit
button_y = Pin(15, Pin.IN, Pin.PULL_UP) # RIGHT

# --- Pen Colors ---
BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
GREY = display.create_pen(150, 150, 150)
YELLOW = display.create_pen(255, 255, 0)
RED = display.create_pen(255, 0, 0)
ORANGE = display.create_pen(255, 165, 0)
CYAN = display.create_pen(0, 255, 255)

# --- Game Constants ---
PLAYER_WIDTH = 20
PLAYER_HEIGHT = 15
PLAYER_START_Y_GLOBAL = HEIGHT - PLAYER_HEIGHT - 5
PLAYER_SPEED = 7

STAR_SIZE = 8
STARS_PER_LEVEL = 5
MAX_LIVES = 3
STARS_PER_LIFE = 15

SPAWN_AREA_WIDTH_FACTOR = 0.60
spawn_area_width = int(WIDTH * SPAWN_AREA_WIDTH_FACTOR)
min_spawn_x = (WIDTH - spawn_area_width) // 2
max_spawn_x = min_spawn_x + spawn_area_width
min_spawn_x = max(STAR_SIZE // 2, min_spawn_x)
max_spawn_x = min(WIDTH - STAR_SIZE // 2, max_spawn_x)

MIN_HORIZONTAL_SEPARATION = STAR_SIZE * 3
MIN_VERTICAL_START_SEPARATION = STAR_SIZE * 2

# --- Game States ---
STATE_TITLE = "title"
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"

# --- Game Variables ---
player_x = 0
score = 0
level = 0
game_speed = 0
stars_collected_this_level = 0
stars = []
lives = 0
missed_stars_count = 0
game_state = STATE_TITLE
last_star_time = 0
initial_star_interval = 2200
star_interval_reduction_per_level = 25
star_interval = 0

# --- Double Click Exit Logic Variables ---
last_x_press_time = 0
x_pressed_waiting_for_second = False
DOUBLE_CLICK_INTERVAL_MS = 300

def reset_game():
    global player_x, score, level, game_speed, stars_collected_this_level
    global stars, lives, missed_stars_count, game_state, last_star_time, star_interval
    player_x = WIDTH // 2 - PLAYER_WIDTH // 2
    score = 0
    level = 1
    game_speed = 1
    stars_collected_this_level = 0
    stars = []
    lives = MAX_LIVES
    missed_stars_count = 0
    last_star_time = time.ticks_ms()
    star_interval = initial_star_interval
    print("Spelet återställt! Hastighet låst till 1.")

def draw_player(x, y_base):
    center_x = x + PLAYER_WIDTH // 2
    top_y = y_base
    bottom_y = y_base + PLAYER_HEIGHT
    p1_x, p1_y = center_x, top_y
    p2_x, p2_y = x, bottom_y
    p3_x, p3_y = x + PLAYER_WIDTH, bottom_y
    display.set_pen(WHITE)
    display.triangle(p1_x, p1_y, p2_x, p2_y, p3_x, p3_y)
    engine_height = 5
    engine_width = PLAYER_WIDTH // 3
    engine_x_left = center_x - engine_width // 2
    engine_y = bottom_y
    flare_p1_x, flare_p1_y = engine_x_left, engine_y
    flare_p2_x, flare_p2_y = engine_x_left + engine_width, engine_y
    flare_p3_x, flare_p3_y = center_x, engine_y + engine_height
    display.set_pen(ORANGE)
    display.triangle(flare_p1_x, flare_p1_y, flare_p2_x, flare_p2_y, flare_p3_x, flare_p3_y)

def add_star():
    spawn_attempts = 10
    best_star_x = -1
    start_y = 0 - STAR_SIZE
    for sx, sy in stars:
        if sy < MIN_VERTICAL_START_SEPARATION:
            return
    if max_spawn_x <= min_spawn_x:
        fallback_min = max(STAR_SIZE // 2, WIDTH // 4)
        fallback_max = min(WIDTH - STAR_SIZE // 2, WIDTH * 3 // 4)
        if fallback_max > fallback_min: best_star_x = random.randint(fallback_min, fallback_max)
        else: best_star_x = WIDTH // 2
        stars.append([best_star_x, start_y])
        return
    for attempt in range(spawn_attempts):
        potential_star_x = random.randint(min_spawn_x, max_spawn_x)
        too_close_horizontally = False
        proximity_check_depth = STAR_SIZE * 5
        for sx, sy in stars:
            if sy < proximity_check_depth:
                if abs(potential_star_x - sx) < MIN_HORIZONTAL_SEPARATION:
                    too_close_horizontally = True
                    break
        if not too_close_horizontally:
            best_star_x = potential_star_x
            break
    if best_star_x == -1:
         best_star_x = random.randint(min_spawn_x, max_spawn_x)
    stars.append([best_star_x, start_y])

def move_stars():
    global stars, lives, missed_stars_count
    new_stars = []
    life_lost_this_frame = False
    for star in stars:
        star[1] += game_speed
        if star[1] >= HEIGHT:
            missed_stars_count += 1
            if missed_stars_count >= STARS_PER_LIFE:
                lives -= 1
                missed_stars_count = 0
                life_lost_this_frame = True
                print(f"Liv förlorat! Liv kvar: {lives}")
        elif star[1] < HEIGHT + STAR_SIZE:
             new_stars.append(star)
    stars = new_stars
    return life_lost_this_frame

def draw_stars():
    display.set_pen(YELLOW)
    for star_x, star_y in stars:
        if star_y > -STAR_SIZE:
             display.circle(star_x, star_y, STAR_SIZE // 2)

def check_collisions():
    global score, stars_collected_this_level, stars, level, game_speed
    player_rect_left = player_x
    player_rect_right = player_x + PLAYER_WIDTH
    player_rect_top = PLAYER_START_Y_GLOBAL
    player_rect_bottom = PLAYER_START_Y_GLOBAL + PLAYER_HEIGHT
    remaining_stars = []
    collided_this_frame = False
    for star_x, star_y in stars:
        star_half_size = STAR_SIZE // 2
        star_rect_left = star_x - star_half_size
        star_rect_right = star_x + star_half_size
        star_rect_top = star_y - star_half_size
        star_rect_bottom = star_y + star_half_size
        if (player_rect_left < star_rect_right and
            player_rect_right > star_rect_left and
            player_rect_top < star_rect_bottom and
            player_rect_bottom > star_rect_top):
            if not collided_this_frame:
                score += 10 * level
                stars_collected_this_level += 1
                collided_this_frame = True
                if stars_collected_this_level >= STARS_PER_LEVEL:
                    level += 1
                    stars_collected_this_level = 0
                    print(f"Ny nivå! Nådde nivå {level}, Hastighet: {game_speed}")
        else:
            remaining_stars.append([star_x, star_y])
    stars = remaining_stars

def draw_ui():
    score_text = f"Poäng: {score}"
    level_text = f"Nivå: {level}"
    display.set_pen(WHITE)
    text_scale = 2
    font_height = 8
    padding = 5
    score_width = display.measure_text(score_text, scale=text_scale)
    level_width = display.measure_text(level_text, scale=text_scale)
    display.text(score_text, WIDTH - score_width - padding, padding, scale=text_scale)
    display.text(level_text, WIDTH - level_width - padding, padding + (font_height * text_scale) + padding // 2, scale=text_scale)
    life_line_height = 10
    life_line_width = 3
    life_spacing = 6
    lives_y = padding
    display.set_pen(RED)
    for i in range(lives):
        line_x = padding + (i * (life_line_width + life_spacing))
        display.rectangle(line_x, lives_y, life_line_width, life_line_height)
    miss_text = f"Miss: {missed_stars_count}/{STARS_PER_LIFE}"
    miss_text_y = lives_y + life_line_height + padding
    display.set_pen(WHITE)
    display.text(miss_text, padding, miss_text_y, scale=text_scale)

def draw_game_over():
    display.set_pen(RED)
    game_over_text = "SPELET SLUT"
    score_text = f"Slutpoäng: {score}"
    restart_text = "Tryck A för Titel"
    text_scale_large = 4
    text_scale_medium = 2
    go_width = display.measure_text(game_over_text, scale=text_scale_large)
    score_width = display.measure_text(score_text, scale=text_scale_medium)
    restart_width = display.measure_text(restart_text, scale=text_scale_medium)
    go_x = (WIDTH - go_width) // 2
    go_y = HEIGHT // 2 - (8 * text_scale_large)
    score_x = (WIDTH - score_width) // 2
    score_y = go_y + (8 * text_scale_large) + 10
    restart_x = (WIDTH - restart_width) // 2
    restart_y = score_y + (8 * text_scale_medium) + 10
    display.text(game_over_text, go_x, go_y, scale=text_scale_large)
    display.set_pen(WHITE)
    display.text(score_text, score_x, score_y, scale=text_scale_medium)
    display.text(restart_text, restart_x, restart_y, scale=text_scale_medium)

def draw_title_screen():
    display.set_pen(CYAN)
    title_text = "Stjärnfångare"
    start_text = "Tryck A för att Starta"
    text_scale_title = 4
    text_scale_start = 2

    title_width = display.measure_text(title_text, scale=text_scale_title)
    start_width = display.measure_text(start_text, scale=text_scale_start)
    base_title_x = (WIDTH - title_width) // 2
    title_y = HEIGHT // 3

    center_offset = 3
    title_x = base_title_x + center_offset

    start_x = (WIDTH - start_width) // 2
    start_y = title_y + (8 * text_scale_title) + 30

    display.text(title_text, title_x, title_y, scale=text_scale_title)
    display.set_pen(YELLOW)
    display.text(start_text, start_x, start_y, scale=text_scale_start)

    title_ship_x = WIDTH // 2 - PLAYER_WIDTH // 2
    title_ship_y = start_y + (8 * text_scale_start) + 20
    draw_player(title_ship_x, title_ship_y)

while True:
    current_time_ms = time.ticks_ms()

    if game_state == STATE_PLAYING or game_state == STATE_GAME_OVER:
        if button_x.value() == 0:
            if not x_pressed_waiting_for_second:
                last_x_press_time = current_time_ms
                x_pressed_waiting_for_second = True
        else:
            if x_pressed_waiting_for_second:
                if time.ticks_diff(current_time_ms, last_x_press_time) < DOUBLE_CLICK_INTERVAL_MS:
                    pass
                else:
                    x_pressed_waiting_for_second = False

        if x_pressed_waiting_for_second and button_x.value() == 0:
             if time.ticks_diff(current_time_ms, last_x_press_time) < DOUBLE_CLICK_INTERVAL_MS:
                 print("X Double Click: Exiting game!")
                 break
             else:
                 last_x_press_time = current_time_ms

    if x_pressed_waiting_for_second and button_x.value() == 1:
        if time.ticks_diff(current_time_ms, last_x_press_time) >= DOUBLE_CLICK_INTERVAL_MS:
             x_pressed_waiting_for_second = False

    if game_state == STATE_TITLE:
        if button_a.value() == 0:
            print("Startar spel!")
            reset_game()
            game_state = STATE_PLAYING
            time.sleep(0.2)
            continue
        display.set_pen(BLACK)
        display.clear()
        draw_title_screen()

    elif game_state == STATE_PLAYING:
        if button_b.value() == 0: player_x -= PLAYER_SPEED
        if button_y.value() == 0: player_x += PLAYER_SPEED
        player_x = max(0, min(player_x, WIDTH - PLAYER_WIDTH))

        life_lost_event = move_stars()
        if life_lost_event and lives <= 0:
            game_state = STATE_GAME_OVER
            print("Spelet slut!")
            time.sleep(0.2)
            continue
        check_collisions()

        star_interval = max(200, initial_star_interval - (level * star_interval_reduction_per_level))
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_star_time) > star_interval:
            add_star()
            last_star_time = current_time

        display.set_pen(BLACK)
        display.clear()
        draw_player(player_x, PLAYER_START_Y_GLOBAL)
        draw_stars()
        draw_ui()

    elif game_state == STATE_GAME_OVER:
        if button_a.value() == 0:
            print("Återgår till titelskärm")
            game_state = STATE_TITLE
            x_pressed_waiting_for_second = False
            time.sleep(0.2)
            continue
        display.set_pen(BLACK)
        display.clear()
        draw_game_over()

    display.update()

    time.sleep(0.02)

print("Star Catcher game loop finished.")
display.set_pen(BLACK)
display.clear()
display.update()