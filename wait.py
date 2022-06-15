import os
import argparse
import datetime
import time
import json
from common import TorqueClient, LoggerService

def parse_user_input():
    parser = argparse.ArgumentParser(prog='Torque Sandbox Start')
    parser.add_argument("sandbox_id", type=str, help="The name of sandbox")
    parser.add_argument("timeout", type=int, help="Set the timeout in minutes to wait for the sandbox to become active")

    return parser.parse_args()


def _simplify_state(sandbox_progress):
    return {step: description["status"] for step, description in sandbox_progress.items()}


if __name__ == "__main__":
    args = parse_user_input()

    space = os.environ.get("TORQUE_SPACE", "")
    token = os.environ.get("TORQUE_TOKEN", "")

    client = TorqueClient(space, token)
    sandbox_id = args.sandbox_id
    timeout = args.timeout

    if not sandbox_id:
        LoggerService.error("Sandbox Id cannot be empty")

    if timeout < 0:
        LoggerService.error("Timeout must be positive")

    start_time = datetime.datetime.now()
    LoggerService.message(f"Waiting for the Sandbox {sandbox_id} to start...")

    sandbox_state = ''

    while (datetime.datetime.now() - start_time).seconds < timeout * 60:
        try:
            sandbox = client.get_sandbox(sandbox_id)
        except Exception as e:
            LoggerService.error(f"Unable to get sandbox with ID {sandbox_id}; reason: {e}")

        sb_details = sandbox.get("details", None)

        if not sb_details:
            LoggerService.error(f"Torque API returned unknown format of response: {json.dumps(sandbox)}")
            break

        status = sb_details["computed_status"]
        progress = sb_details["state"]["current_state"]

        if progress != sandbox_state:
            sandbox_state = progress
            LoggerService.message(f"Current state: {str(sandbox_state)}")

        if status == "Active":
            LoggerService.set_output("sandbox_details", json.dumps(sb_details))
            LoggerService.success(f"Sandbox {sandbox_id} is active!")

        elif status == "Launching":
            time.sleep(10)

        else:
            LoggerService.error(f"Launching failed. The state of Sandbox {sandbox_id} is: {status}")

    LoggerService.error(f"Sandbox {sandbox_id} was not active after the provided timeout of {timeout} minutes")
