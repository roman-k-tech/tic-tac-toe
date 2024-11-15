from typing import NamedTuple
from player import Player
from message import Message, Messages

FieldCoordinates = NamedTuple('FieldCoordinates', [('row', int), ('column', int)])


class Field(dict[FieldCoordinates]):
    def __init__(self, *args, settings, messages: Messages):
        super().__init__(*args)
        self.settings = settings
        self.messages = messages
        self.status = True

    def is_empty_cells(self) -> bool:
        # Повертає True якщо в полі є пусті клітинки, інакше False.
        return any(value is None for value in self.values())

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
        if not self.is_empty_cells():
            self.add_message_to_game('Всі клітинки зайняті. Нічия!')
            self.status = False

            return self.status
        # перевірити виграшні комбінації в рядках (відкидаємо рядки менші за довжину виграшної)
        for row in range(self.settings.field['size_rows']):
            cells = [
                self[FieldCoordinates(row, column)]
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
                self[FieldCoordinates(row, column)]
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
                cells.append(self[FieldCoordinates(r, c)])
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
                cells.append(self[FieldCoordinates(r, c)])
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
                cells.append(self[FieldCoordinates(r, c)])
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
                cells.append(self[FieldCoordinates(r, c)])
                c -= 1
            if winner := self.is_n_symbols_continuously(cells, self.settings.field['win_columns']):
                self.add_message_to_game(f'Переміг {winner}!')
                self.status = False

                return self.status

        return self.status

    def add_message_to_game(self, message: str) -> None:
        """Додати повідомлення до гри"""
        self.messages.append(Message(message, False))

