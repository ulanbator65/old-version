
import traceback
import logging
import requests


NULL_RESPONSE: dict = None


def get_miner_statistics(id: int, miner_url: str) -> dict:
    # Instance stopped
#    if not inst.is_running():
        #            inst.miner_status = "offline"
#        return

    # No connection to Miner
    if not miner_url:
        logging.info(f"Miner stats skipped for instance {id} due to unavailable external port.")
        #            inst.miner_status = "offline"
        return NULL_RESPONSE

    # Get Miner data
    response = requests.get(miner_url, timeout=5)
    if response.status_code == 200:
        return response.json()
    #            inst.add_statistics(inst.id, response.json())
    #            inst.miner_status = "online"
    else:
        #            inst.miner_status = "offline"
        #            inst.reset_statistics()
        logging.info(f"Failed to get miner data from {miner_url} for instance {id}: Status code {response.status_code}")
        return NULL_RESPONSE



