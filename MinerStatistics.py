
from tostring import *
from db.MinerStatisticsRepo import *
from constants import *
from Time import Time
from MinerRules import *
import copy


@auto_str
class MinerStatistics:
    def __init__(self, id: str, block: int, sup: int, xuni: int, duration_hours: float,
                 cost_per_hour: float, difficulty: int = 0, hashrate: float = 0.0, rank: int = 0):

        self.id = id
        self.rank = rank
        self.override = False
        self.timestamp_s: int = Time.now().get_age_in_seconds(0)
        self.duration_hours: float = duration_hours
        self.cost_per_hour: float = round(cost_per_hour, 3)

        self.difficulty: int = difficulty
        self.hashrate: float = hashrate
        self.block: int = block
        self.sup: int = sup
        self.xuni: int = xuni


    @staticmethod
    def from_json(jsondata: dict, id: str, duration_hours: float, cost_per_hour: float) -> 'MinerStatistics':
        difficulty: int = int(jsondata.get('netdiff_count', 0))
        hashrate: float = int(jsondata.get('hashrate_count', 0))
        block: int = int(jsondata.get('regularblock_count', 0))
        sup: int = int(jsondata.get('superblock_count', 0))
        xuni: int = int(jsondata.get('xuniblock_count', 0))

        return MinerStatistics(id, block, sup, xuni,
                               duration_hours, cost_per_hour, difficulty, hashrate)


    @staticmethod
    def create_with_timestamp(id: str, timestamp_s: int, block: int, sup: int, xuni: int, cost_per_hour: float) -> 'MinerStatistics':

        stats = MinerStatistics(id, block, sup, xuni, 0.0, cost_per_hour)
        stats.timestamp_s = timestamp_s
        return stats


    def clone(self) -> 'MinerStatistics':
        return copy.deepcopy(self)


    def reset_hours(self, total_hours: float):
        db = MinerStatisticsRepo()
        hours_offset: float = round(total_hours, 2)

        # If miner was restarted, all counters are reset to zero - just save the hours offset
#        if self.block <= 0:
#            db.update(self.cid, new_hours, 0)
#            self.duration_hours = 0.0
#            return

        # Read old offset
        old_offset = db.get(self.id)

        block_offset = 0
        xuni_offset = 0
        if old_offset:
            block_offset = old_offset[2]
            xuni_offset = old_offset[3]

        # Include the current count into offset
        block_offset += self.block
        xuni_offset += self.xuni

        # Save new offset
        db.update(self.id, hours_offset, block_offset)

        self.duration_hours = 0.0
        self.block -= block_offset
        self.xuni -= xuni_offset


    def normalize(self, total_duration):
        # Auto reset in the case the miner was restarted
        if MinerRules.should_reset_hours(self.block, self.xuni):
            self.reset_hours(total_duration)


    #
    # Handle that Vast instances are rebooted sporadically thereby resetting miner data
    #
    def override_data(self, data: tuple):
        if not data or len(data) < 3:
            return

#        print("Over: ", data)

        # If the managed instance was rebooted thereby resetting miner data -
        # offset block count and hours as a workaround
        hours_delta = data[1]
        block_delta = data[2]

        self.duration_hours -= hours_delta
        self.block -= block_delta

        if self.duration_hours < 0.0:
            print(C_ATTENTION, self)

        self.override = True
#        print(self)


    #
    # Calculate miner performance data
    #
    def xuni_rate(self) -> float:
        return self.calculate_performance(self.duration_hours, self.xuni)

    def block_rate(self, default: float = 0.6) -> float:
        return self.calculate_performance(self.duration_hours, self.block, default)

    def hashrate_per_dollar(self) -> float:
        return self.hashrate / self.cost_per_hour if self.cost_per_hour > 0.0 else 0.0

    def block_cost(self) -> float:
        return self.cost_per_hour / self.block_rate()

    def blocks_per_day(self, default: float = 0.6) -> float:
        return 24*self.block_rate(default)

    def blocks_per_(self, default: float = 0.6) -> float:
        return 24*self.block_rate(default)

    def calculate_performance(self, age_hours: float, count: int, default: float = 0.6) -> float:
        if count == 0 or age_hours < 0.1:
            return default

        return count/age_hours

