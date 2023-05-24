from contextlib import suppress
from time import sleep
from urllib.parse import urljoin

import requests
from requests import HTTPError
from requests.adapters import HTTPAdapter, Retry

from migrator.config import ONCALL_API_TOKEN, ONCALL_API_URL


def api_call(method: str, path: str, **kwargs) -> requests.Response:
    url = urljoin(ONCALL_API_URL, path)

    # Retry on network errors
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1)
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    response = session.request(
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
            resp_json = None
            with suppress(requests.exceptions.JSONDecodeError):
                resp_json = response.json()

            # if no JSON payload is available, just raise the original exception
            if not resp_json:
                raise

            # this is mostly taken from requests.models.Response.raise_for_status, but with additional JSON payload
            http_error_msg = (
                "%s Client Error: %s for url: %s, response payload JSON: %s"
                % (response.status_code, e.response.reason, response.url, resp_json)
            )
            raise requests.exceptions.HTTPError(
                http_error_msg, response=e.response
            ) from e
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
    try:
        api_call("delete", path)
    except requests.exceptions.HTTPError as e:
        # ignore 404s on delete so deleting resources manually while running the script doesn't break it
        if e.response.status_code != 404:
            raise


def update(path: str, payload: dict) -> dict:
    response = api_call("put", path, json=payload)
    return response.json()
