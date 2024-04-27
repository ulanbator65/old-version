
from datetime import datetime
from Time import Time
from tostring import auto_str
from config import VAST_IMAGE, WHITELIST, MANUAL_MODE

from MinerStatistics import MinerStatistics
from MinerStatisticsRepo import MinerStatisticsRepo
from VastInstanceRules import *


@auto_str
class VastInstance:

    def __init__(self, json: dict):
#        print(json)
        self.miner_repo: MinerStatisticsRepo = MinerStatisticsRepo()
        self.json: dict = json
        self.is_managed: bool = not self._is_manual_instance(json.get('image_uuid'))
        self.id: int = json.get('id')
        self.min_bid: float = json.get('min_bid')
        self.start_date = json.get('start_date', None)
        self.duration = json.get('duration', None)
        print("Duration: ", self.duration)

        self.public_ipaddr = json.get('public_ipaddr', '').strip()
        self.external_port = json.get('ports', {}).get('8080/tcp', [{}])[0].get('HostPort', None)
        self.geolocation = json.get('geolocation', '')
        self.cost_per_hour = json.get('dph_total', 0)
        self.gpu_name: str = json.get('gpu_name', '')
        self.gpu_name_short: str = self.gpu_name.replace("RTX ", "")
        self.num_gpus: int = json.get('num_gpus', 0)
        self.total_flops: float = json.get('total_flops', 0)
        self.flops_per_dphtotal: int = int(json.get('flops_per_dphtotal', 0))
        status: str = json.get('actual_status', "none")
        self.actual_status: str = status if status and len(status) > 0 else "none"
        self.rebooted: bool = False
        self.addr: str = None
        env = json.get('extra_env')
        if len(env) > 0:
            self.addr: str = env[0][1]

        #  Miner statistics
        self.miner_status: str = "offline"
        self.miner: MinerStatistics = None


    def _is_manual_instance(self, image: str):
        return MANUAL_MODE and (image == VAST_IMAGE)


    def reset_hours(self):
        offset_hours = self.get_age_in_hours()   # self.miner.hours
        self.miner.reset_hours(offset_hours)


    def get(self, field: str) -> str:
        return self.json.get(field)

    def has_address(self, address: str) -> bool:
        return self.addr.lower() == address.lower()

    def is_miner_online(self) -> bool:
        return self.miner_status == 'online'

    def is_miner_data_loaded(self):
        return self.miner

    def is_manual_override(self):
        return self.miner and self.miner.override

    def is_outbid(self):
        return VastInstanceRules.is_outbid(self.actual_status)

    def is_same(self, id: int) -> bool:
#        print(type(id))
        return self.id == id

    def get_miner_url(self) -> str:
        if not self.get_host():
            return None

#        miner_url = f"{inst.get_link()}/data"
        return f"http://" + self.get_host() + "/data"

    def get_host(self) -> str:
        return f"{self.public_ipaddr}:{self.external_port}" if self.external_port else None


    def clear_statistics(self):
        self.miner = None


    def add_statistics(self, id: int, json: dict):
#        print(json)
        self.miner = MinerStatistics.from_json(json, id, self.get_age_in_hours(), self.cost_per_hour)
        override_data = self.miner_repo.get(id)
        self.miner.override_data(override_data)
        self.miner.normalize()



    def hashrate_per_dollar(self) -> float:
        return self.miner.hashrate_per_dollar() if self.miner else 0.0

    def block_cost(self) -> float:
        return self.miner.block_cost if self.miner else 0.0


    # If instance is running the effective cost is same as cost per hour
    # If instance is not running, return a percentage of the cost per hour
    # based on estimated up time
    def effective_cost_per_hour(self, uptime_percentage: float):
        return self.cost_per_hour if self.is_running() else uptime_percentage * self.cost_per_hour


    def hashrate(self) -> float:
        return self.miner.hashrate if self.miner else 0.0


    def is_running(self) -> bool:
        return VastInstanceRules.is_running(self.actual_status)


    def is_mining(self) -> bool:
        return VastInstanceRules.is_mining(self.is_managed, self.actual_status, int(self.hashrate()))


    def is_dead(self) -> bool:
        return VastInstanceRules.is_dead(self.actual_status)

    def is_model_a40(self) -> bool:
        print(self.gpu_name_short)
        return VastInstanceRules.is_model_A40(self.gpu_name_short)

    def is_model_a5000(self) -> bool:
        print(self.gpu_name_short)
        return VastInstanceRules.is_model_A5000(self.gpu_name_short)

    def get_age_in_seconds(self, start_timestamp) -> float:
        if not start_timestamp:
            return 0

        start_time = datetime.fromtimestamp(start_timestamp)
        tdelta = self.snapshot_time - start_time
        hours_delta = tdelta.seconds/3600
        hours_delta += tdelta.days*24
        seconds = 3600 * hours_delta
        return round(seconds, 0)


    def get_age_in_hours(self) -> float:
        return Time.now().get_age_in_hours(self.start_date)


    def print_states(self):
        print("Actual:", self.json.get('actual_status'), " Intended:", self.json.get('intended_status'), " Current:", self.json.get('cur_state'), " Next:", self.json.get('next_state'))


    @staticmethod
    def is_whitelisted(instance) -> bool:
        for inst in WHITELIST:
            if instance.get('id') == inst:
                return True

        return False
