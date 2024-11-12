from screen import Screen
from typing import NamedTuple, Self
from field import Field, FieldCoordinates
from player import Players, Player
from message import Message, Messages

ScreenCoordinates = NamedTuple('ScreenCoordinates', [('row', int), ('column', int)])
ScreenSymbol = str


class Game:
    def __init__(self, field: Field, players: Players, settings, messages: Messages, status,
                 active_cell: FieldCoordinates | None):
        self.field = field
        self.players = players
        self.settings = settings
        self.messages = messages
        self.status = status
        self.active_cell = active_cell
        self.screen = Screen(settings)

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
        await self.screen.blink_active_cell_screen()

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

    def is_game_running(self) -> bool:
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

            return self.status
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

                return self.status
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

                return self.status
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

                return self.status
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

                return self.status

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

                return self.status

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

                return self.status

        return self.status

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

    def close_blink(self):
        if self._blink:
            self._blink.close()
