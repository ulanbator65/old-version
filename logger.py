
from Field import Field
from constants import *

f = Field(GRAY)
f_error = Field(RED)
f_warning = Field(ORANGE)


def info(info: str):
    print(f.format(info))


def error(info: str):
    print(f_error.format(info))


def warning(info: str):
    print(f_warning.format(info))
