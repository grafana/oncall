from urllib.parse import urljoin

from apps.grafana_plugin.helpers.client import APIClient


class LabelsAPIClient(APIClient):
    LABELS_API_URL = "/api/plugins/grafana-labels/resources/v1/labels/"

    def __init__(self, api_url: str, api_token: str) -> None:
        super().__init__(api_url, api_token)
        self.api_url = urljoin(api_url, self.LABELS_API_URL)

    def create_label(self, label_data):
        return self.api_post("", label_data)

    def get_keys(self):
        return self.api_get("keys")
        # return [{"repr": "team", "id": "keyid123"}, {"repr": "severity", "id": "keyid456"}]

    def get_values(self, key_id):
        # {"keyid123": {"key": {"id": "keyid123", "repr": "team"}, "values": [{"id": "valueid123", "repr": "yolo"}]}}
        return self.api_get(f"id/{key_id}")

    def add_value(self, key_id, label_data):
        return self.api_post(f"id/{key_id}/values", label_data)

    def rename_key(self, key_id, label_data):
        return self.api_put(f"id/{key_id}", label_data)

    def rename_value(self, key_id, value_id, label_data):
        return self.api_put(f"id/{key_id}/values/{value_id}", label_data)
