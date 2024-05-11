
import requests
from requests import Response
import logger as log

from XenBlocksWallet import XenBlocksWallet
from tostring import auto_str


DIFFICULTY_URL1 = "http://xenminer.mooo.com:4447/getallblocks2/109337"
DIFFICULTY_URL2 = "http://xenminer.mooo.com/blockrate_per_day"

DIFFICULTY_URL = "http://xenminer.mooo.com/difficulty"
LEADERBOARD_URL = "http://xenminer.mooo.com/leaderboard"


@auto_str
class XenBlocks:
    def __init__(self):
        pass


    def get_difficulty(self) -> int:
        headers = {}
        try:
            response = requests.get(DIFFICULTY_URL, headers=headers)
            response.raise_for_status()
            return int(response.json().get('difficulty', 0))

        except requests.RequestException as e:
            log.error(f"Error getting difficulty: {e}")
            return 0


    def get_xenblocks_balance(self) -> list[str]:
        stats_table: list = []
        text = self._get_leaderboard()
#        print(text[1100:1800])
#        text = "abc123 <tbody> <tr> <td>2</td> <td>0x7d39f1372f95fbb67d259ac26443b69eb944f1d0</td> <td>385384</td> <td>504</td> <!-- New cell --> <td>100000.0</td> <!-- Moved to last position --> </tr> </tbody> 123 efg"

        if not text:
            return []

        tbody: list = get_elements("<tbody>", "</tbody>", text)
        rows: list = get_elements("<tr>", "</tr>", tbody[0])

        for row in rows:
            stats_table.append(row)

#            fields: list = get_elements("<td>", "</td>", row)
#            if len(fields) > 3:
#                stat: XenBlocksWallet = map_fields(fields)
#                stats_table.append(stat)

        return stats_table


    def map_row(self, row: str, timestamp_s: int) -> XenBlocksWallet:
        fields: list = get_elements("<td>", "</td>", row)
        if len(fields) < 4:
            return None

        return map_fields(fields, timestamp_s)


    def _get_leaderboard(self) -> str:
        headers = {}
        try:
            response: Response = requests.get(LEADERBOARD_URL, headers=headers)
            response.raise_for_status()
            return response.content.decode("utf-8")

        except requests.RequestException as e:
            log.error(f"Error getting wallet balances: {e}")
            return None


def map_fields(fields: list, timestamp_s: int) -> XenBlocksWallet:

    rank = int(fields[0])
    addr = fields[1]
    block = int(fields[2])
    sup = int(fields[3])
#    if sup == 0:
#        log.error("WTF>>>> " + fields[3])

    xuni = 0
    return XenBlocksWallet(addr, rank, block, sup, xuni, timestamp_s, 0.0)


def get_elements(start_tag: str, end_tag: str, from_text: str):
    # Split on end tag
    elements: list = from_text.split(end_tag)

    # Remove text outside the start tag
    elements = list(filter(lambda x: start_tag in x, elements))
    elements = list(map(lambda x: x.split(start_tag)[1].strip(), elements))
    return elements


#
# -- New cell -->\n          <td>100000.0</td> <!-- Moved to last position -->\n        </tr>\n        \n        <tr>\n          <td>860</td>\n
#
# <td>0x7c8d21f88291b70c1a05ae1f0bc6b53e52c4f28a</td>\n
# <td>2896</td>\n
# <td>5</td>
# <!-- New cell -->\n
# <td>100000.0</td>
# <!-- Moved to last position -->\n
# </tr>
# \n        \n        <tr>\n
# <td>861</td>\n
#
# <td>0x19dfb78a1fabfe8a5ccf1029eaacf440de48c7f7</td>\n          <td>2896</td>\n          <td>1</td> <!-- New cell -->\n          <td>100000.0</td> <!-- Moved to last position -->\n        </tr>\n        \n        <tr>\n          <td>862</td>\n          <td>0x9906aeaae832f4f9aee6186becdbf953ab348a41</td>\n          <td>2895</td>\n          <td>2</td> <!-- New cell -->\n          <td>100000.0</td> <!-- Moved to last position -->\n        </tr>\n        \n        <tr>\n          <td>863</td>\n          <td>0x6e0af30ffd4d6ad4e32662a2dc1a02478cbeb628</td>\n          <td>2891</td>\n          <td>4</td> <!-- New cell -->\n          <td>100000.0</td> <!-- Moved to last position -->\n        </tr>\n        \n        <tr>\n          <td>864</td>\n          <td>0x8553c0042fdb32304a7e903324033022ab357b5a</td>\n          <td>2884</td>\n          <td>4</td> <!-- New cell -->\n          <td>100000.0</td> <!-- Moved to last position -->\n        </tr>\n        \n        <tr>\n          <td>865</td>\n          <td>0x0f36321
#
#

