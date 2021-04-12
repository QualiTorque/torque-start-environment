import os
import sys
import argparse
import datetime
import time
from common import ColonyClient, LoggerService

def parse_user_input():
    parser = argparse.ArgumentParser(prog='Colony Sandbox Start')
    parser.add_argument("sandbox_id", type=str, help="The name of sandbox")
    parser.add_argument("timeout", type=int, help="Set the timeout in minutes to wait for the sandbox to become active")

    return parser.parse_args()

def build_shortcuts_json(sandbox_spec):
    res = {}
    applications = sandbox_spec.get('applications', [])
    for app in applications:
        res[app["name"]] = list(app['shortcuts']).copy()
    
    return res

def _simplify_state(sandbox_progress):
    return {step: description["status"] for step, description in sandbox_progress.items()}


if __name__ == "__main__":
    args = parse_user_input()

    space = os.environ.get("COLONY_SPACE", "")
    token = os.environ.get("COLONY_TOKEN", "")

    client = ColonyClient(space, token)
    sandbox_id = args.sandbox_id
    timeout = args.timeout

    if not sandbox_id:
        LoggerService.error("Sandbox Id cannot be empty")

    if timeout < 0:
        LoggerService.error("Timeout must be positive")

    start_time = datetime.datetime.now()
    LoggerService.message(f"Waiting for the Sandbox {sandbox_id} to start...")

    sandbox_state = {}

    while (datetime.datetime.now() - start_time).seconds < timeout * 60:
        try:
            sandbox = client.get_sandbox(sandbox_id)
        except Exception as e:
            LoggerService.error(f"Unable to get sandbox with ID {sandbox_id}; reason: {e}")

        status = sandbox["sandbox_status"]
        progress = sandbox["launching_progress"]

        simple_state = _simplify_state(progress)
        if simple_state != sandbox_state:
            sandbox_state.update(simple_state)
            LoggerService.message(f"Current state: {str(sandbox_state)}")

        if status == "Active":
            LoggerService.set_output("sandbox_details", str(sandbox))
            LoggerService.set_output("sandbox_shortcuts", str(build_shortcuts_json(sandbox)))
            LoggerService.success(f"Sandbox {sandbox_id} is active!")

        elif status == "Launching":
            time.sleep(10)

        else:
            LoggerService.error(f"Launching failed. The state of Sandbox {sandbox_id} is: {status}")

    LoggerService.error(f"Sandbox {sandbox_id} was not active after the provided timeout of {timeout} minutes")
