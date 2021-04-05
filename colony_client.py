import sys
import requests


class ColonySession(requests.Session):
    def __init__(self):
        super(ColonySession, self).__init__()
        self.headers.update({"Accept": "application/json", "Accept-Charset": "utf-8"})

    def colony_auth(self, token: str) -> None:
        self.headers.update({"Authorization": f"Bearer {token}"})


class ColonyClient:
    def __init__(self, space: str, token: str, session: ColonySession = ColonySession(), account: str = None):
        self.token = token
        self.space = space
        self.session = session
        session.colony_auth(self.token)
        self.base_api_url = f"https://cloudshellcolony.com/api/spaces/{self.space}"

    def _request(self, endpoint: str, method: str = 'GET', params: dict = None) -> requests.Response:
        method = method.upper()
        if method not in ("GET", "PUT", "POST", "DELETE"):
            raise ValueError("Method must be in [GET, POST, PUT, DELETE]")

        url = f"{self.base_api_url}/{endpoint}"
        
        request_args = {
            "method": method,
            "url": url,
        }
        if params is None:
            params = {}

        if method == "GET":
            request_args["params"] = params
        else:
            request_args["json"] = params

        response = self.session.request(**request_args)
        if response.status_code >= 400:
            message = ";".join([f"{err['name']}: {err['message']}" for err in response.json().get("errors", [])])
            raise Exception(message)

        return response

    def start_sandbox(
        self,
        blueprint_name: str,
        sandbox_name: str,
        duration: int = 120,
        inputs: dict = None,
        artifacts: dict = None,
        branch: str = None) -> str:

        path = "sandbox"
        iso_duration = f"PT{duration}M"
        params = {
            "sandbox_name": sandbox_name,
            "blueprint_name": blueprint_name,
            "duration": iso_duration,
            "inputs": inputs,
            "artifacts": artifacts,
        }

        if branch:
            params["source"] = {
                "branch": branch,
            }
  
        res = self._request(path, method="POST", params=params)
        sandbox_id = res.json()["id"]

        return sandbox_id

    def get_sandbox(self, sandbox_id: str) -> dict:
        """Returns Sandbox as a json"""
        path = f"sandbox/{sandbox_id}"

        res = self._request(path, method="GET")

        return res.json()


    def end_sandbox(self, sandbox_id: str) -> None:
        path = f"sandbox/{sandbox_id}"

        res = self._request(path, method="DELETE")
