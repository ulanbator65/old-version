
import threading
import requests
import logging
import traceback

from VastAiCLI import VastAiCLI
from VastQuery import VastQuery
from VastInstance import VastInstance
from VastOffer import VastOffer
from XenBlocks import *
from tostring import auto_str
import config

INSTANCE_URL = "https://console.vast.ai/api/v0/instances"


@auto_str
class VastClient:
    def __init__(self, api_key, blacklist, vast_cmd: VastAiCLI = VastAiCLI(config.DB_NAME)):
        self.api_key = api_key
        self.blacklist = blacklist
        self.vast_cmd = vast_cmd


    def get_instances(self) -> list[VastInstance]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        instances = []
        try:
            response = requests.get(INSTANCE_URL, headers=headers)
            response.raise_for_status()
            data = response.json()

            for json_data in data.get('instances', []):
                inst = self.instance_from_json(json_data)
                instances.append(inst)

        except requests.RequestException as e:
            logging.error(f"Error fetching instances: {e}")

        return instances


    def instance_from_json(self, json: dict) -> 'VastInstance':
        return VastInstance(json)


    def create_instance(self, addr: str, instance_id: int, price: float) -> dict:
        cmd = VastAiCLI(self.api_key)
        if not config.MANUAL_MODE:
            return cmd.create(addr, instance_id, price)
        else:
            return cmd.create_manual_instance(addr, instance_id, price)


    def increase_bid(self, instance_id, new_price):
        cmd = VastAiCLI(self.api_key)
        cmd.change_bid(instance_id, new_price)


    def reboot_instance(self, instance_id):
        print(f"Attempting to terminate instance {instance_id}...")
        result = VastAiCLI(self.api_key).reboot(instance_id)

        if result:
            print(f"Instance {instance_id} rebooted successfully.")
            print(result)
        else:
            print(f"Failed to reboot instance {instance_id}.")


    def kill_instance(self, instance_id):
        print(f"Attempting to terminate instance {instance_id}...")
        result = VastAiCLI(self.api_key).delete(instance_id)

        if result:
            print(f"Instance {instance_id} terminated successfully.")
            print(result)
        else:
            print(f"Failed to terminate instance {instance_id}.")


    def get_offer_for_instance(self, instance_id: int) -> list:
        query = VastQuery.instance_query(instance_id, 2.0)

        result = self.vast_cmd.get_offers(query)
#        print(">>>>><>>>>><  ", result)
        iterator = filter(lambda x: (x.get('id') == instance_id), result)
#        iterator = filter(self.is_same, result)
#        iterator = filter(InstanceTable.is_managed, result)
        return list(iterator)


    def get_offers(self, query: VastQuery) -> list[VastOffer]:
        result = self.vast_cmd.get_offers(query)

        return list(filter(lambda x: self.validate(x, query), result))


    def get_query_string(self, model: str, query: VastQuery) -> str:
        query_parts = ["verified=false", "rented=false", f"min_bid <= {query.max_bid}"]
        query_parts.append(f"num_gpus>={query.min_gpus}")

        query_parts.append(f"gpu_name={model.replace(' ', '_')}")

        query_str = " ".join(query_parts)
        return query_str


    def get_miner_data(self, instances: list):
        threads = []

        for inst in instances:
            if inst.is_managed:
                thread = threading.Thread(target=self.get_miner_statistics, args=(inst, {}))
                threads.append(thread)
                thread.start()

        for thread in threads:
            thread.join()


    def get_miner_statistics(self, inst: VastInstance, stats):
        # Instance stopped
        if not inst.is_running():
#            inst.miner_status = "offline"
            return

        # No connection to Miner
        if not inst.is_managed or not inst.get_miner_url():
            logging.info(f"Miner stats skipped for instance {inst.id} due to unavailable external port.")
#            inst.miner_status = "offline"
            return

        # Get Miner data
        try:
            response = requests.get(inst.get_miner_url(), timeout=5)
            if response.status_code == 200:
                inst.add_statistics(inst.id, response.json())
                inst.miner_status = "online"
            else:
                inst.miner_status = "offline"
                inst.reset_statistics()
                logging.info(f"Failed to get miner data from {inst.get_miner_url()} for instance {inst.id}: Status code {response.status_code}")

        except Exception as e:
            inst.miner_status = "offline"
#            inst.miner = None
            traceback.print_exc()
            logging.error(f"Error getting miner data from {inst.get_miner_url()} for instance {inst.id}: {e}")


    def validate(self, instance: VastInstance, query: VastQuery):
        if self.is_blacklisted(instance):
            return False

#            if instance['flops_per_dphtotal'] > 500.0:
#                return False

#        if query.tflop_price > 0 and instance.tflops_per_dph < query.tflop_price:
#            return False

        return True


    def is_blacklisted(self, instance) -> bool:
        for inst in self.blacklist:
            if instance.id == inst:
                return True

        return False

