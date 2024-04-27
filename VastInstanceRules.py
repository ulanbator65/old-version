

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
    def is_outbid(status: str):
        return status == VastInstanceRules.status_for_outbid()

    @staticmethod
    def status_for_outbid():
        return "exited"

    @staticmethod
    def status_for_running():
        return "running"

    @staticmethod
    def status_for_not_started():
        return "created"

    @staticmethod
    def is_model_A40(gpu_model: str):
        return "A40" in gpu_model

    @staticmethod
    def is_model_A5000(gpu_model: str):
        return "A5000" in gpu_model
