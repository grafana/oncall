class LabelsAPIClient:
    # todo: auth

    def get_labels_keys(self):
        return [
            {
                "repr": "team",
                "id": "keyid123",
            },
            {
                "repr": "severity",
                "id": "keyid456",
            },
        ]

    def get_label_key_values(self, key_id):
        mocked_response = {
            "keyid123": {"key": {"id": "keyid123", "repr": "team"}, "values": [{"id": "valueid123", "repr": "yolo"}]},
            "keyid456": {
                "key": {"id": "keyuid456", "repr": "severity"},
                "values": [{"id": "valueid456", "repr": "low"}, {"id": "valueid789", "repr": "high"}],
            },
        }
        return mocked_response.get(key_id)

    def create_label(self, label_data):
        return

    def add_value(self, key_id, value):
        return

    def update_label_key(self, key_id, data):
        return

    def update_label_value(self, key_id, value_id, data):
        return
