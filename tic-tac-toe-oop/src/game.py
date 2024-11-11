import asyncio
from collections import ChainMap
from typing import NamedTuple, Self
from field import Field, FieldCoordinates
from player import Players, Player
from message import Message, Messages

ScreenCoordinates = NamedTuple('ScreenCoordinates', [('row', int), ('column', int)])
ScreenSymbol = str


class Game:
    def __init__(self, field: Field, players: Players, settings, messages: Messages, status, active_cell):
        self.field = field
        self.players = players
        self.settings = settings
        self.messages = messages
        self.status = status
        self.active_cell = active_cell
        self.screen = ChainMap({}, {}, {}, {})  # PlayersScreen, FieldScreen, MessagesScreen
        self._blink = None
        self._active_cell_screen = dict()

    def show_game(self) -> str:
        """На основі повернутих з get_messages_screen, get_field_screen і get_player_screen і сформованого GameScreen

        створює рядок, що відображає весь екран гри
        """
        self.get_messages_screen()
        self.get_field_screen()
        self.get_player_screen()
        # self.get_active_cell_screen()
        result = ''
        for row in range(self.settings.screen['size_rows']):
            for column in range(self.settings.screen['size_columns']):
                result += self.screen.get(ScreenCoordinates(row, column), ' ')
            result += '\n'
        return result

    def show_for_terminal(self) -> None:
        self.get_messages_screen()
        self.get_field_screen()
        self.get_player_screen()
        self.count_active_cell()
        if self._blink is None:
            self._blink = asyncio.create_task(self.blink_active_cell_screen())
            # await self._blink

    def get_messages_screen(self):
        """Для повідомлень які ще не відображувались (Message.status == False) створює словник,

        що описує відображення повідомлення на екрані - координати і символи
        всі координати позиціонуються в прямокутній області між upper_left_corner і lower_right_corner
        """

        upper_left_corner = ScreenCoordinates(
            self.settings.messages['left_up_row_position'],
            self.settings.messages['left_up_column_position'],
        )

        lower_right_corner = ScreenCoordinates(
            self.settings.messages['right_down_row_position'],
            self.settings.messages['right_down_column_position'],
        )

        height = lower_right_corner.row - upper_left_corner.row
        width = lower_right_corner.column - upper_left_corner.column
        messages = self.messages.get_unsent()
        # залишити лише текст повідомлень
        prepared_messages = messages.get_text(height, width)
        lst_prepared_messages = list(prepared_messages)
        screen = {}
        for row in range(upper_left_corner.row, lower_right_corner.row):
            for column in range(upper_left_corner.column, lower_right_corner.column):
                if lst_prepared_messages:
                    screen[ScreenCoordinates(row, column)] = ScreenSymbol(lst_prepared_messages.pop(0))
                else:
                    self.screen.maps[3].update(screen)

    def get_field_screen(self):

        upper_left_corner = ScreenCoordinates(
            self.settings.field['left_up_row_position'],
            self.settings.field['left_up_column_position'],
        )

        # визначаємо розміри поля в символах (рядки, стовпці, роздільники, розміри зображень гравців)
        result = {}
        # обрамлення поля
        max_row_player_symbols = self.settings.players['max_row_symbols']  # розмір ячейки по вертикалі
        max_col_player_symbols = self.settings.players['max_col_symbols']  # розмір ячейки по горизонталі
        # sumbols: "┏", "━", "┳", "┓", "┃", "┣", "┫", "┻", "┛", "┗", "╋"
        # точки перетину ліній: в рядках (max_row_player_symbols + 1) * range(settings["field"]["max_rows"] + 1))
        # в стовпцях (max_col_player_symbols + 1) * range(settings["field"]["max_columns"] + 1))
        # тобто для зображення гравця 1x1 і поля 3x3: (0, 2, 4, 6), (0, 2, 4, 6)
        # тобто для зображення гравця 2x2 і поля 3x3: (0, 3, 6, 9), (0, 3, 6, 9)
        # послідовність координат точок перетину для рядків:
        coordinates_of_intersections_rows = [
            upper_left_corner.row + coordinate * (max_row_player_symbols + 1)
            for coordinate in range(self.settings.field['size_rows'] + 1)
        ]
        # послідовність координат точок перетину для стовпців:
        coordinates_of_intersections_columns = [
            upper_left_corner.column + coordinate * (max_col_player_symbols + 1)
            for coordinate in range(self.settings.field['size_columns'] + 1)
        ]
        for row in range(
                upper_left_corner.row,
                self.settings.field['max_row_symbols'] + upper_left_corner.row,
        ):
            for col in range(
                    upper_left_corner.column,
                    self.settings.field['max_col_symbols'] + upper_left_corner.column,
            ):
                pass
                if (
                        row == coordinates_of_intersections_rows[0]
                        and col == coordinates_of_intersections_columns[0]
                ):
                    symbol = "┏"
                elif (
                        row == coordinates_of_intersections_rows[0]
                        and col == coordinates_of_intersections_columns[-1]
                ):
                    symbol = "┓"
                elif (
                        row == coordinates_of_intersections_rows[-1]
                        and col == coordinates_of_intersections_columns[0]
                ):
                    symbol = "┗"
                elif (
                        row == coordinates_of_intersections_rows[-1]
                        and col == coordinates_of_intersections_columns[-1]
                ):
                    symbol = "┛"
                elif (
                        row in coordinates_of_intersections_rows
                        and col not in coordinates_of_intersections_columns
                ):
                    symbol = "━"
                elif (
                        col in coordinates_of_intersections_columns
                        and row not in coordinates_of_intersections_rows
                ):
                    symbol = "┃"
                elif (
                        row == coordinates_of_intersections_rows[0]
                        and col in coordinates_of_intersections_columns[1:-1]
                ):
                    symbol = "┳"
                elif (
                        row == coordinates_of_intersections_rows[-1]
                        and col in coordinates_of_intersections_columns[1:-1]
                ):
                    symbol = "┻"
                elif (
                        col == coordinates_of_intersections_columns[0]
                        and row in coordinates_of_intersections_rows[1:-1]
                ):
                    symbol = "┣"
                elif (
                        col == coordinates_of_intersections_columns[-1]
                        and row in coordinates_of_intersections_rows[1:-1]
                ):
                    symbol = "┫"
                elif (
                        row in coordinates_of_intersections_rows[1:-1]
                        and col in coordinates_of_intersections_columns[1:-1]
                ):
                    symbol = "╋"
                else:
                    symbol = self.settings.field['empty']
                result[ScreenCoordinates(row, col)] = symbol
        self.screen.maps[2].update(result)

    def get_player_screen(self):
        """Створює словник, що описує відображення гравців на екрані - координати і символи

        всі координати позиціонуються відносно upper_left_corner (і далі відповідно розмірів зображень гравця)
        """
        field_upper_left_corner = ScreenCoordinates(
            self.settings.field['left_up_row_position'],
            self.settings.field['left_up_column_position'],
        )
        result = {}
        # ітеруватись по поточному полю, якщо на певних позиціях
        # є гравець - візуалізувати відповідно налаштувань
        for field_row in range(self.settings.field['size_rows']):
            for field_col in range(self.settings.field['size_columns']):
                if player := self.field[ScreenCoordinates(field_row, field_col)]:
                    player_rows = self.settings.players[player]['image'].split('\n')
                    for player_row_number, player_row in enumerate(player_rows):
                        for player_symbol_col_number, player_symbol in enumerate(
                                player_row
                        ):
                            row = (
                                    field_row * self.settings.players['max_row_symbols']
                                    + (field_row + 1)
                                    + field_upper_left_corner.row
                                    + player_row_number
                            )
                            col = (
                                    field_col * self.settings.players['max_col_symbols']
                                    + (field_col + 1)
                                    + field_upper_left_corner.column
                                    + player_symbol_col_number
                            )
                            result[ScreenCoordinates(row, col)] = player_symbol
        self.screen.maps[1].update(result)

    def count_active_cell(self):
        """Якщо активна клітина не None - додає її у відповідний словник у гру"""
        active_cell_screen = dict()
        if self.active_cell:
            # розмір осередку визначено в game.settings["player"]["max_row_player_symbols"] і max_col_player_symbols
            # лівий верхній кур поля - в атрибуті game.settings["field"]["left_up_row_position"] і
            # left_up_column_position
            left_up_corner_coordinates = ScreenCoordinates(
                self.settings.field['left_up_row_position']
                + self.active_cell.row * (self.settings.players['max_row_symbols'] + 1),
                self.settings.field['left_up_column_position']
                + self.active_cell.column
                * (self.settings.players['max_col_symbols'] + 1)
            )
            right_down_corner_coordinates = ScreenCoordinates(
                left_up_corner_coordinates.row
                + self.settings.players['max_row_symbols']
                + 1,
                left_up_corner_coordinates.column
                + self.settings.players['max_col_symbols']
                + 1
            )
            active_cell_screen[left_up_corner_coordinates] = self.settings.active_cell['left_up_corner_symbol']
            active_cell_screen[right_down_corner_coordinates] = self.settings.active_cell['right_down_corner_symbol']
            # правий верхній кут
            active_cell_screen[
                ScreenCoordinates(
                    left_up_corner_coordinates.row,
                    right_down_corner_coordinates.column
                )
            ] = self.settings.active_cell['right_up_corner_symbol']
            # лівий нижній кут
            active_cell_screen[
                ScreenCoordinates(
                    right_down_corner_coordinates.row,
                    left_up_corner_coordinates.column
                )] = self.settings.active_cell['left_down_corner_symbol']
            #  верхня горизонтальна лінія
            for column in range(
                    left_up_corner_coordinates.column + 1,
                    right_down_corner_coordinates.column
            ):
                active_cell_screen[
                    ScreenCoordinates(
                        left_up_corner_coordinates.row,
                        column
                    )
                ] = self.settings.active_cell['horizontal_symbol']
            #  нижня горизонтальна лінія
            for column in range(
                    left_up_corner_coordinates.column + 1,
                    right_down_corner_coordinates.column,
            ):
                active_cell_screen[
                    ScreenCoordinates(
                        right_down_corner_coordinates.row,
                        column
                    )
                ] = self.settings.active_cell['horizontal_symbol']
            #  ліва вертикальна лінія
            for row in range(
                    left_up_corner_coordinates.row + 1,
                    right_down_corner_coordinates.row
            ):
                active_cell_screen[
                    ScreenCoordinates(
                        row,
                        left_up_corner_coordinates.column
                    )
                ] = self.settings.active_cell['vertical_symbol']
            # права вертикальна лінія
            for row in range(
                    left_up_corner_coordinates.row + 1,
                    right_down_corner_coordinates.row
            ):
                active_cell_screen[
                    ScreenCoordinates(
                        row,
                        right_down_corner_coordinates.column
                    )
                ] = self.settings.active_cell['vertical_symbol']

        self._active_cell_screen = active_cell_screen

    async def blink_active_cell_screen(self):
        while True:
            self.screen.maps[0] = self._active_cell_screen
            await asyncio.sleep(0.05)
            self.screen.maps[0].clear()
            await asyncio.sleep(0.05)

    @staticmethod
    def is_empty_cells(current_field: Field) -> bool:
        # Повертає True якщо в полі є пусті клітинки, інакше False.
        return any(value is None for value in current_field.values())

    @staticmethod
    def is_n_symbols_continuously(cells: list[Player | None], n: int) -> None | Player:
        # Повертає символ, якщо в списку є n символів підряд, інакше None.

        # + 1 лише якщо попередній символ дорівнює поточному (counter, figure, previous_figure)
        # якщо попередній не дорівнює поточному, то знову починаємо з 1 (counter, figure, previous_figure)
        # якщо символа немає, то знову починаємо з 0 ()
        # на кожному циклі перевіряємо, чи кількість символів дорівнює n (тоді стоп і повертаємо символ
        # що створив переможну комбінацію)
        counter = 0
        previous_figure = None
        for figure in cells:
            if figure is None:
                counter = 0
                previous_figure = None
                continue
            elif previous_figure != figure:
                counter = 1
                previous_figure = figure
                continue
            else:
                counter += 1

            if counter == n:
                return previous_figure

    def is_game_over(self) -> Self:
        """Повертає екземпляр Game, в якому:
         - в атрибуті status - True продовжується гра, False - гра закінчилась
         - в атрибуті messages - список повідомлень про переможця або нічию.

        гра закінчується коли:
        - неможливі подальші ходи (всі клітинки зайняті і не сформовано виграшної комбінації)
        - для якогось з гравців сформовано виграшну комбінацію

        При закінченні гри додає в messages повідомлення про переможця або нічию і змінює статус гри на False.
        """
        # створити копію гри - працюємо з копією і потім, після змін, повертаємо її (так як це кортеж - неважливо,
        # ми нічого не змінимо)

        # перевірити що є вільні клітини
        if not self.is_empty_cells(self.field):
            self.add_message_to_game('Всі клітинки зайняті. Нічия!')
            self.status = False

            return self
        # перевірити виграшні комбінації в рядках (відкидаємо рядки менші за довжину виграшної)
        for row in range(self.settings.field['size_rows']):
            cells = [
                self.field[FieldCoordinates(row, column)]
                for column in range(self.settings.field['size_columns'])
                if self.settings.field['win_rows'] <= self.settings.field['size_columns']
            ]
            if winner := self.is_n_symbols_continuously(cells, self.settings.field['win_rows']):
                self.add_message_to_game(f'Переміг {winner}!')
                self.status = False

                return self
        # перевірити виграшні комбінації в колонках (відкидаємо колонки менші за довжину виграшної)
        for column in range(self.settings.field['size_columns']):
            cells = [
                self.field[FieldCoordinates(row, column)]
                for row in range(self.settings.field['size_rows'])
                if self.settings.field['win_rows'] <= self.settings.field['size_rows']
            ]
            if winner := self.is_n_symbols_continuously(cells, self.settings.field['win_columns']):
                self.add_message_to_game(f'Переміг {winner}!')
                self.status = False

                return self
        # перевірити виграшні комбінації в правих діагоналях (перша половина)
        for row in range(
                0,
                self.settings.field['size_rows']
                - (self.settings.field['win_diagonals'] - 1),
        ):
            cells = []
            c = 0
            for r in range(row, self.settings.field['size_rows']):
                cells.append(self.field[FieldCoordinates(r, c)])
                c += 1
            if winner := self.is_n_symbols_continuously(cells, self.settings.field['win_columns']):
                self.add_message_to_game(f'Переміг {winner}!')
                self.status = False

                return self
        # 'друга частина' правих діагоналей
        for column in range(
                1,
                self.settings.field['size_columns']
                - (self.settings.field['win_diagonals'] - 1),
        ):
            cells = []
            r = 0
            for c in range(column, self.settings.field['size_columns']):
                cells.append(self.field[FieldCoordinates(r, c)])
                r += 1
            if winner := self.is_n_symbols_continuously(cells, self.settings.field['win_columns']):
                self.add_message_to_game(f'Переміг {winner}!')
                self.status = False

                return self

        # перевірити виграшні комбінації в лівих діагоналях (перша половина)
        for column in range(
                self.settings.field['win_diagonals'] - 1,
                self.settings.field['size_columns']
        ):
            cells = []
            r = 0
            for c in range(column, -1, -1):
                cells.append(self.field[FieldCoordinates(r, c)])
                r += 1
            if winner := self.is_n_symbols_continuously(cells, self.settings.field['win_columns']):
                self.add_message_to_game(f'Переміг {winner}!')
                self.status = False

                return self

        # 'друга частина' лівих діагоналей
        for row in range(
                1,
                self.settings.field['size_rows']
                - (self.settings.field['win_diagonals'] - 1)
        ):
            cells = []
            c = self.settings.field['size_columns'] - 1
            for r in range(row, self.settings.field['size_rows']):
                cells.append(self.field[FieldCoordinates(r, c)])
                c -= 1
            if winner := self.is_n_symbols_continuously(cells, self.settings.field['win_columns']):
                self.add_message_to_game(f'Переміг {winner}!')
                self.status = False

                return self

        return self

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
            f"очікую вводу позиції від гравця {player_name}."
            f" Введіть рядок (0 ... {self.settings.field['size_rows'] - 1}) "
            f"та стовпець (0 ... {self.settings.field['size_columns'] - 1}) через пробіл",
            end=": ",
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
                    0 <= position.row < self.settings.field["size_rows"]
                    and 0 <= position.column < self.settings.field["size_columns"]
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

    def close_blink(self):
        if self._blink:
            self._blink.close()
