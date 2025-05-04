import time
import random
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
from machine import Pin # Use Pin directly

# --- Display Setup ---
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, rotate=0)
WIDTH, HEIGHT = display.get_bounds()

# --- Button Setup ---
# Pico Display 2.0 buttons are on GP12, GP13, GP14, GP15 (A, B, X, Y)
button_a = Pin(12, Pin.IN, Pin.PULL_UP) # Start Game
button_x = Pin(14, Pin.IN, Pin.PULL_UP) # Exit Game (Double Click)
button_b = Pin(13, Pin.IN, Pin.PULL_UP) # Left
button_y = Pin(15, Pin.IN, Pin.PULL_UP) # Right

# --- Game Constants ---
PADDLE_WIDTH = 60
PADDLE_HEIGHT = 10
PADDLE_SPEED = 10
BALL_RADIUS = 5
BRICK_WIDTH = 30
BRICK_HEIGHT = 10
BRICK_ROWS = 5
BRICK_COLS = WIDTH // (BRICK_WIDTH + 2) # Fit bricks with 2px gap
BRICK_TOP_OFFSET = 20 # Space bricks down from the top
BRICK_COLORS = [
    display.create_pen(255, 0, 0),    # Red
    display.create_pen(255, 165, 0),  # Orange
    display.create_pen(255, 255, 0),  # Yellow
    display.create_pen(0, 255, 0),    # Green
    display.create_pen(0, 0, 255)     # Blue
]
BACKGROUND_COLOR = display.create_pen(0, 0, 0)
PADDLE_COLOR = display.create_pen(200, 200, 200)
BALL_COLOR = display.create_pen(255, 255, 255)
SCORE_COLOR = display.create_pen(255, 255, 255)
TEXT_COLOR = display.create_pen(255, 255, 255)

# --- Game Variables ---
paddle_x = (WIDTH - PADDLE_WIDTH) // 2
paddle_y = HEIGHT - PADDLE_HEIGHT - 5

ball_x = WIDTH // 2
ball_y = HEIGHT // 2
ball_dx = 0 # Initial speed 0 until game starts
ball_dy = 0 # Initial speed 0 until game starts

bricks = []
score = 0
lives = 10

# Game States: START, PLAYING, GAME_OVER, WIN (Removed PAUSED)
game_state = "START"

# --- Double Click Exit Logic Variables ---
last_x_press_time = 0
x_click_state = "IDLE" # States: IDLE, FIRST_PRESS, WAITING_FOR_SECOND
DOUBLE_CLICK_INTERVAL_MS = 300 # Milliseconds for double click detection

# --- Helper Functions ---
def create_bricks():
    """Creates the grid of bricks."""
    global bricks
    bricks = []
    for r in range(BRICK_ROWS):
        for c in range(BRICK_COLS):
            brick_x = c * (BRICK_WIDTH + 2) + 1 # +1 for gap start
            brick_y = r * (BRICK_HEIGHT + 2) + BRICK_TOP_OFFSET + 1
            color_index = r % len(BRICK_COLORS)
            bricks.append({
                "x": brick_x,
                "y": brick_y,
                "w": BRICK_WIDTH,
                "h": BRICK_HEIGHT,
                "color": BRICK_COLORS[color_index],
                "active": True
            })

def draw_paddle():
    """Draws the paddle."""
    display.set_pen(PADDLE_COLOR)
    display.rectangle(paddle_x, paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT)

def draw_ball():
    """Draws the ball."""
    display.set_pen(BALL_COLOR)
    display.circle(int(ball_x), int(ball_y), BALL_RADIUS)

def draw_bricks():
    """Draws the active bricks."""
    for brick in bricks:
        if brick["active"]:
            display.set_pen(brick["color"])
            display.rectangle(brick["x"], brick["y"], brick["w"], brick["h"])

def draw_score_lives():
    """Draws the score and lives."""
    display.set_pen(SCORE_COLOR)
    display.text(f"Poäng: {score}", 10, 5, scale=2)
    display.text(f"Liv: {lives}", WIDTH - 90, 5, scale=2)

def move_paddle():
    """Moves the paddle based on button input."""
    global paddle_x
    if button_b.value() == 0: # Move left (Check value directly)
        paddle_x -= PADDLE_SPEED
        if paddle_x < 0:
            paddle_x = 0
    if button_y.value() == 0: # Move right (Check value directly)
        paddle_x += PADDLE_SPEED
        if paddle_x > WIDTH - PADDLE_WIDTH:
            paddle_x = WIDTH - PADDLE_WIDTH

