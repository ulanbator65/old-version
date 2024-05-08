
from prettytable.colortable import Theme


def fg_color(code: int):
    return FG + str(code) + 'm'


def bg_color(code: int):
    return BG + str(code) + 'm'


CH_EXIT = 'X'
CH_K = 'K'
CH_I = 'I'

PRE = '\033['
FG = '\033[38;5;'
BG = '\033[48;5;'

RESET = PRE + '0m'   # Reset color
BLINK = '\033[5m'

GRAY = fg_color(243)

#GRAY = PRE + '90m'
DARK_GRAY = PRE + '91m' #PRE  + '235m'

RED = PRE + '91m'
YELLOW = PRE + '93m'
GREEN = PRE + '92m'
PURPLE = PRE + '95m'
CYAN = PRE + '96m'
BLUE = PRE + '94m'
WHITE = PRE + '97m'


RED2 = fg_color(161)

LIGHT_YELLOW = fg_color(185)

GREEN2 = fg_color(156)
GREEN3 = fg_color(35)

LIGHT_CYAN = fg_color(159)
LIGHT_CYAN2 = fg_color(123)

BLUE2 = fg_color(27)

LIGHT_PINK = fg_color(132)
DARK_PINK = fg_color(89)
PINK = fg_color(213)

GOLD = fg_color(179)

ORANGE = fg_color(202)
LIGHT_PURPLE = fg_color(140)

GRAY2 = fg_color(235)

C_HIGH_ALERT = RED + BLINK
C_ERROR = RED2
C_ATTENTION = LIGHT_CYAN2
C_ATTENTION_BLINK = ORANGE + BLINK
C_WARNING = LIGHT_YELLOW
C_OK = GREEN2

BG_GRAY = BG + '235m'
BG_BLACK = BG + '232m'
BG_ORANGE = bg_color(29)


C_THEME1 = LIGHT_PINK
C_THEME2 = GRAY2
THEME1: Theme = Theme(default_color=C_THEME1, vertical_color=C_THEME1, horizontal_color=C_THEME1, junction_color=C_THEME1, junction_char="-")
THEME2: Theme = Theme(default_color=LIGHT_CYAN, vertical_color=C_THEME2, horizontal_color=C_THEME2, junction_color=C_THEME2, junction_char="-")


ALL_ADDR: list = ["0x7c8d21F88291B70c1A05AE1F0Bc6B53E52c4f28a".lower(),
                  "0xe977d33d9d6D9933a04F1bEB102aa7196C5D6c23".lower(),
#                  "0xd9007A12b33b699Ee01B7D6f9D9fEae42AB5145C".lower(),
                  "0xfAA35F2283dfCf6165f21E1FE7A94a8e67198DeA".lower(),
                  "0xd76cb96ac40fd3510648419925a645465570c822".lower(),

                  "0x83365693bDAA513C0f5Fe61DCDFb5DEE1493C501".lower(),
                  "0xbAa0BeDaAd3BA04Fe01b71D38D93D5C894392993".lower(),
                  "0xd50e300208c3a4be060e7ed2ad2cd9937d283a23".lower(),
                  "0x352462d203f392b6c3e4ceb6d96bac1383609f17".lower(),
                  ]

