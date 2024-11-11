import asyncio
import curses
import time
from settings import Settings
from game import Game
from field import FieldCoordinates

game = Settings().create_game(active_cell=True)

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


async def main(current_game: Game) -> None:
    while True:
        # виводимо гру на екран
        stdscr.clear()
        current_game.show_for_terminal()
        # оцінюємо розміри екрану терміналу
        max_row, max_col = stdscr.getmaxyx()
        # обираємо найменші розміри для відображення - game.settings["screen"]["size_rows"]
        # і game.settings["screen"]["size_columns"] в порівнянні з розмірами вікна терміналу
        max_row = min(max_row, current_game.settings.screen['size_rows'])
        max_col = min(max_col, current_game.settings.screen['size_columns'])
        # виводимо гру на екран
        for row in range(max_row):
            for col in range(max_col):
                symbol = current_game.screen.get((row, col), " ")
                stdscr.addstr(row, col, symbol)
        stdscr.refresh()
        # перевірити чи гра закінчилась
        current_game = current_game.is_game_over()
        if not current_game.status:
            break
        # обробка клавіш
        try:
            key = stdscr.getch()
        except curses.error:
            continue

        # дивись https://docs.python.org/3/library/curses.html#curses.KEY_ENTER,
        # https://stackoverflow.com/questions/32252733/interpreting-enter-keypress-in-stdscr-curses-module-in-python
        if key == curses.KEY_ENTER or key == 10 or key == 13:
            #  встановити поточного гравця на позицію (тут же змінюється черга і виводяться відповідні повідомлення)
            current_game = current_game.add_player_to_field_position(current_game.active_cell)
            # змінити активну клітинку (стартова позиція)
            current_game.set_active_cell()
            continue
        elif key in directions:
            # переміщення активного осередку
            direction = directions[key]
            current_game.set_active_cell(
                position=FieldCoordinates(
                    current_game.active_cell.row + direction[0],
                    current_game.active_cell.column + direction[1]
                )
            )
            continue
        elif key == -1:
            pass
        else:
            # невірний введення
            current_game.add_message_to_game(
                'Допустимі клавіші: ↑, ↓, ←, → (переміщення активного осередку), Enter (обрати осередок).'
            )

        await asyncio.sleep(0.01)

    # треба щось надрукувати - гра закінчилась
    finish_message = f'  Гра закінчилась! Переможець: {current_game.players[0]}.  Для виходу натисніть ESC.  '
    while not stdscr.getch() == 27:
        stdscr.clear()
        max_row, max_col = stdscr.getmaxyx()
        stdscr.addstr(max_row // 2, (max_col - len(finish_message)) // 2, finish_message)
        current_game.show_for_terminal()
        stdscr.refresh()
        time.sleep(0.1)

    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()


if __name__ == "__main__":
    with asyncio.Runner() as runner:
        runner.run(main(game))