def move_ball():
    """Moves the ball and handles wall collisions."""
    global ball_x, ball_y, ball_dx, ball_dy, lives, game_state # Added game_state

    ball_x += ball_dx
    ball_y += ball_dy

    # Wall collisions
    if ball_x - BALL_RADIUS < 0 or ball_x + BALL_RADIUS > WIDTH:
        ball_dx *= -1
        ball_x = max(BALL_RADIUS, min(ball_x, WIDTH - BALL_RADIUS)) # Prevent sticking
    if ball_y - BALL_RADIUS < 0:
        ball_dy *= -1
        ball_y = BALL_RADIUS # Prevent sticking
    
    # Bottom wall collision (lose life)
    if ball_y + BALL_RADIUS > HEIGHT:
        lives -= 1
        if lives > 0:
            # Reset ball position and speed
            ball_x = WIDTH // 2
            ball_y = HEIGHT // 2
            ball_dx = random.choice([-4, 4]) # Use updated speed on reset
            ball_dy = -4                     # Use updated speed on reset
            time.sleep(0.5) # Shorter pause before restarting ball
        else:
            # Game Over
            game_state = "GAME_OVER" # Change state instead of handling directly


def check_collisions():
    """Checks for collisions between ball, paddle, and bricks."""
    global ball_x, ball_y, ball_dx, ball_dy, score

    # Paddle collision
    if (paddle_y < ball_y + BALL_RADIUS < paddle_y + PADDLE_HEIGHT and
            paddle_x < ball_x < paddle_x + PADDLE_WIDTH):
        ball_dy *= -1
        ball_y = paddle_y - BALL_RADIUS # Move ball slightly above paddle
        
        # Optional: Change horizontal direction based on where it hits paddle
        hit_pos = (ball_x - (paddle_x + PADDLE_WIDTH / 2)) / (PADDLE_WIDTH / 2)
        ball_dx = hit_pos * 4 # Adjust speed/angle based on hit position (-1 to 1) * factor (updated speed)

    # Brick collisions
    for brick in bricks:
        if brick["active"]:
            # Check if ball's bounding box intersects brick's bounding box
            if (brick["x"] < ball_x + BALL_RADIUS and
                brick["x"] + brick["w"] > ball_x - BALL_RADIUS and
                brick["y"] < ball_y + BALL_RADIUS and
                brick["y"] + brick["h"] > ball_y - BALL_RADIUS):

                brick["active"] = False
                score += 10

                # Determine collision side to reverse correct direction
                # Simple approach: reverse vertical direction mostly
                # More complex logic could check which side was hit
                
                # Calculate overlap on each axis
                overlap_x = min(ball_x + BALL_RADIUS - brick["x"], brick["x"] + brick["w"] - (ball_x - BALL_RADIUS))
                overlap_y = min(ball_y + BALL_RADIUS - brick["y"], brick["y"] + brick["h"] - (ball_y - BALL_RADIUS))

                # Reverse direction based on smaller overlap (likely impact direction)
                if overlap_x < overlap_y:
                     ball_dx *= -1
                     # Nudge ball out horizontally
                     if ball_x < brick["x"] + brick["w"] / 2:
                         ball_x = brick["x"] - BALL_RADIUS
                     else:
                         ball_x = brick["x"] + brick["w"] + BALL_RADIUS
                else:
                     ball_dy *= -1
                     # Nudge ball out vertically
                     if ball_y < brick["y"] + brick["h"] / 2:
                         ball_y = brick["y"] - BALL_RADIUS
                     else:
                         ball_y = brick["y"] + brick["h"] + BALL_RADIUS
                
                break # Only handle one brick collision per frame

    # Check for win condition (moved from main loop)
    active_bricks = sum(1 for brick in bricks if brick["active"])
    if active_bricks == 0:
        global game_state
        game_state = "WIN"

