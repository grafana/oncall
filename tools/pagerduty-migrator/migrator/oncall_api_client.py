from time import sleep
from urllib.parse import urljoin

import requests
from requests import HTTPError

from migrator.config import ONCALL_API_TOKEN, ONCALL_API_URL
TAB = " " * 4

def api_call(method: str, path: str, **kwargs) -> requests.Response:
    url = urljoin(ONCALL_API_URL, path)

    response = requests.request(
        method, url, headers={"Authorization": ONCALL_API_TOKEN}, **kwargs
    )

    try:
        response.raise_for_status()
    except HTTPError as e:
        if e.response.status_code == 429:
            cooldown_seconds = int(e.response.headers["Retry-After"])
            sleep(cooldown_seconds)
            return api_call(method, path, **kwargs)
        elif e.response.status_code == 400:
            json_res = response.json()
            print(TAB + ">>> " + json_res["detail"])
        elif e.response.status_code == 500:
            json_res = response.json()
            print(TAB + ">>> " + json_res["detail"])
        else:
            raise

    return response


def list_all(path: str) -> list[dict]:
    response = api_call("get", path)

    data = response.json()
    results = data["results"]

    while data["next"]:
        response = api_call("get", data["next"])

        data = response.json()
        results += data["results"]

    return results


def create(path: str, payload: dict) -> dict:
    response = api_call("post", path, json=payload)
    return response.json()


def delete(path: str) -> None:
    api_call("delete", path)


def update(path: str, payload: dict) -> dict:
    response = api_call("put", path, json=payload)
    return response.json()
