
import config as conf

arg = "--minerAddr 0xfAA35F2283dfCf6165f21E1FE7A94a8e67198DeA --totalDevFee 1"


class VastTemplate:
    def __init__(self, api_key):
        self.api_key = api_key
        self.cuda_ver = "11.6.1"


    def get_create_cmd(self, addr: str, offer_id: int, price: float) -> list[str]:
        return self.get_create_cmd_11_6(addr, offer_id, price)
#        return self.get_create_cmd_smit(addr, offer_id, price)


#  Copy file from VAST:
#  scp -P 18342 root@ssh5.vast.ai:/root/poc/copa/xengpuminer ./


    def get_create_cmd_11_6(self, addr: str, offer_id: int, price: float) -> list[str]:
        return [
            "vastai", "create", "instance", str(offer_id),
            "--price", str(price),
            "--image", f"nvidia/cuda:{self.cuda_ver}-devel-ubuntu20.04",
            #            "--image", "nvidia/cuda:11.8.0-devel-ubuntu20.04",
            "--env", f"-e ADDR={addr}",
#            "--env", f"-e ACCOUNT={addr}",
            "--onstart", "onstart.txt", #START_PAR,
            "--disk", "7.944739963496298",
            "--api-key", self.api_key,
            "--ssh",
            "--raw"
        ]

    def get_create_cmd_smit(self, addr: str, offer_id: int, price: float) -> list[str]:
        return [
            "vastai", "create", "instance", str(offer_id),
            "--price", str(price),
            "--image", "smit1237/xengpuminer:vast",
            "--env", f"-e ADDR={addr}",
            "--args", "--args ...",
            "--api-key", self.api_key,
            "--raw"
        ]
