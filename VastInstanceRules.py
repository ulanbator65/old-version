
from datetime import datetime, timedelta


class VastInstanceRules:

    @staticmethod
    def has_address(address: str, other_address: str) -> bool:
        return address.lower() == other_address.lower()

    @staticmethod
    def is_running(status: str) -> bool:
        return status == VastInstanceRules.status_for_running()

    @staticmethod
    def is_mining(is_managed: bool, miner_status: str, hashrate: int) -> bool:
        return miner_status == "online" or (not is_managed and hashrate > 0)   # Manual data from manual instance

    @staticmethod
    def is_dead(status: str) -> bool:
        return status in [ VastInstanceRules.status_for_outbid() ]

    @staticmethod
    def is_not_started(status: str) -> bool:
        return status in [ VastInstanceRules.status_for_not_started() ]

    @staticmethod
    def is_outbid(status: str) -> bool:
        return status == VastInstanceRules.status_for_outbid() or status == "created" or status == "loading"

    @staticmethod
    def status_for_outbid() -> str:
        return "exited"

    @staticmethod
    def status_for_running() -> str:
        return "running"

    @staticmethod
    def status_for_not_started() -> str:
        return "created"

    @staticmethod
    def is_model_A40(gpu_model: str) -> bool:
        return "A40" in gpu_model

    @staticmethod
    def is_model_A5000(gpu_model: str) -> bool:
        return "A5000" in gpu_model

    @staticmethod
    def needs_reboot(status: str, hash_per_usd: int, hpd_min: int = 15000) -> bool:
        return VastInstanceRules.is_running(status) and (hash_per_usd < hpd_min)

    @staticmethod
    def is_new_instance(start_time: float) -> bool:
        return VastInstanceRules.age_in_hours(start_time) < 0.3

    @staticmethod
    def age_in_hours(timestamp: float) -> float:
        age = datetime.now().timestamp() - timestamp
        return age / 3600


