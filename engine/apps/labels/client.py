from apps.grafana_plugin.helpers.client import APIClient


class LabelsAPIClient(APIClient):
    API_URL = "api/plugins/grafana-irm-labels-repo-app/resources/v1"  # todo

    def get_labels_keys(self):
        return self.api_get(f"{self.API_URL}/keys")
        # return [{"repr": "team", "id": "keyid123"}, {"repr": "severity", "id": "keyid456"}]

    def get_label_key_values(self, key_id):
        # {"keyid123": {"key": {"id": "keyid123", "repr": "team"}, "values": [{"id": "valueid123", "repr": "yolo"}]}}
        # return self.api_get(f"{self.API_URL}/labels/{key_id}")
        return self.api_get(f"{self.API_URL}/label/{key_id}")

    def get_label_key_by_name(self, key_repr):
        # {"keyid123": {"key": {"id": "keyid123", "repr": "team"}, "values": [{"id": "valueid123", "repr": "yolo"}]}}
        # return self.api_get(f"{self.API_URL}/labels/key/{key_repr}")
        return self.api_get(f"{self.API_URL}/label/key/{key_repr}")

    def create_label(self, label_data):
        return self.api_post(f"{self.API_URL}/labels", label_data)

    def add_value(self, key_id, label_data):
        # return self.api_post(f"{self.API_URL}/labels/{key_id}/value", label_data)
        return self.api_post(f"{self.API_URL}/label/{key_id}/value", label_data)

    def update_label_key(self, key_id, label_data):
        return self.api_post(f"{self.API_URL}/labels/{key_id}", label_data)

    def update_label_value(self, key_id, value_id, label_data):
        return self.api_post(f"{self.API_URL}/labels/{key_id}/{value_id}", label_data)
