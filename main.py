import time
import picographics
from machine import Pin
import sys
import gc # Make sure garbage collector is imported

print("--- Starting main.py ---")

# --- Display Setup ---
try:
    BACKLIGHT_PIN = 20
    display = picographics.PicoGraphics(display=picographics.DISPLAY_PICO_DISPLAY_2)
    WIDTH, HEIGHT = display.get_bounds()
    print(f"Display initialized ({WIDTH}x{HEIGHT})")
    backlight = Pin(BACKLIGHT_PIN, Pin.OUT)
    backlight.value(1)
    print("Backlight ON")
    # --- Initial Display Test ---
    WHITE_PEN_TEST = display.create_pen(255, 255, 255) # Removed GREEN_PEN definition
    display.set_pen(WHITE_PEN_TEST) # Use WHITE_PEN_TEST directly
    display.clear() # Clear with white initially
    display.text("Display OK", 10, 10, scale=3); display.update()
    print("Initial display test shown.")
    time.sleep(1) # Shorter pause is fine
except Exception as e:
    print("!!! ERROR DURING DISPLAY INITIALIZATION !!!")
    sys.print_exception(e)
    led = Pin("LED", Pin.OUT);
    while True: led.toggle(); time.sleep(0.1)

# --- Button Setup ---
try:
    button_a = Pin(12, Pin.IN, Pin.PULL_UP) # SELECT
    button_b = Pin(13, Pin.IN, Pin.PULL_UP) # UP
    button_y = Pin(15, Pin.IN, Pin.PULL_UP) # DOWN
    print("Buttons initialized")
except Exception as e: print("!!! ERROR DURING BUTTON INITIALIZATION !!!"); sys.print_exception(e)

# --- Pen Colors ---
try:
    BLACK = display.create_pen(0, 0, 0); WHITE = display.create_pen(255, 255, 255)
    CYAN = display.create_pen(0, 255, 255); MAGENTA = display.create_pen(255, 0, 255)
    YELLOW = display.create_pen(255, 255, 0); GREEN = display.create_pen(0, 255, 0)
    RED = display.create_pen(255, 0, 0)
    PURPLE = display.create_pen(128, 0, 128) # Added Purple
    print("Pens created")
except Exception as e: print("!!! ERROR CREATING PENS !!!"); sys.print_exception(e)

# --- Menu Configuration ---
# !!! IMPORTANT: Replace filenames with your actual game files !!!
games = [
    { "name": "Stjärnfångare", "file": "star_catcher.py" }, # Avoid special chars in name for safety
    { "name": "Ta bort klossar", "file": "breakout.py" }, # <<< CHANGE THIS FILENAME
]
selected_index = 0
menu_title = "Välj Spel" # Avoid special chars

# --- Initial Display Test ---
try:
    print("Starting blinking display test...")
    start_time = time.ticks_ms()
    blink_duration_ms = 2000 # Blink for 2 seconds
    blink_interval_ms = 250 # Blink speed
    use_magenta = True
    WHITE_PEN_TEST = display.create_pen(255, 255, 255) # Ensure white is defined here

    while time.ticks_diff(time.ticks_ms(), start_time) < blink_duration_ms:
        if use_magenta:
            display.set_pen(MAGENTA)
        else:
            display.set_pen(PURPLE)
        display.clear()
        display.set_pen(WHITE_PEN_TEST)
        display.text("Display OK", 10, 10, scale=3)
        display.update()
        use_magenta = not use_magenta # Toggle color
        time.sleep_ms(blink_interval_ms)

    print("Blinking display test finished.")
    # Clear screen before proceeding
    display.set_pen(BLACK)
    display.clear()
    display.update()

except Exception as e:
    print("!!! ERROR DURING DISPLAY INITIALIZATION !!!")
    sys.print_exception(e)
    led = Pin("LED", Pin.OUT);
    while True: led.toggle(); time.sleep(0.1)

