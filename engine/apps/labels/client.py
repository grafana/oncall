from urllib.parse import urljoin

from apps.grafana_plugin.helpers.client import APIClient


class LabelsAPIClient(APIClient):
    LABELS_API_URL = "/api/plugins/grafana-irm-labels-repo-app/resources/v1"  # todo

    def __init__(self, api_url: str, api_token: str) -> None:
        super().__init__(api_url, api_token)
        self.api_url = urljoin(api_url, self.LABELS_API_URL)

    def get_keys(self):
        return self.api_get("/keys")
        # return [{"repr": "team", "id": "keyid123"}, {"repr": "severity", "id": "keyid456"}]

    def get_values(self, key_id):
        # {"keyid123": {"key": {"id": "keyid123", "repr": "team"}, "values": [{"id": "valueid123", "repr": "yolo"}]}}
        # return self.api_get("/labels/{key_id}")
        return self.api_get(f"/label/{key_id}")

    def get_key_by_name(self, key_repr):
        # {"keyid123": {"key": {"id": "keyid123", "repr": "team"}, "values": [{"id": "valueid123", "repr": "yolo"}]}}
        # return self.api_get(f"{self.API_URL}/labels/key/{key_repr}")
        return self.api_get(f"/label/key/{key_repr}")

    def create_label(self, label_data):
        return self.api_post("/labels", label_data)

    def add_value(self, key_id, label_data):
        # return self.api_post(f"{self.API_URL}/labels/{key_id}/value", label_data)
        return self.api_post(f"/label/{key_id}/value", label_data)

    def update_key(self, key_id, label_data):
        return self.api_post(f"/labels/{key_id}", label_data)

    def update_value(self, key_id, value_id, label_data):
        return self.api_post(f"/labels/{key_id}/{value_id}", label_data)
