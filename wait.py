import os
import sys
import argparse
import datetime
import time
from colony_client import ColonyClient

def parse_user_input():
    parser = argparse.ArgumentParser(prog='Colony Sandbox Start')
    parser.add_argument("sandbox_id", type=str, help="The name of sandbox")
    parser.add_argument("timeout", type=int, help="Set the timeout in minutes to wait for the sandbox to become active")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_user_input()

    client = ColonyClient(
        space=os.environ.get("COLONY_SPACE", ""),
        token=os.environ.get("COLONY_TOKEN", "")
    )
    sandbox_id = args.sandbox_id
    timeout = args.timeout

    start_time = datetime.datetime.now()
    sys.stdout.write(f"Waiting for the Sandbox {sandbox_id} to start...\n")

    while (datetime.datetime.now() - start_time).seconds < timeout * 60:
        sandbox = client.get_sandbox(sandbox_id)
        status = sandbox["sandbox_status"]

        if status == "Active":
            sys.stdout.write(f"Sandbox {sandbox_id} is active\n")
            sys.exit(0)

        elif status == "Launching":
            progress = sandbox["launching_progress"]
            for check_points, properties in progress.items():
                sys.stdout.write(f"{check_points}: {properties['status']}\n")
            time.sleep(30)

        else:
            sys.stderr.write("Launching failed. The state of Sandbox {sandbox_id} is: {status}\n")
            sys.exit(1)

    sys.stderr.write(f"Sandbox {sandbox_id} was not active after the provided timeout of {timeout} minutes\n")
    sys.exit(1)
