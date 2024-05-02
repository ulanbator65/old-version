
from tostring import *


@auto_str
class Balance:
    def __init__(self, balance: float, timestamp: float):
        self.balance = balance
        self.timestamp_s = timestamp


    def calc_cost_per_hour(self, other: 'Balance') -> float:

        tdelta_s = other.timestamp_s - self.timestamp_s
        tdelta_h = tdelta_s/3600
        bdelta = other.balance - self.balance

        return bdelta / tdelta_h


