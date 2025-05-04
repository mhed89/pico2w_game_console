# Pico 2W Game Console

A simple game console framework for the Raspberry Pi Pico 2 W (RP2350) with a Pico Display 2.0.

## Games Included

*   **Stjärnfångare (Star Catcher):** Catch falling stars with your spaceship.
*   **Ta bort klossar (Breakout):** A classic brick-breaking game.

## How to Run

1.  Ensure you have MicroPython installed on your Raspberry Pi Pico 2 W. **Note:** This project is designed for the **Raspberry Pi Pico 2 W (RP2350)** and requires the specific Pimoroni MicroPython UF2 file for this board and the Pico Display 2.0.
2.  Upload `main.py`, `star_catcher.py`, and `breakout.py` to the root directory of your Pico 2 W.
3.  The `main.py` script will run automatically on boot, presenting the game menu.

## Controls

### Main Menu (`main.py`)

*   **Button B:** Move selection UP
*   **Button Y:** Move selection DOWN
*   **Button A:** Select and launch game

### Stjärnfångare (`star_catcher.py`)

*   **Button B:** Move spaceship LEFT
*   **Button Y:** Move spaceship RIGHT
*   **Button A:** Start game / Return to Title Screen (from Game Over)
*   **Button X (Double Click):** Exit game and return to main menu

### Ta bort klossar (`breakout.py`)

*   **Button B:** Move paddle LEFT
*   **Button Y:** Move paddle RIGHT
*   **Button A:** Start game (from title screen)
*   **Button X (Double Click):** Exit game and return to main menu

## Memory Handling

The `main.py` script includes basic memory management to improve stability when switching between games:

*   **Garbage Collection:** The `gc` module is used to run the garbage collector (`gc.collect()`) before launching a game and after it exits. This helps reclaim memory that is no longer in use.
*   **Isolated Execution Scope:** Each game is executed using `exec()` within its own dictionary scope. These dictionaries are cleared after the game finishes, helping to release the memory associated with the game's code and variables.
*   **Monitoring:** `main.py` prints the available memory (`gc.mem_free()`) before and after running a game to help diagnose potential memory issues.
