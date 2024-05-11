
import platform
import os
import getch

from constants import *


def get_choice(text: str):
    print(text)
    return getch.getch().upper()


def text_color(text: str, color=LIGHT_YELLOW):
    return color + text + RESET


def display_splash_screen():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

    splash_screen = """
\033[92m,

Welcome to TreeCityWes.eth's Vast.ai XenBlocks Mining Assistant. 

    - Remember to create .ENV file with Wallet Address and API variables
    - Open-source with zero fee collection - https://github.com/TreeCityWes/XenBlocks-Assistant
    - Smit: https://www.buymeacoffee.com/smit1237 | Wes: https://www.buymeacoffee.com/treecitywes


This script is designed to work with Smit1237's XenBlocks Template on Vast.ai

    - Template: https://cloud.vast.ai/?ref_id=88736&t...
    - Docker: https://hub.docker.com/r/smit1237/xen...
    - Vast.ai Sign-Up: https://cloud.vast.ai/?ref_id=88736
    - More Information at https://hashhead.io

RESET"""

    print(splash_screen)
