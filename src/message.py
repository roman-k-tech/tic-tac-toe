from collections import deque
from typing import Self


class Message:
    def __init__(self, text, status):
        self.text = text
        self.status = status


class Messages(deque[Message]):

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    def get_unsent(self) -> Self:
        return Messages(deque(message for message in self if message.status is False))

    def get_text(self, width, height):
        messages = [message for message in self if message.status is False]
        # замінити повідомлення на такі ж зі зміненими статусами
        for index, message in enumerate(messages):
            messages[index] = Message(message.text, True)

        # залишити лише текст повідомлень
        messages = [message.text for message in messages]
        return self.prepare_messages(messages, width, height)

    @classmethod
    def prepare_messages(cls, messages, width: int, height: int) -> str:
        """Готує повідомлення для виведення на екран.

        Створює рядок, який складається з повідомлень, розбитих по словах в рядки довжиною не більше за width
        і доповнених пробілами до width.
        Між окремими повідомленнями додані рядки з пробілів шириною width.
        Якщо кількість рядків більше за height - виводить лише ті що влізли
        """
        result = ""
        for message in messages:
            # обробити повідомлення
            result += cls.prepare_message_for_transfer_in_words(message=message, width=width)
            # додати рядок пробілів шириною width між повідомленнями
            result += " " * width
            if len(result) // width > height:
                last = width + 3
                result = result[:-last] + "..."
                break
        return result

    @staticmethod
    def prepare_message_for_transfer_in_words(message: str, width: int) -> str:
        """Готує повідомлення для виведення на екран.

        формує рядок таким чином, щоб якщо його нарізати по width символів, то результати нарізки починались
        з слова, і ні одно слово не було б розірвано

        Якщо зустрічаються слова, довжина яких більше за width - обрізає їх на width -3 символи і доповнює "..."
        """
        # розбити повідомлення на слова
        words = message.split()
        # перевірити довжину слів і обрізати якщо потрібно
        words = map(
            lambda word: word[: width - 3] + "..." if len(word) > width else word, words
        )

        result = ""  # тут накопичується результат
        current_length = 0  # змінна яка містить поточну довжину "субрядка" (довжина якого не може перевищувати width)
        for word in words:
            # якщо довжина слова максимальна і це початок "субрядка" - сформувати цілий рядок
            if len(word) == width and current_length == 0:
                result += word
            # якщо довжина слова + current_length менше за width - додати слово до "субрядка"
            elif len(word) + current_length < width:
                result += word + " "
                current_length += len(word) + 1
            # якщо довжина слова + current_length дорівнює width - додати слово до "субрядка" і перейти на новий рядок
            elif len(word) + current_length == width:
                result += word
                current_length = 0
            elif (len(word) + current_length > width) and len(word) < width:
                result += (width - current_length) * " " + word + " "
                current_length = len(word) + 1
            elif (len(word) + current_length > width) and (len(word) == width):
                result += (width - current_length) * " " + word
                current_length = len(word)
        result += (width - current_length) * " "
        return result
