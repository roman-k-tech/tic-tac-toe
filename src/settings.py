import random
import tomllib
from collections import deque
from pathlib import Path
from field import Field, FieldCoordinates
from player import Players
from game import Game
from message import Messages, Message

TOML_FILE = (Path(__file__).parent.parent / 'settings.toml').resolve()


class Settings:

    def __init__(self, path: Path = TOML_FILE):
        self._settings_file = path
        self.players = {}
        self.field = {}
        self.screen = {}
        self.messages = None
        self.active_cell = None
        self.symbols = None
        self.restrictions = {}

        self._read_settings()
        self._check_player_symbols_and_max_field_size()

    def _read_settings(self):
        with open(self._settings_file, 'rb') as f:
            options = tomllib.load(f)

        for key, value in options.items():
            setattr(self, key, value)

    def _check_player_symbols_and_max_field_size(self):
        """Перевіряє:
        - що розміри поля в символах не перевищують максимальні можливі значення (з урахуванням ліній,
        розмірів зображень гравців)

        Генерую виключення ValueError з відповідним повідомленням, якщо перевірка не пройшла.

        Якщо перевірка пройшла - додає в налаштування розміри поля в символах в розділ
        settings["field"]["max_row_symbols"], settings["field"]["max_col_symbols"]
        і розміри зображень гравців в розділ
        settings["players"]["max_row_symbols"], settings["players"]["max_col_symbols"]
        """

        # визначаємо максимальну висоту і ширину зображень гравців
        max_row_player_symbols = 0
        max_col_player_symbols = 0
        for player in self.players.values():
            rows = player['image'].split('\n')
            max_row_player_symbols = (
                len(rows) if len(rows) > max_row_player_symbols else max_row_player_symbols
            )
            max_col_in_row = max([len(row) for row in rows])
            max_col_player_symbols = (
                max_col_in_row
                if max_col_in_row > max_col_player_symbols
                else max_col_player_symbols
            )
        #  визначаємо максимальну висоту і ширину поля в символах (тут є хардкор: вважаємо що поле
        #  обрамляється лініями і один символ і ячейки відділяються лінями псевдографіки в один символ)
        #  TODO: перенести визначення символів обрамлення поля в налаштування
        #  TODO: додати оцінку розмірів зображення повідомлень при оцінці чи влізе поле на екран
        max_row_field_symbols = (
                self.field["size_rows"] * max_row_player_symbols
                + self.field["size_rows"]
                + 1
        )
        max_col_field_symbols = (
                self.field['size_columns'] * max_col_player_symbols
                + self.field["size_columns"]
                + 1
        )
        if max_row_field_symbols > self.screen["size_rows"]:
            raise ValueError(
                f"Зображення поля виходить за межі максимально можливої висоти екрану: "
                f"поле (рядки): {max_row_field_symbols} > max екран (рядки): "
                f"{self.restrictions['max_screen_rows']}"
            )
        if max_col_field_symbols > self.screen["size_columns"]:
            raise ValueError(
                f"Зображення поля виходить за межі максимально можливої ширини екрану: "
                f"поле (стовпці): {max_col_field_symbols} > max екран (стовпці): "
                f"{self.restrictions['max_screen_columns']}"
            )
        self.field["max_row_symbols"] = max_row_field_symbols
        self.field["max_col_symbols"] = max_col_field_symbols
        self.players["max_row_symbols"] = max_row_player_symbols
        self.players["max_col_symbols"] = max_col_player_symbols

    def create_field(self):
        """Створює нове поле з чистими клітинами (None)."""

        size_rows = self.field['size_rows']
        size_columns = self.field['size_columns']
        coordinates = {
            FieldCoordinates(row, column): None
            for row in range(size_rows)
            for column in range(size_columns)
        }

        return Field(coordinates)

    def create_players(self):
        players = deque(key for key, value in self.players.items() if isinstance(value, dict))
        random.shuffle(players)

        return Players(players)

    def create_game(self, active_cell):
        game_field = self.create_field()
        players = self.create_players()
        game = Game(
            field=game_field,
            players=players,
            settings=self,
            messages=Messages([Message('Hello!', False)], maxlen=self.messages['max_count']),
            status=True,
            active_cell=None
        )
        if active_cell:
            game.set_active_cell()

        return game


if __name__ == "__main__":
    import pprint

    pprint.pprint(Settings())
