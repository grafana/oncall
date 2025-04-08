from contextlib import suppress
from time import sleep
from urllib.parse import urljoin

import requests
from requests import HTTPError
from requests.adapters import HTTPAdapter, Retry


def api_call(method: str, base_url: str, path: str, **kwargs) -> requests.Response:
    url = urljoin(base_url, path)

    # Retry on network errors
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1)
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    response = session.request(method, url, **kwargs)

    try:
        response.raise_for_status()
    except HTTPError as e:
        if e.response.status_code == 429:
            cooldown_seconds = int(e.response.headers.get("Retry-After", 0.2))
            sleep(cooldown_seconds)
            return api_call(method, base_url, path, **kwargs)
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
