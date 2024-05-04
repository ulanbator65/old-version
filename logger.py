
from Field import Field
from constants import *

f = Field(GRAY)
f_error = Field(RED)
f_warning = Field(ORANGE)


def print_info(info: str):
    print(f.format(info))


def print_error(info: str):
    print(f_error.format(info))


def print_warning(info: str):
    print(f_warning.format(info))