# --- Menu Functions ---
def draw_menu():
    try:
        display.set_pen(BLACK); display.clear()
        # Title
        display.set_pen(CYAN); title_scale = 3
        title_width = display.measure_text(menu_title, scale=title_scale)
        display.text(menu_title, (WIDTH - title_width) // 2, 10, scale=title_scale)
        # Items
        item_scale = 2; item_height = 8 * item_scale; start_y = 45; padding = 8
        for i, game in enumerate(games):
            y_pos = start_y + i * (item_height + padding)
            if y_pos > HEIGHT - 20: break
            if i == selected_index:
                display.set_pen(YELLOW)
                display.rectangle(5, y_pos - padding // 2, WIDTH - 10, item_height + padding)
                display.set_pen(BLACK)
                display.text("> " + game["name"], 15, y_pos, scale=item_scale)
            else:
                display.set_pen(WHITE)
                display.text("  " + game["name"], 15, y_pos, scale=item_scale)
        # Instructions
        display.set_pen(GREEN); instr_scale = 2; instr_text = "B=Upp, Y=Ner, A=Starta spel"
        instr_width = display.measure_text(instr_text, scale=instr_scale)
        display.text(instr_text, (WIDTH - instr_width) // 2, HEIGHT - (8 * instr_scale) - 5, scale=instr_scale)
        display.update()
    except Exception as e:
        print("!!! ERROR IN draw_menu !!!"); sys.print_exception(e)
        try: # Try showing error on screen
            display.set_pen(BLACK); display.clear(); display.set_pen(RED)
            display.text("Draw Menu Err!", 10, 10, scale=2); display.update()
        except: pass

# --- MODIFIED FUNCTION ---
def launch_game(filename):
    print(f"Attempting to launch: {filename}")
    display.set_pen(BLACK); display.clear()
    display.set_pen(WHITE); display.text(f"Startar...", 10, HEIGHT // 2 - 8, scale=2)
    display.update()
    time.sleep(0.5)

    # Create a new, empty dictionary for the game's execution scope
    game_globals = {}
    game_locals = game_globals # Often locals can be same as globals for simple exec

    # --- Explicit Memory Management ---
    print("--- Running GC before launch ---")
    gc.collect()
    print(f"Memory free before launch: {gc.mem_free()}")
    # --- End Memory Management ---

    try:
        print(f"Opening {filename}")
        with open(filename, "r") as f:
            game_code = f.read()
            print(f"Read {len(game_code)} bytes. Executing...")
            # Execute the code within the dedicated scope
            exec(game_code, game_globals, game_locals)
            print(f"Execution finished normally for {filename}")

    except FileNotFoundError:
        print(f"!!! ERROR: File not found: {filename}")
        display.set_pen(BLACK); display.clear(); display.set_pen(RED)
        display.text("FEL: Fil saknas", 10, 30, scale=2); # File Missing
        display_filename = filename if len(filename) < 25 else filename[:22] + "..."
        display.text(display_filename, 10, 60, scale=2)
        display.set_pen(WHITE); display.text("Tryck A", 10, 90, scale=2)
        display.update()
        while button_a.value() == 1: time.sleep(0.1)

    except MemoryError as e:
        print(f"!!! MEMORY ERROR launching/running {filename} !!!"); sys.print_exception(e)
        display.set_pen(BLACK); display.clear(); display.set_pen(RED)
        display.text("FEL: Minnesfel!", 10, 30, scale=2); # Memory Error
        display.set_pen(WHITE); display.text("Tryck A", 10, 90, scale=2)
        display.update()
        while button_a.value() == 1: time.sleep(0.1)

    except Exception as e:
        print(f"!!! ERROR DURING GAME EXECUTION ({filename}) !!!"); sys.print_exception(e)
        display.set_pen(BLACK); display.clear(); display.set_pen(RED)
        display.text("FEL i spel:", 10, 30, scale=2); # Error in game
        display_filename = filename if len(filename) < 25 else filename[:22] + "..."
        display.text(display_filename, 10, 60, scale=2)
        display.set_pen(WHITE); display.text("Tryck A", 10, 90, scale=2)
        display.update()
        while button_a.value() == 1: time.sleep(0.1)

    finally:
        # --- Explicit Memory Cleanup ---
        print("--- Cleaning up game scope and running GC ---")
        # Clear the dictionaries used for the game's scope
        game_globals.clear()
        game_locals.clear()
        # Run garbage collection
        gc.collect()
        print(f"Memory free after cleanup: {gc.mem_free()}")
        # --- End Memory Cleanup ---
        time.sleep(0.5) # Delay before redrawing menu

# --- Main Loop ---
print("Drawing initial menu...")
draw_menu()
print("Entering main loop...")

while True:
    try:
        up_pressed = button_b.value() == 0
        down_pressed = button_y.value() == 0
        select_pressed = button_a.value() == 0

        if up_pressed:
            # print("Input: UP") # Optional debug
            selected_index = (selected_index - 1) % len(games)
            draw_menu()
            time.sleep(0.2) # Debounce

        elif down_pressed:
            # print("Input: DOWN") # Optional debug
            selected_index = (selected_index + 1) % len(games)
            draw_menu()
            time.sleep(0.2) # Debounce

        elif select_pressed:
            print(f"Input: SELECT (Index: {selected_index})")
            selected_game = games[selected_index]
            launch_game(selected_game["file"])
            # Execution continues here AFTER launch_game finishes and cleanup runs
            print("Returned from launch_game. Redrawing menu.")
            draw_menu() # Redraw menu immediately after returning

        if not (up_pressed or down_pressed or select_pressed):
             time.sleep(0.05)

    except Exception as e:
        print("!!! UNHANDLED ERROR IN MAIN LOOP !!!"); sys.print_exception(e)
        try: # Attempt to display a critical error message
            display.set_pen(BLACK); display.clear(); display.set_pen(RED)
            display.text("Critical Err!", 10, 10, scale=2); display.text("Check REPL", 10, 40, scale=2)
            display.update()
        except: pass
        time.sleep(5)
