import os


def clear_terminal_screen() -> None:
    """Очищає термінал"""

    os.system('cls' if os.name == 'nt' else 'clear')
