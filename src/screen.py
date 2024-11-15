import asyncio
from collections import ChainMap
from typing import NamedTuple
from message import Messages
from field import Field, FieldCoordinates

ScreenCoordinates = NamedTuple('ScreenCoordinates', [('row', int), ('column', int)])
ScreenSymbol = str


class Screen(ChainMap):

    def __init__(self, settings):
        self.active_cell_scr = dict()
        self.player_scr = dict()
        self.field_scr = dict()
        self.messages_scr = dict()
        super().__init__(self.active_cell_scr, self.player_scr, self.field_scr, self.messages_scr)

        self.settings = settings
        self._active_cell_scr = dict()
        self.printed = False

    def get_messages_screen(self, messages: Messages):
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
        messages = messages.get_unsent()
        # залишити лише текст повідомлень
        prepared_messages = messages.get_text(height, width)
        lst_prepared_messages = list(prepared_messages)
        screen = {}
        for row in range(upper_left_corner.row, lower_right_corner.row):
            for column in range(upper_left_corner.column, lower_right_corner.column):
                if lst_prepared_messages:
                    screen[ScreenCoordinates(row, column)] = ScreenSymbol(lst_prepared_messages.pop(0))
                else:
                    self.messages_scr.update(screen)

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

        self.field_scr.update(result)

    def get_player_screen(self, field: Field):
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
                if player := field[ScreenCoordinates(field_row, field_col)]:
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
        self.player_scr.update(result)

    def count_active_cell(self, active_cell: FieldCoordinates):
        active_cell_screen = dict()
        # розмір осередку визначено в game.settings["player"]["max_row_player_symbols"] і max_col_player_symbols
        # лівий верхній кур поля - в атрибуті game.settings["field"]["left_up_row_position"] і
        # left_up_column_position
        left_up_corner_coordinates = ScreenCoordinates(
            self.settings.field['left_up_row_position']
            + active_cell.row * (self.settings.players['max_row_symbols'] + 1),
            self.settings.field['left_up_column_position']
            + active_cell.column
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

        self._active_cell_scr = active_cell_screen

    async def blink_active_cell_screen(self):
        self.maps[0] = self._active_cell_scr
        await asyncio.sleep(0.05)
        self.maps[0].clear()
        await asyncio.sleep(0.05)
