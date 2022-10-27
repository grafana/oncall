import requests
from django.utils import timezone

from apps.migration_tool.constants import REQUEST_URL


class APIResponseException(Exception):
    pass


def get_data_with_respect_to_pagination(api_token, endpoint):
    def fetch(url):
        response = requests.get(url, headers={"AUTHORIZATION": api_token})
        if response.status_code != 200:
            raise APIResponseException(f"Status code: {response.status_code}, Data: {response.content}")
        return response.json()

    data = fetch(f"{REQUEST_URL}/{endpoint}")
    results = data["results"]

    while data["next"]:
        data = fetch(data["next"])

        new_results = data["results"]
        results.extend(new_results)

    return results


def convert_string_to_datetime(dt_str):
    try:
        dt = timezone.datetime.strptime(dt_str, "%Y-%m-%dT%X.%f%z")
    except ValueError:
        dt = timezone.datetime.strptime(dt_str, "%Y-%m-%dT%XZ")
    return dt
