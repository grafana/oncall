from apps.grafana_plugin.helpers.client import APIClient


class LabelsAPIClient(APIClient):
    API_URL = "api/plugins/grafana-irm-labels-repo-app/resources/v1/labels"

    def __init__(self, organization):
        self.organization = organization
        # todo: auth

    def get_labels_keys(self):
        return self.api_get(self.API_URL)
        # return [{"repr": "team", "id": "keyid123"}, {"repr": "severity", "id": "keyid456"}]

    def get_label_key_values(self, key_id):
        # {"keyid123": {"key": {"id": "keyid123", "repr": "team"}, "values": [{"id": "valueid123", "repr": "yolo"}]}}
        return self.api_get(f"{self.API_URL}/{key_id}/value")

    def create_label(self, label_data):
        return self.api_post(self.API_URL, label_data)

    def add_value(self, key_id, label_data):
        return self.api_post(f"{self.API_URL}/{key_id}/value", label_data)

    def update_label_key(self, key_id, label_data):
        return self.api_post(f"{self.API_URL}/{key_id}", label_data)

    def update_label_value(self, key_id, value_id, label_data):
        return self.api_post(f"{self.API_URL}/{key_id}/{value_id}", label_data)
