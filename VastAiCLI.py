
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
        return self._stdout_to_dict(result)


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
        return self._stdout_to_dict(result)


    def change_bid(self, instance_id: int, price: float) -> dict:
        command = [
            "vastai", "change", "bid", str(instance_id),
            "--price", str(price),
            "--api-key", self.api_key,
            "--raw"
        ]
        result = self.run(command)
        return self._stdout_to_dict(result)


    def reboot(self, instance_id: int) -> dict:
        command = ["vastai", "reboot", "instance", str(instance_id), "--api-key", self.api_key]
        result = self.run(command)
        return self._stdout_to_dict(result)


    def delete(self, instance_id: int) -> str:
        command = ["vastai", "destroy", "instance", str(instance_id), "--api-key", self.api_key]
        return self.run(command)
#        return self._stdout_to_dict(result)


    def delete_all(self, ids: list) -> dict:
        command = ["vastai", "destroy", "instances", s, "--api-key", self.api_key]
        result = self.run(command)
        return self._stdout_to_dict(result)


    def get_offers(self, query: VastQuery) -> list[VastOffer]:
        try:
            command = ["vastai", "search", "offers", query.get_query(), "--type", "bid", "--raw"]
            response = self.run(command)
            response = json.loads(response)

            if not isinstance(response, list):
                print("Error: Unexpected response format. Check your command!")

            return list(map(lambda x: VastOffer(x), response))

        except Exception as e:
            print(f"Error: Exception!!! {e}")
            return []


    def get_billing(self) -> str:
        command = ["vastai", "show", "invoices", "--api-key", self.api_key]
        response = self.run(command)
        return response


    def run(self, command: list) -> str:
        f = Field(GRAY)
        print(f.format("INFO >>> "), f.format(str(command)))

        response = self.__execute_command(command) #, capture_output=True, text=True)

        if not response:
            print("Error >>> no response received")
        elif response.stderr:
            print("Error >>> ", response.stderr.strip())
        else:
            return response.stdout


    def run_old(self, command: list) -> dict:
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


    def __execute_command(self, cmd: list) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(cmd, capture_output=True, text=True, check=True)

        except subprocess.CalledProcessError as e:
            print(f">>>     Error running command: {e}")


    def _stdout_to_dict(self, txt: str) -> dict:

        result = txt.split("{")
        if len(result) < 2:
            return None

        result = result[1].split("}")
        items = result[0].split(",")
        d: dict = {}

        for item in items:
            s = item.replace("'", "")
            name_value_pair = s.split(":")

            d[name_value_pair[0].strip()] = name_value_pair[1].strip()

        return d


