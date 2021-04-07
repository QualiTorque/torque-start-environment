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

def build_shortcuts_json(sandbox_spec):
    res = {}
    applications = sandbox_spec.get('applications', [])
    for app in applications:
        res[app["name"]] = list(app['shortcuts']).copy()
    
    return res

def _simplify_state(sandbox_progress):
    return {step: description["status"] for step, description in sandbox_progress.items()}

def _compose_sb_url(account_name, sandbox_id, space):
    return f"https://{account}.cloudshellcolony.com/{space}/sandboxes/{sandbox_id}"



if __name__ == "__main__":
    args = parse_user_input()

    space = os.environ.get("COLONY_SPACE", "")
    token = os.environ.get("COLONY_TOKEN", "")
    account = os.environ.get("COLONY_ACCOUNT", "")

    client = ColonyClient(space, token)
    sandbox_id = args.sandbox_id
    timeout = args.timeout

    if not sandbox_id:
        print("::error::Sandbox Id cannot be empty")
        sys.exit(1)

    if timeout < 0:
        print("::error::Timeout must be positive")
        sys.exit(1)

    start_time = datetime.datetime.now()
    print(f"Waiting for the Sandbox {sandbox_id} to start...")

    sandbox_state = {}

    while (datetime.datetime.now() - start_time).seconds < timeout * 60:
        try:
            sandbox = client.get_sandbox(sandbox_id)
        except Exception as e:
            print(f"::error::Unable to get sandbox with ID {sandbox_id}; reason: {e}")
            sys.exit(1)

        status = sandbox["sandbox_status"]

        if status == "Active":
            print(f"Sandbox {sandbox_id} is active")
            print(f"::set-output name=sandbox_details::{str(sandbox)}")
            print(f"::set-output name=sandbox_shortcuts::{str(build_shortcuts_json(sandbox))}")
            if account:
                url = _compose_sb_url(account, sandbox_id, space)
                print(f"Sandbox URL: {url}")

            sys.exit(0)

        elif status == "Launching":
            progress = sandbox["launching_progress"]
            simple_state = _simplify_state(progress)
            if simple_state != sandbox_state:
                sandbox_state.update(simple_state)
                print(f"Current state: {str(sandbox_state)}")
            time.sleep(10)

        else:
            print(f"::error::Launching failed. The state of Sandbox {sandbox_id} is: {status}")
            sys.exit(1)

    print(f"::error::Sandbox {sandbox_id} was not active after the provided timeout of {timeout} minutes")
    sys.exit(1)
