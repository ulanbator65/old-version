
from tostring import *
from constants import *


@auto_str
class Field:
    def __init__(self, color: str):
        self.color = color

    def blue(self):
        self.color = BLUE
        return self

    def format(self, text: str, color: str = None):
        c = color if color else self.color
        return c + _normalize(text) +  RESET

    def center(self, text: str, w: int):
        t1 = self.color + _normalize(text) + RESET
        return RESET + t1.center(w) + RESET

    def string(self, text: str):
        return self.color + _normalize(text) +  RESET

    def gray(self, text: str):
        return self.format(text, GRAY)

    def yellow(self, text: str):
        return self.format(text, YELLOW)

    @staticmethod
    def attention(text: str):
        return Field(YELLOW).format(text)


def _normalize(text: str):
    return text if text else ""