def start_screen():
    """Displays the start screen."""
    display.set_pen(BACKGROUND_COLOR)
    display.clear()
    display.set_pen(TEXT_COLOR)
    # Adjust x-coordinates for left alignment with some padding
    display.text("TA BORT KLOSSAR", 10, HEIGHT // 2 - 40, scale=3)
    display.text("Tryck A för att Starta", 10, HEIGHT // 2 + 10, scale=2)
    display.update()

def game_over_screen():
    display.set_pen(BACKGROUND_COLOR)
    display.clear()
    display.set_pen(TEXT_COLOR) # Use TEXT_COLOR
    display.text("GAME OVER", WIDTH // 2 - 80, HEIGHT // 2 - 20, scale=3)
    display.text(f"Poäng: {score}", WIDTH // 2 - 70, HEIGHT // 2 + 20, scale=2)
    display.update()
    time.sleep(3) # Shorter wait

def win_screen():
    display.set_pen(BACKGROUND_COLOR)
    display.clear()
    display.set_pen(TEXT_COLOR) # Use TEXT_COLOR
    display.text("DU VANN!", WIDTH // 2 - 60, HEIGHT // 2 - 20, scale=3)
    display.text(f"Poäng: {score}", WIDTH // 2 - 70, HEIGHT // 2 + 20, scale=2)
    display.update()
    time.sleep(3) # Shorter wait

def reset_game():
    """Resets game variables for a new game."""
    global score, lives, paddle_x, ball_x, ball_y, ball_dx, ball_dy, bricks
    score = 0
    lives = 10
    create_bricks()
    paddle_x = (WIDTH - PADDLE_WIDTH) // 2
    ball_x = WIDTH // 2
    ball_y = HEIGHT // 2
    # Give a slight delay before ball moves
    ball_dx = 0
    ball_dy = 0
    # Draw initial state before ball moves
    display.set_pen(BACKGROUND_COLOR)
    display.clear()
    draw_paddle()
    draw_ball()
    draw_bricks()
    draw_score_lives()
    display.update()
    time.sleep(0.5)
    # Now set the ball speed
    ball_dx = random.choice([-4, 4])
    ball_dy = -4

# --- Main Game Loop ---
while True:
    current_time_ms = time.ticks_ms() # Get current time once per loop
    x_pressed = button_x.value() == 0 # Read button state once (check value)

    # --- Double Click Exit Check (Replaces old logic) ---
    # --- This logic runs first ---
    if game_state != "START": # Only allow exit during play/game over/win states
        if x_click_state == "IDLE":
            if x_pressed:
                x_click_state = "FIRST_PRESS"
                last_x_press_time = current_time_ms
                # print("X State: -> FIRST_PRESS") # Debug

        elif x_click_state == "FIRST_PRESS":
            if not x_pressed: # Released after first press
                # Check if release happened quickly enough to be part of a potential double click
                if time.ticks_diff(current_time_ms, last_x_press_time) < DOUBLE_CLICK_INTERVAL_MS:
                    x_click_state = "WAITING_FOR_SECOND"
                    # Keep last_x_press_time from the *start* of the first press
                    # print("X State: -> WAITING_FOR_SECOND") # Debug
                else: # Released too late, reset
                    x_click_state = "IDLE"
                    # print("X State: FIRST_PRESS -> IDLE (Timeout on release)") # Debug
            elif time.ticks_diff(current_time_ms, last_x_press_time) >= DOUBLE_CLICK_INTERVAL_MS:
                 # Held too long, reset even if still pressed
                 x_click_state = "IDLE"
                 # print("X State: FIRST_PRESS -> IDLE (Held too long)") # Debug

        elif x_click_state == "WAITING_FOR_SECOND":
            if x_pressed: # Second press detected
                 # Check if the second press happened quickly enough after the *start* of the first press
                 if time.ticks_diff(current_time_ms, last_x_press_time) < DOUBLE_CLICK_INTERVAL_MS:
                     # Double click successful!
                     print("X Double Click: Exiting game!")
                     break # Exit the main while loop
                 else: # Second press too late, treat this as a new first press
                     x_click_state = "FIRST_PRESS"
                     last_x_press_time = current_time_ms
                     # print("X State: WAITING_FOR_SECOND -> FIRST_PRESS (Second press too late)") # Debug
            elif time.ticks_diff(current_time_ms, last_x_press_time) >= DOUBLE_CLICK_INTERVAL_MS:
                 # Timeout waiting for second press after the first release
                 x_click_state = "IDLE"
                 # print("X State: WAITING_FOR_SECOND -> IDLE (Timeout waiting)") # Debug

    # Reset exit state if game goes back to START screen or finishes
    # This prevents accidental exit if clicks span across state changes
    if game_state == "START" and x_click_state != "IDLE":
         x_click_state = "IDLE"
         # print(f"X State: Resetting to IDLE due to game state change to START") # Debug


    # --- Game State Logic ---
    if game_state == "START":
        start_screen()
        if button_a.value() == 0:
            reset_game()
            game_state = "PLAYING"

    elif game_state == "PLAYING":
        # --- Input ---
        move_paddle()

        # --- Logic ---
        move_ball()       # This might change game_state to GAME_OVER
        if game_state == "PLAYING": # Check if move_ball changed the state
            check_collisions() # This might change game_state to WIN

        # --- Drawing ---
        display.set_pen(BACKGROUND_COLOR)
        display.clear()
        draw_paddle()
        draw_ball()
        draw_bricks()
        draw_score_lives()

        # --- Update Display ---
        display.update()

    elif game_state == "GAME_OVER":
        game_over_screen()
        game_state = "START" # Go back to start screen

    elif game_state == "WIN":
        win_screen()
        game_state = "START" # Go back to start screen

    # --- Frame Limiter ---
    if game_state == "PLAYING":
        time.sleep(0.01) # Adjust for game speed
    else:
        time.sleep(0.05)

# --- End of Game Loop ---
print("Breakout game loop finished.")
# Cleanup if needed (main.py handles GC)
display.set_pen(BACKGROUND_COLOR)
display.clear()
display.update()
