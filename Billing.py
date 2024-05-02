
from tostring import *
import json


@auto_str
class Billing:
    def __init__(self, description: str, quantity: float, rate: float, amount: float, timestamp: int, tx_type: str):

        self.description = description
        self.quantity = quantity
        self.rate = rate
        self.amount = amount
        self.timestamp = timestamp
        self.tx_type = tx_type


    @staticmethod
    def parse_balance(data: str) -> float:
        lines: list = data.strip().split("\n")
        header = lines[0]
        totals: str = lines[len(lines)-1]
        rows: list = lines[1:len(lines)-2]

        return _parse_totals_row(totals)


def _parse_item_row(row: str) -> 'Billing':
    row.strip()
    columns: list = row.split(' ')
    columns = list(filter(lambda x: len(x.strip()) > 0, columns))

    descr = columns[0]
    quantity = _parse_float(columns[1])
    rate = _parse_float(columns[2])
    amount = _parse_float(columns[3])
    timestamp = int(_parse_float(columns[4]))
    tx_type = columns[5]

    return Billing(descr, quantity, rate, amount, timestamp, tx_type)


def _parse_totals_row(row: str) -> float:
    row.strip()
    values: list = row.strip().split('}')[0].split(',')
    credit = values[3].split(':')[1]

    return _parse_float(credit)


def _parse_float(value: str) -> float:
    if value.strip() in "-":
        return 0.0
    return float(value.strip())