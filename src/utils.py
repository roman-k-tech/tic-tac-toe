import curses
import os

stdscr = curses.initscr()
curses.start_color()
curses.noecho()
curses.cbreak()
stdscr.nodelay(True)
curses.use_default_colors()
curses.init_pair(1, curses.COLOR_RED, -1)
curses.init_pair(2, curses.COLOR_GREEN, -1)
curses.init_pair(3, curses.COLOR_YELLOW, -1)
curses.init_pair(4, curses.COLOR_BLUE, -1)
curses.init_pair(5, curses.COLOR_MAGENTA, -1)
curses.init_pair(6, curses.COLOR_CYAN, -1)
curses.init_pair(7, curses.COLOR_WHITE, -1)
stdscr.keypad(True)

#  створюємо словник для керування переміщеннями активного осередку
directions = {
    curses.KEY_UP: (-1, 0),
    curses.KEY_DOWN: (1, 0),
    curses.KEY_LEFT: (0, -1),
    curses.KEY_RIGHT: (0, 1)
}


def clear_terminal_screen() -> None:
    """Очищає термінал"""

    os.system('cls' if os.name == 'nt' else 'clear')
