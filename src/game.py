import asyncio
import curses
import time
from screen import Screen
from typing import NamedTuple, Self
from field import Field, FieldCoordinates
from player import Players
from message import Message, Messages
from utils import stdscr, directions

ScreenCoordinates = NamedTuple('ScreenCoordinates', [('row', int), ('column', int)])
ScreenSymbol = str


class Game:
    def __init__(self, field: Field, players: Players, settings, messages: Messages,
                 active_cell: FieldCoordinates | None):
        self.field = field
        self.players = players
        self.settings = settings
        self.messages = messages
        self.active_cell = active_cell
        self.screen = Screen(settings)
        self.stdscr = curses.initscr()

    def show_game(self) -> str:
        """На основі повернутих з get_messages_screen, get_field_screen і get_player_screen і сформованого GameScreen

        створює рядок, що відображає весь екран гри
        """
        self.screen.get_messages_screen(self.messages)
        self.screen.get_field_screen()
        self.screen.get_player_screen(self.field)
        # self.get_active_cell_screen()
        result = ''
        for row in range(self.settings.screen['size_rows']):
            for column in range(self.settings.screen['size_columns']):
                result += self.screen.get(ScreenCoordinates(row, column), ' ')
            result += '\n'
        return result

    def show_for_terminal(self) -> None:
        self.screen.get_messages_screen(self.messages)
        self.screen.get_field_screen()
        self.screen.get_player_screen(self.field)
        self.screen.count_active_cell(self.active_cell)

    async def blink_active_cell_screen(self):
        while self.field.status:
            await self.screen.blink_active_cell_screen()

    async def is_game_running(self):
        while self.field.is_game_running():
            await asyncio.sleep(0.01)

    async def run_game(self):
        async with asyncio.TaskGroup() as tasks:
            tasks.create_task(self.is_game_running())
            tasks.create_task(self.blink_active_cell_screen())
            tasks.create_task(self.redraw_screen())
            tasks.create_task(self.get_input())

    def input_next_position(self) -> FieldCoordinates | str:
        """очікує від гравця введення позиції на полі гри

        перевіряє що:
        - введені дані можуть бути конвертовані в цілі числа
        - введені дані в межах розмірів поля

        друкує підказку для гравця, що має ввести позицію

        - якщо всі перевірки пройдено - повертає координати клітинки
        - якщо якась перевірка не пройдена - повертає повідомлення про помилку
        """
        player_name = self.settings.players[self.players[0]]['name']
        print(
            f'очікую вводу позиції від гравця {player_name}.'
            f' Введіть рядок (0 ... {self.settings.field['size_rows'] - 1}) '
            f'та стовпець (0 ... {self.settings.field['size_columns'] - 1}) через пробіл',
            end=': '
        )
        input_str = input()
        try:
            row, column = map(int, input_str.split())
            if row in range(
                    self.settings.field['size_rows']
            ) and column in range(self.settings.field['size_columns']):
                return FieldCoordinates(row, column)
            else:
                return "Позиція виходить за межі поля"
        except ValueError:
            return "Введені дані не можуть бути конвертовані в цілі числа"

    def add_player_to_field_position(self, position: FieldCoordinates) -> Self:
        """Додає гравця, що є на черзі (current_game.players[0]), на позицію position в полі гри.

        - у випадку, якщо клітина вільна:
            - додає гравця на позицію position в полі гри (current_game.field)
            - формує відповідне повідомлення про вдалий хід гравця (current_game.messages)
            - змінює чергу гравців (current_game.players)
            - формує повідомлення про хід наступного гравця (current_game.messages)
            - повертає оновлений екземпляр гри
        - у випадку, якщо клітина зайнята:
            - формує відповідне повідомлення про невдалий хід гравця (current_game.messages) і
            необхідність переходити
            - поверає оновлений екземпляр гри
        """
        player = self.players[0]
        if self.field[position] is None:
            self.field[position] = player
            self.add_message_to_game(f'Гравець {player} зробив хід')
            self.players.rotate()
            self.add_message_to_game(f'Гравець {self.players[0]} наступний')
        else:
            self.add_message_to_game('Ця клітинка зайнята. Спробуйте ще раз')

        return self

    def set_active_cell(self, position: FieldCoordinates | None = None) -> None:
        """Встановлює активну клітинку на полі гри.

        - якщо position не передано, то встановлює активну клітинку на позицію
        (settings["field"][size_rows] // 2, settings["field"][size_columns] // 2)
        - якщо position передано, то перевіряє що позиція в межах поля, і якщо так то
        встановлює активну клітинку на позицію position, якщо ні - то залишається попередня позиція
        """

        if position is None:
            #  якщо позиція не передана - встановлюємо активну клітинку на центр поля
            active_cell = FieldCoordinates(
                self.settings.field['size_rows'] // 2,
                self.settings.field['size_columns'] // 2
            )
        else:
            #  перевіряємо - чи запропонована для встановлення позиція - в межах поля?
            if (
                    0 <= position.row < self.settings.field['size_rows']
                    and 0 <= position.column < self.settings.field['size_columns']
            ):
                #  якщо так - встановлюємо активну клітинку на позицію position
                active_cell = position
            else:
                #  якщо ні - залишаємо попередню позицію і додаємо повідомлення про помилку
                self.add_message_to_game('Позиція не може виходити за межі поля.')
                active_cell = self.active_cell

        self.active_cell = active_cell

    def add_message_to_game(self, message: str) -> None:
        """Додати повідомлення до гри"""
        self.messages.append(Message(message, False))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        finish_message = f'  Гра закінчилась! Переможець: {self.players[0]}.  Для виходу натисніть ESC.  '
        while not stdscr.getch() == 27:
            stdscr.clear()
            max_row, max_col = stdscr.getmaxyx()
            stdscr.addstr(max_row // 2, (max_col - len(finish_message)) // 2, finish_message)
            self.show_for_terminal()
            stdscr.refresh()
            time.sleep(0.1)

        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    async def redraw_screen(self):
        while True:
            if not self.field.status:
                await asyncio.sleep(0.2)
                break
            # виводимо гру на екран
            stdscr.clear()
            self.show_for_terminal()
            # оцінюємо розміри екрану терміналу
            max_row, max_col = stdscr.getmaxyx()
            # обираємо найменші розміри для відображення - game.settings["screen"]["size_rows"]
            # і game.settings["screen"]["size_columns"] в порівнянні з розмірами вікна терміналу
            max_row = min(max_row, self.settings.screen['size_rows'])
            max_col = min(max_col, self.settings.screen['size_columns'])
            # виводимо гру на екран
            for row in range(max_row):
                for col in range(max_col):
                    symbol = self.screen.get((row, col), ' ')
                    stdscr.addstr(row, col, symbol)
            stdscr.refresh()
            await asyncio.sleep(0.01)

        await asyncio.sleep(1)

    async def get_input(self):
        while self.field.status:

            try:
                key = stdscr.getch()
            except curses.error:
                continue

            if key == curses.KEY_ENTER or key == 10 or key == 13:
                #  встановити поточного гравця на позицію (тут же змінюється черга і виводяться відповідні повідомлення)
                current_game = self.add_player_to_field_position(self.active_cell)
                # змінити активну клітинку (стартова позиція)
                current_game.set_active_cell()
                continue
            elif key in directions:
                # переміщення активного осередку
                direction = directions[key]
                self.set_active_cell(
                    position=FieldCoordinates(
                        self.active_cell.row + direction[0],
                        self.active_cell.column + direction[1]
                    )
                )
                continue
            elif key == -1:
                pass
            else:
                # невірний введення
                self.add_message_to_game(
                    'Допустимі клавіші: ↑, ↓, ←, → (переміщення активного осередку), Enter (обрати осередок).'
                )

            await asyncio.sleep(0.01)
