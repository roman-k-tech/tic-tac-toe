import time
from collections import deque, ChainMap

from settings import Settings
from game import Game
from message import Message, Messages
import utils
from field import FieldCoordinates

game = Settings().create_game(active_cell=False)


def main(current_game: Game) -> None:
    while True:
        #     надрукувати повідомлення про поточний стан гри (хто ходе, помилки, якщо є, і тд)
        #     show_messages(current_game)
        #     надрукувати поле
        #     show_field(current_game)
        utils.clear_terminal_screen()
        print(current_game.show_game())
        current_game = current_game.is_game_over()
        if not current_game.status:
            break

        # гравець вводить хід (який гравець - знаємо в атрибуті current_game.players)
        position = current_game.input_next_position()
        if not isinstance(position, FieldCoordinates):
            current_game.messages.append(Message(position, False))
            continue
        #     додати гравця на поле в позицію position
        current_game = current_game.add_player_to_field_position(position)
        # вивести повідомлення про переможця
        # show_messages(current_game)
        # вивести поле
        # show_field(current_game)
        time.sleep(0.1)

    # вивести повідомлення про переможця
    utils.clear_terminal_screen()
    print(current_game.show_game())


if __name__ == "__main__":
    main(game)
