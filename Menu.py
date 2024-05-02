import ui
from Automation import *

BORDER_WIDTH = 4*20


class Menu:
    def __init__(self, header: str, items: list, width: int, col_header=LIGHT_CYAN, col_row=GOLD, col_bg=BG_GRAY):
        self.header: str = header
        self.items: list[str] = items
        self.inner_width = width
        self.color1 = col_header
        self.col_row = col_row
        self.col_bg = col_bg


    def select(self):
        self.print()

        f = Field(LIGHT_CYAN)
        choice = ui.get_choice(f.center("Enter your choice: ", self.inner_width))
        print(f.center("Choice = " + choice, self.inner_width))

        return choice


    def center(self):
        self.header.center(self.inner_width)
        for item in self.items:
            item.center(self.inner_width)

        return self


    def print(self):
        f1 = Field(self.color1 + self.col_bg)
        f = Field(self.col_row + self.col_bg)

        print()
        self.print_item(f, " ")
        self.print_header(f1, self.header)

        for item in self.items:
            self.print_item(f, item)

        self.print_item(f, " ")


    def print_header(self, f: Field, text: str):
        inner = text.center(self.inner_width)
        self._print_center(f, inner, self.total_width())

    def print_item(self, f: Field, text: str):
        inner = text.ljust(self.inner_width)
        self._print_center(f, inner, self.total_width())

    def total_width(self):
        return self.inner_width + BORDER_WIDTH

    def _print_center(self, f: Field, text: str, width: int):
        print(f.center(text, width))

