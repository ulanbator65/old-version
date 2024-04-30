
import subprocess
import json

from VastQuery import VastQuery
from VastOffer import VastOffer
from tostring import auto_str
from config import *
from Field import Field
from constants import *


@auto_str
class VastAiCLI:
    def __init__(self, api_key):
        self.api_key = api_key


    def create(self, addr: str, instance_id: int, price: float) -> dict:
        command = [
            "vastai", "create", "instance", str(instance_id),
            "--price", str(price),
            "--image", VAST_IMAGE,
            "--env", f"-e ADDR={addr}",
            "--args", "--args ...",
            "--api-key", self.api_key,
            "--raw"
        ]
        result = self.run(command)
        print(result)
        return result

    def create_manual_instance(self, addr: str, instance_id: int, price: float) -> dict:
        command = [
            "vastai", "create", "instance", str(instance_id),
            "--price", str(price),
            "--image", VAST_IMAGE,
#            "--env", "null",
            "--env", f"-e ADDR={addr}",
            "--disk", "16",
            "--ssh"
        ]
        result = self.run(command)
        print(result)
        return result

    def change_bid(self, instance_id, price):
        command = [
            "vastai", "change", "bid", str(instance_id),
            "--price", str(price),
            "--api-key", self.api_key,
            "--raw"
        ]
        result = self.run(command)
        print(result)
        return result


    def reboot(self, instance_id):
        command = ["vastai", "reboot", "instance", str(instance_id), "--api-key", self.api_key]
        result = self.run(command)
        print(result)
        return result


    def delete(self, instance_id):
        command = ["vastai", "destroy", "instance", str(instance_id), "--api-key", self.api_key]
        result = self.run(command)
        print(result)
        return result


    def get_offers(self, query: VastQuery) -> list[VastOffer]:
        command = ["vastai", "search", "offers", query.get_query(), "--type", "bid", "--raw"]
        response = self.run(command)

        if not isinstance(response, list):
            print("Error: Unexpected response format. Please ensure your command execution function is correct.")

        return list(map(lambda x: VastOffer(x), response))


    def run(self, command: list) -> dict:
        f = Field(GRAY)
        print(f.format("INFO >>> "), f.format(str(command)))

        response = self.__execute_command(command) #, capture_output=True, text=True)

        if not response:
            print("Error >>> no response received")

        elif response.stderr:
            print("Error >>> ", response.stderr.strip())

        elif response.stdout:
            try:
                return json.loads(response.stdout)

            except json.JSONDecodeError:
                return {"success": False, "error": "Loading...", "stdout": response.stdout.strip()}


    def __execute_command(self, cmd: list):
        try:
            return subprocess.run(cmd, capture_output=True, text=True, check=True)

        except subprocess.CalledProcessError as e:
            print(f">>>     Error running command: {e}")


