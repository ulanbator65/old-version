
import subprocess
import json

from tostring import *
import config


@auto_str
class ShellCommand:
    def __init__(self):
        pass


    def run(self, command: list) -> any:
        print("INFO >>> ", command)

        result = self.__execute_command(command) #, capture_output=True, text=True)

        if result.stderr:
            print("Error >>> ", result.stderr.strip())

        if result.stdout:
            try:
                return result.stdout # json.loads(result.stdout)

            except json.JSONDecodeError:
                return {"success": False, "error": "Loading...", "stdout": result.stdout.strip()}


    def __execute_command(self, cmd: list):
        try:
            # return subprocess.run(cmd, capture_output=True, text=True)
#            ssh = subprocess.Popen(f"ssh {user}@{host} {cmd}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
#            ssh.call("")

            commands = ["echo 'hi'",  "echo 'another command'", "ls -al"]
            login = ["ssh", "-p", "19267", "root@210.239.9.203", "-L", "8080:localhost:8080", ";".join(commands)]

            p = subprocess.Popen(login, stdin=subprocess.PIPE)

#            p = subprocess.Popen([
#            "ssh",
#            "-o UserKnownHostsFile=/dev/null",
#            "-o StrictHostKeyChecking=no",
#            ";".join(commands)
#            ])

            for command in commands:
                p.stdin.write(command)
                p.stdin.write("\n")
                p.flush()

            p.communicate()

        except subprocess.CalledProcessError as e:
            print(f">>>     Error running command: {e}")


