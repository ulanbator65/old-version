
import threading
import requests
import traceback
import json
from datetime import datetime

from VastAiCLI import VastAiCLI
from VastQuery import VastQuery
from VastInstance import VastInstance
from VastOffer import VastOffer
from XenBlocks import *
from Billing import Billing
from MinerDataCache import MinerDataCache
from db.DbCache import DbCache
from Field import Field
from constants import *
from tostring import auto_str
import config
from cachetools import cached, TTLCache
import logger as log


INSTANCE_URL = "https://console.vast.ai/api/v0/instances"

f = Field(ORANGE)
fgray = Field(GRAY)

SECONDS = 1
MINUTES = 60*SECONDS


@auto_str
class VastClient:
    def __init__(self, api_key, blacklist, vast_cmd: VastAiCLI = VastAiCLI(config.DB_NAME)):
        self.api_key = api_key
        self.blacklist = blacklist
        self.vast_cmd = vast_cmd


    def get_instances(self) -> list[VastInstance]:
        instances = []
        try:
            data: dict = self.get_cached_instances()
            rows = data.get('instances', [])

            if len(rows) < 1:
                raise Exception("WTF!!!")

            for json_data in rows:
                inst = self.instance_from_json(json_data)
                instances.append(inst)

            if len(instances) < 1:
                log.error("No VAST instances found!!!")

        except requests.RequestException as e:
            log.error(f"Error fetching instances: {e}")

        return instances


    def instance_from_json(self, json: dict) -> 'VastInstance':
        return VastInstance(json)


    def create_instance(self, addr: str, instance_id: int, price: float) -> int:
        cmd = VastAiCLI(self.api_key)

        if not config.MANUAL_MODE:
            response = cmd.create(addr, instance_id, price)
        else:
            response = cmd.create_manual_instance(addr, instance_id, price)

        contract_id = int(response.get('new_contract'))
        log.warning(f"Created instance for offer id {instance_id}! Contract id = {contract_id}")
        return contract_id


    def increase_bid(self, instance_id: int, new_price: float):
        cmd = VastAiCLI(self.api_key)
        cmd.change_bid(instance_id, new_price)


    @cached(cache=TTLCache(maxsize=1, ttl=1*MINUTES))
    def get_vast_balance(self) -> float:
        billing_data: str = VastAiCLI(self.api_key).get_billing()

        if not billing_data:
            log.error("Failed to get billing!!")
            return None

        return Billing.parse_table(billing_data)


    def reboot_instance(self, instance_id):
        log_info(f"Attempting to reboot instance {instance_id}...")
        result = VastAiCLI(self.api_key).reboot(instance_id)

        if result:
            print(f.format(f"Instance {instance_id} rebooted successfully."))
            print(result)
        else:
            print(f.format(f"Failed to reboot instance {instance_id}."))


    def kill_instance(self, instance_id):
        log_info(f"Attempting to terminate instance {instance_id}...")
        result = VastAiCLI(self.api_key).delete(instance_id)

        if result:
            print(f.format(f"Instance {instance_id} terminated successfully."))
            print(result)
        else:
            print(f.format(f"Failed to terminate instance {instance_id}."))


    def kill_instances(self, ids: list):
        log_info(f"Attempting to terminate instances {ids}...")
        result = VastAiCLI(self.api_key).delete_all(ids)

        if result:
            print(f.format(f"Instance {ids} terminated successfully."))
            print(result)
        else:
            print(f.format(f"Failed to terminate instance {ids}."))


    def get_offer_for_instance(self, instance_id: int) -> list:
        query = VastQuery.instance_query(instance_id, 2.0)

        result = self.vast_cmd.get_offers(query)

        iterator = filter(lambda x: (x.get('id') == instance_id), result)
#        iterator = filter(self.is_same, result)
#        iterator = filter(InstanceTable.is_managed, result)
        return list(iterator)


    def get_offers(self, query: VastQuery) -> list[VastOffer]:
        return self.vast_cmd.get_offers(query)


    def get_query_string(self, model: str, query: VastQuery) -> str:
        query_parts = ["verified=false", "rented=false", f"min_bid <= {query.max_bid}"]
        query_parts.append(f"num_gpus>={query.min_gpus}")
        query_parts.append(f"gpu_name={model.replace(' ', '_')}")

        query_str = " ".join(query_parts)
        return query_str


    def load_miner_data(self, instances: list):
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
        if not inst.is_running() or not inst.is_managed or not inst.get_miner_url():
            log.info(f"Miner stats skipped for instance {inst.cid} due to unavailable external port.")
            inst.miner_status = "offline"
            return

        # Get Miner data
        try:
            data = MinerDataCache(inst.cid, inst.get_miner_url()).get_miner_data()
#            data = MinerCache.get_miner_statistics(inst.cid, inst.get_miner_url())
            if data:
                inst.add_statistics(inst.cid, data)
                inst.miner_status = "online"
            else:
                inst.miner_status = "offline"
                # Do not reset statistics at this time, it could be interpreted as a dead miner instance
#                inst.reset_statistics()

        except Exception as e:
            inst.miner_status = "offline"
#            inst.miner = None
#            traceback.print_exc()
#            log.info(f"Error getting miner data from {inst.get_miner_url()} for instance {inst.cid}: {e}")


    def get_miner_statistics_delete(self, inst: VastInstance, stats):
        # Instance stopped
        if not inst.is_running():
            #            inst.miner_status = "offline"
            return

        # No connection to Miner
        if not inst.is_managed or not inst.get_miner_url():
            log.info(f"Miner stats skipped for instance {inst.cid} due to unavailable external port.")
            #            inst.miner_status = "offline"
            return

        # Get Miner data
        try:
            response = requests.get(inst.get_miner_url(), timeout=5)
            if response.status_code == 200:
                inst.add_statistics(inst.cid, response.json())
                inst.miner_status = "online"
            else:
                inst.miner_status = "offline"
                inst.reset_statistics()
                log.info(f"Failed to get miner data from {inst.get_miner_url()} for instance {inst.cid}: Status code {response.status_code}")

        except Exception as e:
            inst.miner_status = "offline"
            #            inst.miner = None
            traceback.print_exc()
            log.error(f"Error getting miner data from {inst.get_miner_url()} for instance {inst.cid}: {e}")


    def is_blacklisted(self, instance) -> bool:
        for inst in self.blacklist:
            if instance.cid == inst:
                return True

        return False


    def get_cached_instances(self) -> dict:
        ttl_s = 40
        key = "VastInstances"
        cach_entry: DbCache.CacheEntry = DbCache().get(key)

        if cach_entry.is_expired(ttl_s):
            response = self.get_cached_response()
            DbCache().update(key, response.text)
            return json.loads(response.text)

        return json.loads(cach_entry.get_value())


    @cached(cache=TTLCache(maxsize=1, ttl=10*SECONDS))
    def get_cached_response(self) -> requests.Response:
        print("VAST instance cache loaded...")

        headers = {"Authorization": f"Bearer {self.api_key}"}
        response: requests.Response = requests.get(INSTANCE_URL, headers=headers)
        response.raise_for_status()
        return response


def log_info(info):
    print(fgray.format(info))


def log_attention(info):
    print(f.format(info))