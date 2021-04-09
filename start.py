import os
import sys
import argparse
from common import ColonyClient, LoggerService

def parse_user_input():
    parser = argparse.ArgumentParser(prog='Colony Sandbox Start')

    parser.add_argument("blueprint_name", type=str, help="The name of source blueprint")
    parser.add_argument("sandbox_name", type=str, help="The name of sandbox")
    parser.add_argument("duration", type=int, default=120, help="The name of source blueprint")
    parser.add_argument("branch", type=str, help="Run the Blueprint version from a remote Git branch")
    parser.add_argument("inputs", type=str, help="The inputs can be provided as a comma-separated list of key=value pairs")
    parser.add_argument("artifacts", type=str, help="A comma-separated list of artifacts per application")

    return parser.parse_args()

def parse_comma_separated_string(params_string: str = None) -> dict:
    res = {}

    if not params_string:
        return res

    key_values = params_string.split(",")

    for item in key_values:
        parts = item.split("=")
        if len(parts) != 2:
            raise ValueError("Line must be comma-separated list of key=values: key1=val1, key2=val2...")

        key = parts[0].strip()
        val = parts[1].strip()

        res[key] = val

    return res

def _compose_sb_url(account_name, sandbox_id, space):
    return f"https://{account}.cloudshellcolony.com/{space}/sandboxes/{sandbox_id}"


if __name__ == "__main__":
    args = parse_user_input()

    inputs_dict = parse_comma_separated_string(args.inputs)
    artifacts_dict = parse_comma_separated_string(args.artifacts)

    space = os.environ.get("COLONY_SPACE", "")
    token = os.environ.get("COLONY_TOKEN", "")
    account = os.environ.get("COLONY_ACCOUNT", "")

    client = ColonyClient(space, token)

    try: 
        sandbox_id = client.start_sandbox(
            args.blueprint_name,
            args.sandbox_name,
            args.duration,
            inputs_dict,
            artifacts_dict,
            args.branch
        )
    except Exception as e:
        LoggerService.error(f"Unable to start sandbox. Reason {e}")

    if account:
        url = _compose_sb_url(account, sandbox_id, space)
        LoggerService.message(f"Sandbox URL: {url}")

    LoggerService.set_output("sandbox_id", sandbox_id)
    LoggerService.success(f"Sandbox {sandbox_id} has started")
